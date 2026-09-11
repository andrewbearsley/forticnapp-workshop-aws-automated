# Lab 11: Install Integrations via Terraform

## Objectives

In Lab 3, FortiCNAPP deployed the integrations for you from the console wizard. That is the fastest path, and it is what most partners should use. But some customers want the Terraform in their own repository, reviewed in a pull request and applied by a pipeline. In this lab, we'll use the Lacework CLI to generate Terraform code, then deploy the same CloudTrail and Configuration integrations as code. This is the production-ready approach: repeatable, version-controlled, and pipeline-friendly.

## Prerequisites

- Completed [Lab 10: Install Terraform](../lab-10/README.md)

> [!TIP]
> **Shortcut worth knowing.** If you already onboarded with automated configuration in
> Lab 3, you can download the Terraform FortiCNAPP generated instead of generating your
> own. Go to **Settings** > **Integrations** > **Cloud accounts** > **Deployment History**,
> open your deployment, and click **Terraform files** on any integration. This lab
> generates the code from scratch so you can see how the Lacework CLI does it.
- AWS account with appropriate permissions
- FortiCNAPP account access with API key configured

## Lab Steps

### Step 1: Open AWS CloudShell

1. Navigate to <a href="https://aws.amazon.com/" target="_blank">https://aws.amazon.com/</a>
2. Click **Sign into console**
3. After logging in, change to your local region (e.g., **Asia Pacific (Singapore)**) using the region selector in the top right of the AWS Console
4. Click the **CloudShell** icon in the top navigation bar (cloud icon with `>_` symbol)
5. Wait for CloudShell to initialize

### Step 2: Verify Lacework CLI Configuration

Verify that the Lacework CLI is configured and working:

```bash
lacework version
```

![CloudShell with lacework version output](images/aws-cloudshell-lacework-version.png)

### Step 3: Generate Terraform Configuration for AWS Integration

Use the Lacework CLI to generate Terraform code for AWS integration. This will create Terraform files for CloudTrail and Configuration assessment:

```bash
lacework generate cloud-account aws \
  --config --cloudtrail --noninteractive \
  --aws_region ap-southeast-1
```

**Parameters explained:**
- `--config`: Enable AWS Configuration integration
- `--cloudtrail`: Enable AWS CloudTrail integration
- `--noninteractive`: Run without prompts (uses defaults)
- `--aws_region ap-southeast-1`: Specify the AWS region (Asia Pacific - Singapore)

This command generates Terraform files in the `~/lacework/aws` directory.

### Step 4: Review Generated Terraform Files

Navigate to the generated Terraform directory and review the files:

```bash
cd ~/lacework/aws
ls -la
```

The CLI generates a single `main.tf` file that uses pre-built Terraform modules from the Lacework registry. All the complexity (IAM policies, S3 buckets, CloudTrail setup) is handled by the modules with sensible defaults.

Review the generated configuration:

```bash
cat main.tf
```

### Step 5: Initialize Terraform

CloudShell home is capped at 1 GB and the AWS provider alone is ~700 MB, so with the Lacework CLI (~50 MB) and Terraform binary (~150 MB) already in `~/bin`, there's barely enough room. CloudShell's split mount layout (`/home` on disk, `/tmp` on tmpfs) also trips up git when Terraform downloads modules. Set three env vars to work around both before running `init`:

```bash
mkdir -p /tmp/tfcache $HOME/tmp
export TF_PLUGIN_CACHE_DIR=/tmp/tfcache
export TMPDIR=$HOME/tmp
export GIT_DISCOVERY_ACROSS_FILESYSTEM=1
terraform init
```

What each one does:
- `TF_PLUGIN_CACHE_DIR=/tmp/tfcache` puts the provider cache on tmpfs (several GB) instead of home (1 GB).
- `TMPDIR=$HOME/tmp` keeps git's temp working dir on the same filesystem as `.terraform/modules/`, so module clones don't fail crossing the `/home` mount boundary.
- `GIT_DISCOVERY_ACROSS_FILESYSTEM=1` silences git's mount-crossing complaint if it does happen.

> **Troubleshooting**
>
> - `Error while installing ... it is still not detected in /tmp; this is a bug in Terraform`: CloudShell home is full (the "/tmp" message is misleading). Run `df -h $HOME` to confirm, then `rm -rf ~/lacework/aws/.terraform ~/lacework/aws/.terraform.lock.hcl /tmp/tfcache` and retry.
> - `Error while installing ...: text file busy`: a stale terraform process is holding the provider binary open. Run `pkill -f terraform`, then `rm -rf /tmp/tfcache` and retry.
> - `Could not download module ...: not a git repository (or any parent up to mount point /home)`: the env vars above (`TMPDIR` and `GIT_DISCOVERY_ACROSS_FILESYSTEM`) fix this. Make sure both are exported in the same shell as `terraform init`.

### Step 6: Review Terraform Plan

Review what Terraform will create before applying:

```bash
terraform plan
```

This shows you:
- Resources that will be created (IAM roles, CloudTrail, S3 buckets, etc.)
- Any changes that will be made
- Output values that will be generated

The plan output will display in your terminal. Review it carefully to understand what will be deployed.

**What will be created (40+ resources total):**

