# Lab 2: Get Temporary AWS Credentials

## Objectives

Automated configuration builds your integration for you. To do that, FortiCNAPP needs AWS
credentials with enough permission to create IAM roles, buckets, keys and queues.

You do not hand over a long-lived access key. You hand over a short-lived one. In this
lab, we'll generate temporary AWS STS credentials. FortiCNAPP uses them once to build the
integration, then discards them and runs on the cross-account role it created.

## Prerequisites

- AWS account with administrator access
- Either AWS IAM Identity Center access, or an assumable IAM role

## The guide is built into the console

FortiCNAPP ships these instructions in the product. On the **Authorize** step of the
wizard, click **Open Guide** to open the Authorization Guide panel.

![FortiCNAPP Authorization Guide panel open on the Authorize step](images/forticnapp-authorization-guide.png)

Use this lab to prepare your credentials before you start Lab 3, so the wizard does not
sit waiting while you go and find them.

## Lab Steps

**Pick your method from how you signed in to AWS.** This is not a preference, it is a
constraint.

| How you signed in | Use | Why |
|---|---|---|
| AWS IAM Identity Center (SSO) | **Method A** | The access portal issues a role session, which can complete discovery. |
| An IAM user, or anything else | **Method B** | Assume a role. A role session can complete discovery. |

> **Do not use plain `aws sts get-session-token`.** It looks like the obvious CloudShell
> shortcut, and FortiCNAPP's own in-product guide offers it, but the credentials it returns
> **cannot complete discovery**.
>
> Discovery calls IAM APIs. AWS blocks IAM API calls from `GetSessionToken` credentials
> unless MFA information was included in the request. The wizard fails at Task 2 with:
>
> ```
> operation error IAM: ListAttachedUserPolicies, StatusCode: 403
> InvalidClientTokenId: The security token included in the request is invalid
> ```
>
> Turning off *Simulate IAM permissions* does not fix it. That only changes which IAM call
> fails first.
>
> If you must use `get-session-token`, add MFA with `--serial-number` and `--token-code`.
> Those credentials can call IAM.

#### Not sure which one you are?

Run this in AWS CloudShell:

```bash
aws sts get-caller-identity --query Arn --output text
```

| The ARN looks like | You are | Use |
|---|---|---|
| `arn:aws:sts::<id>:assumed-role/AWSReservedSSO_...` | Federated through Identity Center | Method A |
| `arn:aws:iam::<id>:user/<name>` | A plain IAM user | Method B |

### Method A: AWS IAM Identity Center

1. Go to your AWS access portal.
2. Select the account you want to integrate.
3. Click **Access keys** next to the role you will use.
4. Select **Option 3: Use individual values in your AWS service client**.
5. Copy these three values:
   - **AccessKeyId**
   - **SecretAccessKey**
   - **SessionToken**

Go to Lab 3.

### Opening CloudShell

Method B needs it. Method A does not.

CloudShell has the AWS CLI preinstalled and already signed in as your console identity, so
you install nothing and configure nothing.

1. Log into the AWS Console.
2. Change to your local region using the region selector at the top right, for example
   **Asia Pacific (Singapore)**.
3. Click the **CloudShell** icon in the toolbar at the top right, or search for
   **CloudShell** in the console search bar.
4. Wait for the shell prompt.

### Method B: Assume a role

Your account needs a role with the required permissions and a trust policy that lets your
IAM user assume it. Run this in CloudShell.

1. Assume the role:

   ```bash
   aws sts assume-role \
     --role-arn "YourRoleArn" \
     --role-session-name "lacework-onboarding" \
     --duration-seconds 21600
   ```

2. Copy these three values from the `Credentials` block:
   - `AccessKeyId`
   - `SecretAccessKey`
   - `SessionToken`

   To copy from CloudShell, select the text and use **Actions** > **Copy**.

![Authorization Guide showing the AWS CLI commands](images/forticnapp-authorization-guide-cli.png)

> **Instructor note.** The in-product Authorization Guide also lists
> `aws sts get-session-token` without MFA. Do not use it. See the warning above.

## Permissions

Fortinet recommends **full administrator access for your first deployment**. AWS
permissions here are complex, and a partial policy fails during discovery.

Once you know the flow, use least privilege instead. The Authorization Guide panel offers
four ready-made policy documents to download:

| File | Covers |
|---|---|
| `aws_config_policy.json` | Configuration integration |
| `aws_cloudtrail_policy.json` | CloudTrail integration |
| `aws_agentless_policy.json` | Agentless Workload Scanning |
| `aws_eks_auditlog_policy.json` | EKS audit log integration |

> **Gotcha**: if you plan to use the optional **Simulate IAM permissions** check in Lab 3,
> your credentials additionally need `iam:SimulatePrincipalPolicy`, plus `iam:GetRole` for
> assumed roles.
>
> Note this is a *permissions* requirement on top of the *credential type* requirement
> above. A role session with the wrong policy fails the simulation; a `GetSessionToken`
> session fails it no matter what policy is attached.

## Important

- Set the duration to suit your session. `21600` seconds gives you six hours.
- Treat the three values as secrets. Do not paste them into chat, email or a shared doc.
- FortiCNAPP uses these credentials only to build the integration. It then runs on the
  cross-account role it created, which holds scoped read permissions.

## What did we do here?

We created a short-lived AWS credential set for the integration to run under.

This is the step that makes automated configuration safe. The CloudFormation path never
asks for a credential, because you run each stack yourself. That costs you two console
walk-throughs. Automated configuration trades those for one bounded credential, and gives
you preflight validation and automatic rollback in return.

## Additional Resources

- <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/331296/obtaining-temporary-cloud-account-credentials" target="_blank">FortiCNAPP Administration Guide: Obtaining temporary cloud account credentials</a>
- <a href="https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html" target="_blank">AWS STS GetSessionToken</a>
- <a href="https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html" target="_blank">AWS STS AssumeRole</a>
