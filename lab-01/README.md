# Lab 1: What FortiCNAPP Sees

## Objectives

Before you connect anything, look at an environment that is already connected and full of
real findings. Five questions, in the order you would actually ask them on your first day
owning a cloud estate.

By the end you will know what the later labs are building towards, and roughly where
things live in the console.

## Prerequisites

- Your email address added to the FortiCNAPP demo environment

> **This lab uses a different tenant to the rest of the workshop.** Lab 1 runs in
> **FORTIDEMO-2026-04**, which is full of demo data. From Lab 3 onward you work in
> **FORTINETAPACDEMO**, where you onboard your own AWS account. Watch the tenant name at
> the bottom of the left navigation.

## Step 1: Sign in and pick the tenant

1. Go to <a href="https://partner-demo.lacework.net/" target="_blank">https://partner-demo.lacework.net/</a>
2. Enter your email address and click **Get sign in link**.
3. Open the link from your email.
4. If an onboarding wizard appears, choose **Go to platform**.
5. At the **bottom of the left navigation**, click the account name and select
   **FORTIDEMO-2026-04**.

![Tenant selector at the bottom of the left navigation, showing FORTIDEMO-2026-04 and FORTINETAPACDEMO](images/forticnapp-tenant-selector.png)

**Checkpoint:** the bottom of the left navigation reads `FORTIDEMO-2026-04`.

## Step 2: Turn off email notifications

Do this now, before you go any further. This tenant is noisy, and by default it will email
you about it.

1. Go to **Settings** > **My profile**.
2. Turn **off** **Default email notification**.
3. Turn **off** **Receive monthly updates from FortiCNAPP**.

![My profile preferences with Default email notification and monthly updates turned off](images/forticnapp-email-notifications.png)

These are **your** preferences only. You are not changing anything for anyone else in the
tenant.

> Repeat this in **Lab 3**, the first time you enter FORTINETAPACDEMO. The setting is per
> tenant.

## Step 3: How bad is it?

Go to **Dashboard**.

Three numbers tell you where you stand. Everything else in the console is a way of drilling
into one of them.

![Dashboard showing threat alerts, non-compliant resources and exposed fixable hosts](images/forticnapp-dashboard.png)

| Widget | What it counts | Which lab creates it |
|---|---|---|
| **Threat alert overview** | Something is happening that looks like an attack | Lab 3, CloudTrail and agentless |
| **Non-compliant resources** | Configuration that fails a benchmark | Lab 3, configuration |
| **Exposed Fixable Hosts** | Internet-reachable hosts with a patchable vulnerability | Labs 3 to 5 |

**Checkpoint:** you can read a number off each of the three widgets.

> Worth pausing on **Exposed Fixable Hosts**. Not "hosts with vulnerabilities", which is
> every host. Exposed, and fixable. That is the list you would actually work through on a
> Monday morning.

## Step 4: What have I got?

Go to **Inventory** > **Resource Inventory**.

![Resource Inventory listing cloud resources with alerts, compliance violations and attack paths](images/forticnapp-resource-inventory.png)

1. Look at the total resource count at the top.
2. Scroll the table. Note the **Alerts**, **Compliance violations** and **Attack Paths**
   columns beside each resource.
3. Use **Show more** to filter, for example by resource type.

**Checkpoint:** you can see a resource with a non-zero number in at least one of those
three columns.

Nobody typed this inventory in. FortiCNAPP asked AWS what exists. In a data centre you know
what is in the rack because you put it there; in a cloud account, anyone with credentials
can create something at three in the morning. Asking the provider is the only way to know.

## Step 5: What is happening right now?

Go to **Threat Center** > **Alerts**.

![Threat Alerts filtered to high severity, showing compromised hosts and privileged containers](images/forticnapp-threat-alerts.png)

1. Open one alert titled **Potentially Compromised Host**.
2. Read the description and the affected resource.
3. Go back and look at **Threat Center** > **Cloud Activity**, which is the CloudTrail
   record of who did what in the account.

**Checkpoint:** you have opened one alert and can say which host it refers to.

Alerts come from behaviour, not configuration. A host reaching out to somewhere it never
has before is a behavioural signal, and it needs the agent or CloudTrail to spot it. That is
why Labs 3, 4 and 5 exist.

## Step 6: What do I fix first?

You have thousands of findings and a finite Tuesday. Two views help you choose.

### Attack Path

Go to **Risk Center** > **Findings** > **Attack Path**.

![Attack Path showing top risky hosts, container images, exposed secrets and data assets](images/forticnapp-attack-path.png)

Attack Path only lists combinations that are genuinely reachable and genuinely damaging: a
vulnerable host that is internet-facing **and** holds credentials to something valuable.

**Checkpoint:** find the entry under **Top risky paths with exposed secrets**. That is a
private key sitting on a reachable host.

One vulnerability on an isolated box is a ticket. The same vulnerability on an
internet-facing box with a key to the database is an incident. Attack Path is how you tell
the two apart.

### Compliance

Go to **Risk Center** > **Findings** > **Compliance** > **Cloud**.

![Cloud Compliance dashboard showing frameworks including CIS, ISO 27001, NIST CSF and SOC 2](images/forticnapp-cloud-compliance.png)

1. Look at the framework list: CIS, ISO/IEC 27001, NIST CSF, SOC 2 and others.
2. Pick a framework and open it to see which policies fail and on which resources.

**Checkpoint:** you can name one framework and the number of non-compliant resources
against it.

The same underlying findings, scored against whichever standard your auditor cares about.
You do not re-scan for each one.

## Step 7: Could I have caught it earlier?

Go to **Risk Center** > **Findings** > **Code Security**.

**Infrastructure (IaC)** scans the Terraform and CloudFormation that builds the
infrastructure.

![IaC assessments listing repositories with critical, high, medium and low findings](images/forticnapp-iac-findings.png)

**Applications** scans what your code depends on.

![Application vulnerabilities listing CVEs in third party libraries](images/forticnapp-app-vulnerabilities.png)

**Checkpoint:** find a Log4j CVE in the Applications list. You already know that one.

Everything up to this point finds problems that are already running. This finds them in the
code, before they exist in AWS. You do both in Labs 7 and 8.

## Optional: ask your own question

**Explorer** builds a visual query across resources and their relationships.
**Search** runs a text query across everything FortiCNAPP holds.

Both are worth five minutes if you have them. Neither is needed for the later labs.

## What did we do here?

We went from "how bad is it" to "how would I have prevented it", which is the same path you
walk during a real incident.

Hold on to the shape, because the rest of the workshop fills it in:

| Question | You built it in |
|---|---|
| What have I got, and is it compliant | Lab 3 |
| What is happening on my workloads | Labs 4 and 5 |
| Could I have caught it in code | Labs 7 and 8 |

Next: [Lab 2: Get Temporary AWS Credentials](../lab-02/README.md).
