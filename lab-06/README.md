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

> **Read the tag values from this screen, and search on the tag key.** The values are not
> stable. The administration guide documents `lacework_tag: self-deployment` and
> `lacework_integration: configuration`. A 2026 deployment record shows
> `lacework_integration: aws_config`. Resources deployed in March 2025 carry
> `lacework_tag: lacework-self-deploy`. All three are real, seen in the same tenant.
>
> Search on the key `lacework_tag` with any value. Do not filter on a value, or you will
> miss resources and leave them running.

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
   - **Tag value**: leave empty, so the search matches every value
7. Click **Search resources**.

Agentless scanning also tags its networking with `LWTAG_LACEWORK_AGENTLESS`. Run a second
search on that key to catch the VPC, subnet, route table, internet gateway and security
group it creates in each scanned region.

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

## Why this lab matters more than it looks

Orphaned agentless infrastructure keeps running.

The agentless scanner is driven by an **EventBridge rule on an hourly schedule**. Deleting
the integration in FortiCNAPP does not delete that rule. The rule keeps firing, keeps
starting an ECS task, and keeps costing money, while reporting to an integration that no
longer exists.

We found exactly this in a real Fortinet demo account: an agentless deployment from March
2025 still running `rate(1 hour)` in September 2026, pointing at an integration GUID that
had been deleted from the tenant. Nothing in the FortiCNAPP console showed it, because
there was no integration left to show.

Orphaned storage grows quietly too. The CloudTrail bucket left behind by that same 2025
deployment held **816,721 objects** by the time we emptied it, eighteen months of logs
nobody was reading. Deleting the integration in the console did nothing to it.

Check the EventBridge rule in every region you scanned:

```bash
aws events list-rules --region <region> \
  --query "Rules[?contains(Name,'lacework')].[Name,State,ScheduleExpression]" --output text
```

## What did we do here?

We removed both sides of the workshop: the integration records in FortiCNAPP and the
resources in AWS.

This is where the automated path pays off a second time. On the CloudFormation path, you
create the integration record in the console first, then launch a stack to build the AWS
side. CloudFormation never owns that record, so deleting the stack leaves an integration
polling a bucket that no longer exists, and you have to remember to delete it separately.

Automated configuration records every resource it created and tags all of them. Cleanup
becomes a tag search you can verify, and the deployment record tells you when you are done.
