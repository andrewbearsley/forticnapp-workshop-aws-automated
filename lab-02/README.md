# Lab 2: Get Temporary AWS Credentials

## Objectives

In Lab 3, FortiCNAPP builds your integration for you: IAM roles, buckets, keys, queues, a
CloudTrail trail. To do that it needs permission to create things in your AWS account.

You are not handing over a permanent key. You are issuing a **visitor pass that expires in
an hour**. FortiCNAPP uses it once to build the integration, then throws it away and runs
on the read-only role it created. That role is what stays.

This lab gets you that pass, so the wizard in Lab 3 does not sit waiting while you go and
find it.

## Prerequisites

- An AWS account with administrator access
- Either AWS IAM Identity Center access, or an IAM user that can create a role

## Which method do you need?

Not a preference. It depends on how you signed in to AWS.

Ask AWS who you are. You do that in **CloudShell**, a Linux terminal built into the console
with your credentials already loaded.

### Opening CloudShell

1. Check the **region selector** reads **Asia Pacific (Singapore)**.
2. Click the **`>_`** icon in the top bar. **CloudShell** at the bottom left does the same
   thing.

![AWS Console Home, with the region selector and both CloudShell buttons highlighted](images/aws-console-cloudshell.png)

CloudShell opens as a panel across the bottom. First launch takes a minute.

![CloudShell panel open at a prompt, with the region tab showing ap-southeast-1](images/aws-cloudshell-open.png)

### Who are you?

```bash
aws sts get-caller-identity --query Arn --output text
```

![CloudShell showing the ARN returned by get-caller-identity](images/aws-cloudshell-whoami.png)

Read the ARN it prints:

| If it says | You are | Go to |
|---|---|---|
| `arn:aws:iam::<id>:user/<name>` | A plain IAM user, which is the lab setup | **Method B** |
| `arn:aws:sts::<id>:assumed-role/AWSReservedSSO_...` | Signed in through Identity Center | **Method A** |

**Checkpoint:** you know which of the two methods you are following.

---

## Method A: AWS IAM Identity Center

This is the Fortinet staff path. You will not be in CloudShell for it, the values come
straight out of the access portal.

1. Open your AWS access portal.
2. Go to the **Accounts** tab and select the account you want to integrate.
3. Click **Access keys** next to the role you will use.
4. Choose **Option 3: Use individual values in your AWS service client**.
5. Copy all three values somewhere you can paste from:
   - **AccessKeyId**
   - **SecretAccessKey**
   - **SessionToken**

**Checkpoint:** you have three values, and the first starts with `ASIA`.

Skip to [Lab 3](../lab-03/README.md).

---

## Method B: Create a role, then assume it

You are an administrator in your own lab account, so you can create the role yourself.
Nobody needs to provision it for you.

Run all of this in CloudShell.

### 1. Create the role

```bash
ACCT=$(aws sts get-caller-identity --query Account --output text)
USER=$(aws sts get-caller-identity --query Arn --output text | awk -F/ '{print $NF}')

cat > trust.json <<JSON
{"Version":"2012-10-17","Statement":[{
  "Effect":"Allow",
  "Principal":{"AWS":"arn:aws:iam::${ACCT}:user/${USER}"},
  "Action":"sts:AssumeRole"}]}
JSON

aws iam create-role --role-name forticnapp-onboarding \
  --assume-role-policy-document file://trust.json
```

The trust policy says one thing: *this role may be assumed by me, and nobody else.*

### 2. Give it permissions

```bash
aws iam attach-role-policy --role-name forticnapp-onboarding \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

### 3. Assume it

Wait about ten seconds for the role to propagate, then:

```bash
sleep 10
read -r AK SK ST < <(aws sts assume-role \
  --role-arn "arn:aws:iam::${ACCT}:role/forticnapp-onboarding" \
  --role-session-name lacework-onboarding --duration-seconds 3600 \
  --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text)

printf '\n=== Access key ID ===\n%s\n\n=== Secret access key ===\n%s\n\n=== Session token ===\n%s\n\n' "$AK" "$SK" "$ST"
```

The `printf` exists only to label the output. Without it AWS returns three values separated
by tabs, and the session token is long enough that you cannot tell where it starts.

![CloudShell showing three labelled credential blocks, values blacked out](images/aws-cloudshell-credentials.png)

**Checkpoint:** three labelled blocks print, and the access key ID starts with `ASIA`.

To copy a value, select it with the mouse and press **Cmd+C**, or **Ctrl+Shift+C** on
Windows and Linux. Select from the start of the value to the end of the line, not the label.

> **Paste these into the Lab 3 wizard only.** Not into chat, not into a shared document,
> and take care if your screen is being shared. They are live credentials for an hour.

> **Do not raise `--duration-seconds` above 3600.** CloudShell may already be running as a
> role session. AWS caps role chaining at one hour.

---

## Permissions

`AdministratorAccess` keeps the lab moving. For a customer, use least privilege instead.

The **Authorization Guide** panel in the Lab 3 wizard (click **Open Guide** on the
Authorize step) offers four ready-made policy documents:

| File | Covers |
|---|---|
| `aws_config_policy.json` | Configuration |
| `aws_cloudtrail_policy.json` | CloudTrail |
| `aws_agentless_policy.json` | Agentless Workload Scanning |
| `aws_eks_auditlog_policy.json` | EKS audit log |

![FortiCNAPP Authorization Guide panel, open on the Authorize step](images/forticnapp-authorization-guide.png)

If you plan to use **Simulate IAM permissions** in Lab 3, the credentials also need
`iam:SimulatePrincipalPolicy`, plus `iam:GetRole` for assumed roles.

## If it goes wrong in Lab 3

| Symptom | Cause |
|---|---|
| `InvalidClientTokenId` at Configure, Task 2 | You used plain `aws sts get-session-token`. AWS blocks IAM API calls from those credentials unless MFA was included, and discovery calls IAM. Use a role session. |
| `Session token is required` | You pasted a long-lived `AKIA` key. The wizard needs a session token; static keys are rejected. |
| `Cannot call GetSessionToken with session credentials` | You are federated. Use Method A. |
| Credentials expired mid-wizard | They last an hour. Run Method A or B again. |

## What did we do here?

We issued a short-lived credential and nothing else.

This is the step that makes automated configuration safe to use on a customer account. The
CloudFormation path never asks for a credential, because you launch each stack yourself,
and it costs you two console walk-throughs. Here you trade one bounded hour of access for
a wizard that does the work, plus a preflight permission check you would not otherwise get.

Next: [Lab 3: Onboard AWS with Automated Configuration](../lab-03/README.md).
