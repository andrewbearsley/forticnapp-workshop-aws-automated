#!/bin/bash
# CloudShell Cleanup Script
#
# Removes everything the workshop created, on both sides:
#   - FortiCNAPP cloud integrations (Labs 2, 3 via CloudFormation and Lab 9 via Terraform)
#   - AWS resources (Labs 2, 3, 5, 6, 8, 9, 10, 11)
#   - CloudShell artifacts (binaries, repos, config)
#
# To use: Copy and paste this entire script into AWS CloudShell, or save as a file and run:
#   bash cloudshell_cleanup.sh
#
# WARNING: this assumes a disposable workshop AWS account. It sweeps EVERY
# enabled region and removes ALL EC2 instances, key pairs and non-default
# security groups in the account, not just the ones the workshop created, plus
# every FortiCNAPP integration pointing at this AWS account. Do not run it in an
# account that hosts anything you want to keep.

# Best-effort sweep: continue past individual failures rather than aborting.
# Do not use `set -e` here, one failed delete should not strand the rest.
set +e

# Disable AWS CLI pager to prevent interactive prompts
export AWS_PAGER=""

echo "=== FortiCNAPP Workshop Cleanup ==="
echo ""

# ===========================================================================
# Step 1: Destroy Terraform resources (Lab 9)
#
# Terraform owns its FortiCNAPP integrations in state, so `destroy` removes
# both the AWS resources and the integration records. Run this before Step 2
# so Step 2 only has to mop up what Terraform never owned.
# ===========================================================================
echo "Checking for Terraform deployments..."
if [ -d "$HOME/lacework/aws" ]; then
    echo "  Found Terraform working directory: ~/lacework/aws"

    cd "$HOME/lacework/aws" || {
        echo "  Warning: Failed to navigate to ~/lacework/aws directory"
        cd "$HOME"
    }

    if command -v terraform &>/dev/null || [ -f "$HOME/bin/terraform" ]; then
        TERRAFORM_CMD="terraform"
        if [ -f "$HOME/bin/terraform" ]; then
            TERRAFORM_CMD="$HOME/bin/terraform"
        fi

        if [ ! -d ".terraform" ] && [ ! -f "terraform.tfstate" ] && [ ! -f ".terraform/terraform.tfstate" ]; then
            echo "  Terraform not initialized - initializing first..."
            if $TERRAFORM_CMD init -upgrade 2>/dev/null; then
                echo "  Done: Terraform initialized"
            else
                echo "  Warning: Terraform init failed - may not have resources to destroy"
            fi
        fi

        echo "  Running terraform destroy..."
        if $TERRAFORM_CMD destroy -auto-approve 2>/dev/null; then
            echo "  Done: Terraform resources destroyed successfully"
        else
            echo "  Warning: Terraform destroy encountered errors (check output above)"
            echo "  This may be normal if no resources exist or were already destroyed"
        fi
    else
        echo "  Warning: Terraform command not found - skipping destroy"
        echo "  You may need to manually destroy Terraform resources"
    fi

    cd "$HOME"
else
    echo "  - No Terraform working directory found (~/lacework/aws does not exist)"
    echo "  Skipping Terraform init and destroy"
fi
echo ""

# ===========================================================================
# Step 2: Deregister FortiCNAPP cloud integrations for this AWS account
#
# THIS IS THE STEP THAT IS EASY TO MISS.
#
# Labs 2 and 3 create the integration record in the FortiCNAPP console FIRST,
# then launch CloudFormation to build the AWS side. CloudFormation never owns
# that record. Deleting the stack removes the S3 bucket, the cross-account role
# and the ECS scanner, but the FortiCNAPP integration survives and keeps polling
# a bucket that no longer exists, reporting:
#
#   "Data loading error: Unable to access scan results within storage bucket"
#
# The record can only be removed through FortiCNAPP, which is what this does.
# It runs before Step 5 removes the Lacework CLI and its credentials.
# ===========================================================================
echo "Removing FortiCNAPP cloud integrations for this AWS account..."

LW_CLI=""
if command -v lacework &>/dev/null; then
    LW_CLI="lacework"
elif [ -x "$HOME/bin/lacework" ]; then
    LW_CLI="$HOME/bin/lacework"
fi

if [ -z "$LW_CLI" ]; then
    echo "  Warning: Lacework CLI not found (Labs 4 and 8 install it)"
    echo "  Remove the integrations manually in the FortiCNAPP console:"
    echo "    Settings > Integrations > Cloud accounts > select your integration > Delete"