**AWS Configuration Integration:**
- 1 IAM Role (`lacework_iam_role`) - Cross-account role for Lacework to access AWS Config
- 7 IAM Policies - Audit policies for reading AWS Config data (base policy + 6 versioned policies for 2025)
- 7 IAM Role Policy Attachments - Attaching the audit policies to the IAM role
- 1 Lacework Integration (`lacework_integration_aws_cfg`) - Configuration assessment integration
- 1 Lacework External ID - Security identifier for the IAM role
- 2 Random IDs - Unique identifiers for resource naming
- 1 Time Sleep - Wait period for resource propagation

**AWS CloudTrail Integration:**
- 1 CloudTrail - AWS CloudTrail for API activity logging
- 2 S3 Buckets - One for CloudTrail logs, one for CloudTrail log delivery
- 2 S3 Bucket Policies - Access policies for the buckets
- 2 S3 Bucket Versioning - Enable versioning on both buckets
- 2 S3 Bucket Encryption - Server-side encryption configuration
- 2 S3 Bucket Public Access Block - Block public access to buckets
- 2 S3 Bucket Ownership Controls - Bucket ownership settings
- 1 S3 Bucket Logging - Access logging configuration
- 1 S3 Bucket ACL - Access control list for log bucket
- 1 KMS Key - Encryption key for CloudTrail logs
- 1 SNS Topic - Topic for CloudTrail notifications
- 1 SNS Topic Policy - Access policy for SNS topic
- 1 SNS Topic Subscription - Subscription to forward notifications
- 1 SQS Queue - Queue to receive CloudTrail notifications
- 1 SQS Queue Policy - Access policy for SQS queue
- 1 IAM Policy - Cross-account policy for CloudTrail access
- 1 IAM Role Policy Attachment - Attaching policy to IAM role
- 1 Lacework Integration (`lacework_integration_aws_ct`) - CloudTrail integration
- 1 Random ID - Unique identifier for resource naming
- 1 Time Sleep - Wait period for resource propagation

**Optional: Save the plan to a file:**

If you want to save the plan output for later review or documentation:

```bash
terraform plan > plan-output.txt
```

Then view it with:

```bash
cat plan-output.txt
```

### Step 7: Apply Terraform Configuration

If the plan looks correct, apply the Terraform configuration to deploy the integration:

```bash
terraform apply
```

When prompted, type `yes` to confirm the deployment.

**Note**: This process may take several minutes as it creates 46 resources including:
- IAM roles and policies (for both Config and CloudTrail integrations)
- CloudTrail with encryption and logging
- S3 buckets for CloudTrail logs (with versioning, encryption, and access controls)
- KMS key for encryption
- SNS topic and SQS queue for CloudTrail notifications
- Lacework integrations (Configuration and CloudTrail)
- Supporting resources (random IDs, time delays for propagation)

### Step 8: Verify Integration Deployment

After the Terraform apply completes successfully, verify the integration:

1. **Using Lacework CLI:**
```bash
lacework cloud-account list
```

You should see entries for:
- `AwsCfg` (Configuration integration)
- `AwsCtSqs` (CloudTrail integration)

2. **In FortiCNAPP Console:**
   - Log into FortiCNAPP console at <a href="https://partner-demo.lacework.net/" target="_blank">https://partner-demo.lacework.net/</a>
   - Ensure tenant is set to **FORTINETAPACDEMO**
   - Navigate to **Settings** > **Integrations** > **Cloud accounts**
   - Verify that your AWS account appears with both Configuration and CloudTrail integrations active

### Step 9: Clean Up Resources

After completing the lab, clean up the resources created by Terraform:

1. **Review what will be destroyed:**
```bash
terraform plan -destroy
```

This shows you what resources will be removed.

2. **Destroy the resources:**
```bash
terraform destroy
```

When prompted, type `yes` to confirm the destruction.

**Note**: This will:
- Remove the FortiCNAPP integrations from your AWS account
- Delete IAM roles and policies created by Terraform
- Remove S3 buckets created for CloudTrail (if created by Terraform)
- Remove SNS topics created for notifications (if created by Terraform)
- **Note**: If you're using an existing CloudTrail, it will not be deleted, only the integration will be removed

3. **Verify cleanup:**
```bash
lacework cloud-account list
```

The AWS integrations should no longer appear in the list.

4. **Clean up Terraform files:**
```bash
rm -rf ~/lacework/aws
```

## What did we do here?

We deployed the same CloudTrail and Configuration integrations from Lab 3, but this time with Terraform we own instead of the console wizard. The Lacework CLI generated the Terraform code, and `terraform apply` created 46 resources - IAM roles, S3 buckets, KMS encryption, SNS/SQS notifications, and the FortiCNAPP integrations themselves.

This is how you'd do it in production. The Terraform configuration can be checked into version control, reviewed in pull requests, and deployed through CI/CD pipelines. Need to integrate 50 AWS accounts? Fortinet provides organization-level Terraform modules that deploy across all accounts in your AWS Organization in one go. And when you're done, `terraform destroy` cleanly removes everything.


## Additional Resources

- <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/283460/aws-integration-terraform-from-aws-cloudshell" target="_blank">FortiCNAPP Documentation: AWS Integration Terraform from AWS CloudShell</a>


