# Lab 6: Clean Up Workshop Resources

## Objectives

Leaving workshop resources running in AWS costs money. In this lab, we'll remove
everything the workshop created: the integrations from Lab 3, the resources they built in
AWS, and the EC2 instances from Labs 4 and 5.

Cleanup on the automated path is easier than on the CloudFormation path, because
FortiCNAPP recorded exactly what it created. You do not have to guess.

## Prerequisites

- Access to the AWS Console
- FortiCNAPP console access, tenant **FORTINETAPACDEMO**

## Find what was created

Before deleting anything, get the list.

1. Go to **Settings** > **Integrations** > **Cloud accounts**.
2. Select the **Deployment History** tab.
3. Open the deployment you created in Lab 3.
4. Expand each integration to see its **Resources** table.

![Deployment record showing the resource list and the tags applied to every resource](images/forticnapp-deployment-resources.png)

Each integration lists every resource by ARN, name and type. Each one also states the
exact tags applied, for example:

> All cloud resources are tagged with `lacework_tag: self-deployment` and
> `lacework_integration: aws_config`

> **Read the tag values from this screen.** The administration guide lists the
> `lacework_integration` value for the configuration integration as `configuration`, while
> the product applies `aws_config`. The deployment record is authoritative.

Keep this page open. It is your cleanup checklist.

## Lab Steps

### Step 1: Delete the Integrations in FortiCNAPP

1. Go to **Settings** > **Integrations** > **Cloud accounts**.
2. Select the **Cloud Accounts** tab.
3. Find your AWS account ID in the list.
4. Delete each integration on that account: Configuration, CloudTrail and Agentless.

### Step 2: Delete the AWS Resources by Tag

Deleting the integration in FortiCNAPP does not delete the resources in your AWS account.
Remove them with the tag search.

1. Log into the AWS Console.
2. Select the region you used in Lab 3.
3. Go to **Resource Groups & Tag Editor** > **Tag Editor**.
4. Set **Regions** to your workshop region, or **All regions** to be thorough.
5. Set **Resource types** to **All supported resource types**.
6. Add this tag filter:
   - **Tag key**: `lacework_tag`
   - **Tag value**: `self-deployment`
7. Click **Search resources**.

The result is every resource automated configuration created. Work through the list and
delete each one. Cross-check against the Resources table on the deployment record.

Expect to see IAM roles and policies, S3 buckets, KMS keys, SNS topics and SQS queues, an
ECS cluster for agentless scanning, and Lambda functions.

> **Order matters.** Empty an S3 bucket before you delete it. Delete resources that depend
> on an IAM role before the role itself.

### Step 3: Terminate the EC2 Instances

#### Linux instance (from Lab 4)

1. Go to the **EC2** service.
2. Find the instance you created in Lab 4, for example `FortiCNAPP-Linux-Agent`.
3. Select it, then choose **Instance state** > **Terminate instance**.
4. Confirm.

![Terminating an EC2 instance from the AWS Console](images/aws-ec2-terminate-instance.png)

#### Windows instance (from Lab 5)

1. Find the instance you created in Lab 5, for example `FortiCNAPP-Windows-Agent`.
2. Select it, then choose **Instance state** > **Terminate instance**.
3. Confirm.

### Step 4: Verify

1. In AWS, re-run the Tag Editor search for `lacework_tag = self-deployment`. It should
   return nothing.
2. In AWS, confirm both EC2 instances show **terminated**.
3. In FortiCNAPP, confirm your AWS account no longer appears under **Cloud accounts**.

## If you took the advanced track

Labs 8 to 11 create their own resources. See
[Lab 12: Scripted Cleanup of All Workshop Resources](../lab-12/README.md), which runs
`terraform destroy` for the Lab 9 deployment and sweeps the account.

## What did we do here?

We removed both sides of the workshop: the integration records in FortiCNAPP and the
resources in AWS.

This is where the automated path pays off a second time. On the CloudFormation path, you
create the integration record in the console first, then launch a stack to build the AWS
side. CloudFormation never owns that record, so deleting the stack leaves an integration
polling a bucket that no longer exists, and you have to remember to delete it separately.

Automated configuration records every resource it created and tags all of them. Cleanup
becomes a tag search you can verify, and the deployment record tells you when you are done.