elif ! command -v jq &>/dev/null; then
    echo "  Warning: jq not found - cannot filter integrations by account"
    echo "  Remove the integrations manually in the FortiCNAPP console:"
    echo "    Settings > Integrations > Cloud accounts > select your integration > Delete"
else
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo "  Warning: Could not determine AWS account ID - skipping"
    else
        echo "  AWS account: $AWS_ACCOUNT_ID"

        # Match on every field that can carry the account ID, so Configuration,
        # CloudTrail and Agentless integrations are all caught.
        INTG_GUIDS=$("$LW_CLI" cloud-account list --json --noninteractive 2>/dev/null \
            | jq -r --arg a "$AWS_ACCOUNT_ID" '
                .[]? | select(
                    (.data.awsAccountId // "") == $a
                    or ((.data.crossAccountCredentials.roleArn // "") | contains($a))
                    or ((.data.bucketArn // "") | contains($a))
                    or ((.data.queueUrl // "") | contains($a))
                ) | "\(.intgGuid)|\(.type)|\(.name)"' 2>/dev/null)

        if [ -z "$INTG_GUIDS" ]; then
            echo "  - No FortiCNAPP integrations found for account $AWS_ACCOUNT_ID"
            echo "    (if you expected some, check you are on the right tenant)"
        else
            echo "$INTG_GUIDS" | while IFS='|' read -r guid itype iname; do
                [ -z "$guid" ] && continue
                echo "  Deleting $itype integration: $iname"
                if "$LW_CLI" cloud-account delete "$guid" --noninteractive 2>/dev/null; then
                    echo "    Done: $guid"
                else
                    echo "    Warning: Failed to delete $guid - remove it in the console"
                fi
            done
        fi
    fi
fi
echo ""

# ===========================================================================
# Step 3: AWS regional sweep
#
# The workshop is run across APAC and students pick their own local region.
# CloudShell only ever operates in the region it opened in, so sweep every
# region the account has enabled rather than assuming one.
# ===========================================================================
if ! command -v aws &>/dev/null; then
    echo "AWS CLI not found - skipping all AWS resource cleanup"
    REGIONS=""
else
    REGIONS=$(aws ec2 describe-regions --all-regions \
        --query 'Regions[?OptInStatus!=`not-opted-in`].RegionName' \
        --output text 2>/dev/null)

    if [ -z "$REGIONS" ]; then
        REGIONS="${AWS_REGION:-$(aws configure get region 2>/dev/null)}"
        echo "Warning: Could not list regions, falling back to: ${REGIONS:-none}"
    fi
fi

# Return every ROOT CloudFormation stack whose name matches the pattern,
# case-insensitively. Nested stacks carry a RootId and are excluded, since
# deleting the root removes them. Returns all matches, not just one: students
# who redeploy after a failure end up with AWS-AgentlessScanning AND
# AWS-AgentlessScanning-2, and both need to go.
# Field separator is a tab, not whitespace: Lab 3 lets students name the stack
# freely and they use spaces ("Agentless Workload Scanning JT"). Splitting on
# whitespace silently drops every such stack.
find_workshop_stacks() {
    local region=$1
    local pattern=$2
    aws cloudformation describe-stacks --region "$region" \
        --query 'Stacks[].[StackName,RootId]' --output text 2>/dev/null \
      | awk -F'\t' '$2=="None" {print $1}' \
      | grep -iE "$pattern" 2>/dev/null
}

delete_cfn_stack() {
    local region=$1
    local stack_name=$2
    echo "    Deleting stack $stack_name (this may take a few minutes)..."
    aws cloudformation delete-stack --region "$region" --stack-name "$stack_name" 2>/dev/null
    if aws cloudformation wait stack-delete-complete --region "$region" --stack-name "$stack_name" 2>/dev/null; then
        echo "      Done: $stack_name deleted"
        return 0
    fi
    # Deletion failed. Retry retaining whatever blocked it (usually a non-empty
    # S3 bucket). Step 4 sweeps those buckets afterwards.
    echo "      Retrying with retained resources..."
    local failed_resources
    failed_resources=$(aws cloudformation describe-stack-resources --region "$region" --stack-name "$stack_name" \
        --query 'StackResources[?ResourceStatus==`DELETE_FAILED`].LogicalResourceId' --output text 2>/dev/null)
    if [ -n "$failed_resources" ]; then
        aws cloudformation delete-stack --region "$region" --stack-name "$stack_name" \
            --retain-resources $failed_resources 2>/dev/null
        aws cloudformation wait stack-delete-complete --region "$region" --stack-name "$stack_name" 2>/dev/null
        echo "      Done: $stack_name deleted (some resources retained, Step 4 will sweep them)"
    else
        echo "      Warning: Could not determine what blocked deletion of $stack_name"
    fi
}

for REGION in $REGIONS; do
    # Cheap probe first so quiet regions do not each cost five API calls.
    STACKS=$(find_workshop_stacks "$REGION" "agentless|cloudtrail|lacework|forticnapp")
    INSTANCES=$(aws ec2 describe-instances --region "$REGION" \
        --query 'Reservations[].Instances[].InstanceId' --output text \
        --filters "Name=instance-state-name,Values=running,stopped" 2>/dev/null)
    TRAILS=$(aws cloudtrail list-trails --region "$REGION" \
        --query 'Trails[].Name' --output text 2>/dev/null | tr '\t' '\n' | grep -i "lacework" 2>/dev/null)
    KEY_PAIRS=$(aws ec2 describe-key-pairs --region "$REGION" \
        --query 'KeyPairs[].KeyName' --output text 2>/dev/null | tr '\t' '\n')
    SEC_GROUPS=$(aws ec2 describe-security-groups --region "$REGION" \
        --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text 2>/dev/null)

    if [ -z "$STACKS" ] && [ -z "$INSTANCES" ] && [ -z "$TRAILS" ] \
       && [ -z "$KEY_PAIRS" ] && [ -z "$SEC_GROUPS" ]; then
        continue
    fi

    echo "--- Region: $REGION ---"

    # Terminate EC2 instances first, so nothing is writing scan data and the
    # security groups become deletable. Deliberately not waiting here, the
    # stack deletions below take long enough for termination to finish.
    if [ -n "$INSTANCES" ]; then
        echo "  Terminating EC2 instances:"
        for instance in $INSTANCES; do
            echo "    - $instance"
        done
        if aws ec2 terminate-instances --region "$REGION" --instance-ids $INSTANCES >/dev/null 2>&1; then
            echo "    Done: Termination requested"
        else
            echo "    Warning: Failed to terminate some instances"
        fi
    fi

    # Delete CloudFormation stacks. Matches on a broad pattern because Lab 3
    # lets students name the stack whatever they like, and they do.
    if [ -n "$STACKS" ]; then
        echo "  CloudFormation stacks:"
        # Read line by line, stack names can contain spaces
        printf '%s\n' "$STACKS" | while IFS= read -r stack; do
            [ -z "$stack" ] && continue
            delete_cfn_stack "$REGION" "$stack"
        done
    fi

    # Delete CloudTrail trails created by the workshop
    if [ -n "$TRAILS" ]; then
        echo "  CloudTrail trails:"
        for trail in $TRAILS; do
            echo "    Deleting trail: $trail"
            aws cloudtrail stop-logging --region "$REGION" --name "$trail" 2>/dev/null
            sleep 2
            if aws cloudtrail delete-trail --region "$REGION" --name "$trail" 2>/dev/null; then
                echo "      Done: $trail"
            else
                echo "      Warning: Failed to delete trail $trail"
            fi
        done
    fi

    # Delete EC2 key pairs
    if [ -n "$KEY_PAIRS" ]; then
        echo "  EC2 key pairs:"
        printf '%s\n' "$KEY_PAIRS" | while IFS= read -r key_pair; do
            [ -z "$key_pair" ] && continue
            if aws ec2 delete-key-pair --region "$REGION" --key-name "$key_pair" 2>/dev/null; then
                echo "    Done: $key_pair"
            else
                echo "    Warning: Failed to delete key pair $key_pair"
            fi
        done
    fi

    # Delete security groups (except 'default'). Re-read the list, the stack
    # deletions above may already have removed some.
    SEC_GROUPS=$(aws ec2 describe-security-groups --region "$REGION" \
        --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text 2>/dev/null)
    if [ -n "$SEC_GROUPS" ]; then
        echo "  Security groups:"
        for sg_id in $SEC_GROUPS; do
            if aws ec2 delete-security-group --region "$REGION" --group-id "$sg_id" 2>/dev/null; then
                echo "    Done: $sg_id"
            else
                echo "    Warning: Failed to delete $sg_id (may still be in use)"
            fi
        done
    fi
done
echo ""

# ===========================================================================
# Step 4: Empty and delete Lacework-related S3 buckets
#
# Bucket names are global, so no region loop is needed to find them. Each
# bucket's own region is resolved before operating on it, which catches
# buckets left in regions the student used but CloudShell never opened in.
# ===========================================================================
echo "Emptying and deleting Lacework-related S3 buckets..."
if command -v aws &>/dev/null; then
    ALL_BUCKETS=$(aws s3api list-buckets --query 'Buckets[].Name' --output text 2>/dev/null)

    LACEWORK_BUCKETS=""
    if [ -n "$ALL_BUCKETS" ]; then
        for bucket in $ALL_BUCKETS; do
            if echo "$bucket" | grep -qiE "(lacework|lw-|forticnapp)" 2>/dev/null; then
                LACEWORK_BUCKETS="$LACEWORK_BUCKETS $bucket"
            fi
        done
    fi

    if [ -n "$LACEWORK_BUCKETS" ]; then
        TMPFILE=$(mktemp)
        for bucket in $LACEWORK_BUCKETS; do
            echo "  Processing bucket: $bucket"

            if ! aws s3api head-bucket --bucket "$bucket" 2>/dev/null; then
                echo "    - Bucket does not exist or is already deleted"
                continue
            fi

            # Resolve the bucket's own region. us-east-1 reports as None.
            B_REGION=$(aws s3api get-bucket-location --bucket "$bucket" \
                --query 'LocationConstraint' --output text 2>/dev/null)
            if [ "$B_REGION" = "None" ] || [ -z "$B_REGION" ]; then
                B_REGION="us-east-1"
            fi
            echo "    Region: $B_REGION"

            echo "    Removing objects..."
            aws s3 rm "s3://$bucket" --recursive --region "$B_REGION" 2>/dev/null

            echo "    Removing versions and delete markers..."
            BATCH_COUNT=0
            while true; do
                aws s3api list-object-versions --bucket "$bucket" --region "$B_REGION" \
                    --no-paginate --output json 2>/dev/null > "$TMPFILE" || break

                DELETE_JSON=$(python3 -c "
import json, sys
with open('$TMPFILE') as f:
    data = json.load(f)
items = []
for v in data.get('Versions', []) or []:
    items.append({'Key': v['Key'], 'VersionId': v['VersionId']})
for m in data.get('DeleteMarkers', []) or []:
    items.append({'Key': m['Key'], 'VersionId': m['VersionId']})
if items:
    print(json.dumps({'Objects': items, 'Quiet': True}))
" 2>/dev/null)

                if [ -z "$DELETE_JSON" ]; then
                    break
                fi

                echo "$DELETE_JSON" > "$TMPFILE.del"
                aws s3api delete-objects --bucket "$bucket" --region "$B_REGION" \
                    --delete "file://$TMPFILE.del" 2>/dev/null || break
                BATCH_COUNT=$((BATCH_COUNT + 1))
                echo "      Deleted batch $BATCH_COUNT..."
            done

            if [ "$BATCH_COUNT" -gt 0 ]; then
                echo "    Emptied bucket ($BATCH_COUNT batches)"
            fi

            echo "    Deleting bucket..."
            if aws s3api delete-bucket --bucket "$bucket" --region "$B_REGION" 2>/dev/null; then
                echo "    Done: Deleted bucket: $bucket"
            else
                echo "    Warning: Failed to delete bucket: $bucket"
                echo "    Try manually: aws s3 rb s3://$bucket --force --region $B_REGION"
            fi
        done
        rm -f "$TMPFILE" "$TMPFILE.del"
    else
        echo "  - No Lacework-related buckets found"
    fi
else
    echo "  - AWS CLI not found (skipping S3 bucket cleanup)"
fi
echo ""

# ===========================================================================
# Step 5: Remove CloudShell artifacts
#
# Runs last, because Step 2 needs the Lacework CLI and ~/.lacework.toml to
# still exist in order to deregister the integrations.
# ===========================================================================
echo "Removing Terraform..."
if [ -f "$HOME/bin/terraform" ]; then
    rm -f "$HOME/bin/terraform"
    echo "  Terraform removed from bin/"
fi
if [ -f "$HOME/terraform" ]; then
    rm -f "$HOME/terraform"
    echo "  Terraform removed from home directory"
fi

echo "Removing Lacework CLI..."
if [ -f "$HOME/bin/lacework" ]; then
    rm -f "$HOME/bin/lacework"
    echo "  Lacework CLI removed"
else
    echo "  Lacework CLI not found"
fi

echo "Removing cloned repositories..."
if [ -d "$HOME/lacework-iac-scan-example" ]; then
    rm -rf "$HOME/lacework-iac-scan-example"
    echo "  Removed lacework-iac-scan-example repository"
fi

if [ -d "$HOME/lacework-sca-scan-example" ]; then
    rm -rf "$HOME/lacework-sca-scan-example"
    echo "  Removed lacework-sca-scan-example repository"
fi

echo "Removing LICENSE files and workshop artifacts..."
for f in LICENSE.txt LICENSES.txt sbom.json terraform.zip; do
    if [ -f "$HOME/$f" ]; then
        rm -f "$HOME/$f"
        echo "  Removed $f"
    fi
done

# Remove any malformed export/command files or directories (often created by copy-paste errors)
find "$HOME" -maxdepth 1 \( -type f -o -type d \) \( -name "*export*" -o -name "*TF_PLUGIN*" -o -name "*Configure*" -o -name "*Terraform*" \) 2>/dev/null | while read -r item; do
    if [ -e "$item" ]; then
        if [ -f "$item" ]; then
            if head -1 "$item" 2>/dev/null | grep -qE "(export|TF_PLUGIN|Configure)" 2>/dev/null; then
                rm -f "$item"
                echo "  Removed malformed file: $(basename "$item")"
            fi
        elif [ -d "$item" ]; then
            dirname=$(basename "$item")
            if echo "$dirname" | grep -qiE "(export|TF_PLUGIN|Configure|Terraform)" 2>/dev/null; then
                rm -rf "$item"
                echo "  Removed malformed directory: $dirname"
            fi
        fi
    fi
done

echo "Removing Terraform working directory..."
if [ -d "$HOME/lacework" ]; then
    rm -rf "$HOME/lacework"
    echo "  Removed ~/lacework directory"
fi

echo "Removing Terraform plugin cache..."
if [ -d "$HOME/.terraform.d" ]; then
    rm -rf "$HOME/.terraform.d"
    echo "  Removed ~/.terraform.d directory"
else
    echo "  ~/.terraform.d directory not found"
fi

echo "Removing Lacework CLI configuration..."
if [ -d "$HOME/.lacework" ]; then
    rm -rf "$HOME/.lacework"
    echo "  Removed Lacework CLI configuration directory"
else
    echo "  Lacework CLI configuration directory not found"
fi

if [ -f "$HOME/.lacework.toml" ]; then
    rm -f "$HOME/.lacework.toml"
    echo "  Removed Lacework CLI config file (.lacework.toml)"
else
    echo "  Lacework CLI config file not found"
fi

if [ -d "$HOME/bin" ] && [ -z "$(ls -A $HOME/bin)" ]; then
    rmdir "$HOME/bin"
    echo "  Removed empty bin directory"
fi

echo "Cleaning up .bashrc..."
if [ -f "$HOME/.bashrc" ]; then
    cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  Created backup of .bashrc"

    sed -i '/^export PATH=\$HOME\/bin:\$PATH$/d' "$HOME/.bashrc" 2>/dev/null || \
    sed -i '' '/^export PATH=\$HOME\/bin:\$PATH$/d' "$HOME/.bashrc" 2>/dev/null

    sed -i '/^export PATH=HOME\/bin:/d' "$HOME/.bashrc" 2>/dev/null || \
    sed -i '' '/^export PATH=HOME\/bin:/d' "$HOME/.bashrc" 2>/dev/null

    sed -i '/^export TF_PLUGIN_CACHE_DIR=/d' "$HOME/.bashrc" 2>/dev/null || \
    sed -i '' '/^export TF_PLUGIN_CACHE_DIR=/d' "$HOME/.bashrc" 2>/dev/null

    if bash -n "$HOME/.bashrc" 2>/dev/null; then
        echo "  Cleaned up .bashrc (syntax verified)"
    else
        echo "  Warning: Syntax error detected after cleanup - restoring backup"
        cp "$HOME/.bashrc.backup."* "$HOME/.bashrc" 2>/dev/null
        echo "  Restored .bashrc from backup"
    fi
else
    echo "  .bashrc not found"
fi

echo ""
echo "=== Cleanup complete ==="
echo ""
echo "Verify in the FortiCNAPP console: Settings > Integrations > Cloud accounts"
echo "should no longer list your AWS account. If it does, delete it there."
