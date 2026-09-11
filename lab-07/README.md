# Lab 7: Code Security for Infrastructure as Code (IaC)

## Objectives

Labs 3 to 5 found problems in a **running** account. This lab finds them in the Terraform
that would have created it, before anything exists.

That is the whole idea behind shift left. A public S3 bucket found in production is an
incident with a clock on it. The same bucket found in a pull request is a two-line change
nobody outside the team hears about.

The scanner reads Terraform, CloudFormation and the other IaC formats, and checks them
against the same policies FortiCNAPP uses on live resources.

## Prerequisites

- Completed [Lab 6](../lab-06/README.md), with the CLI working in CloudShell

## Lab Steps

You should still be in CloudShell from Lab 6. If it timed out, reopen it and run
`source ~/.bashrc` to put the CLI back on your PATH.

### Step 1: Install the IaC Scanner

The CLI ships small and pulls in what it needs:

```bash
lacework component install iac
```

Already installed from a previous run? Update it instead:

```bash
lacework component update iac
```

**Checkpoint:** the command finishes without an error.

### Step 2: Get Some Code to Scan

This repository is deliberately full of bad Terraform:

```bash
cd ~
git clone https://github.com/andrewbearsley/lacework-iac-scan-example.git
cd lacework-iac-scan-example/example-terraform
```

### Step 3: Scan It

```bash
lacework iac scan
```

It reads every Terraform file below the current directory, checks each against policy, and
prints what failed. Uploading to the platform is on by default, controlled by `--upload`.

### Step 4: Read the Output

You will get a lot of findings. Do not try to read them all. Work through these three
questions instead:

1. **How many are Critical or High?** That is the number anyone reacts to first.
2. **What kinds of problem are they?** Group them in your head: encryption off, access too
   open, logging missing. Most estates repeat the same few mistakes.
3. **Which file is the worst?** One module usually accounts for a large share, which is
   where you would start.

Each finding gives you a policy ID, a severity, and a **file and line number**. That last
part is what makes this useful: it points a developer at the exact line, in their own
editor, in their own language.

**Checkpoint:** you can name the single most common category of finding in this repo.

> **Why your scan does not show up in the console.** Look under **Risk Center** >
> **Findings** > **Code Security** > **Infrastructure (IaC)** and you will not find it. That is expected. A
> CLI scan from CloudShell has no repository behind it.
>
> The **Assessments** view fills up when a repository is onboarded through
> **Code Security** > **Add integration** (GitHub, GitLab or Bitbucket), or when the scan
> runs inside a registered CI/CD pipeline. That is how it runs for real. This lab is the
> scanner on its own, so you can see what it does.

## What did we do here?

We ran the platform's policies against code instead of against cloud.

Same checks, different moment. The scanner found well over a hundred issues in a repo that
would have deployed perfectly happily. It named the file and the line for every one.

Wired into a pipeline, these findings arrive as comments on a pull request, before the plan
is ever applied. The fix costs a developer five minutes instead of costing you an incident
review.

## Additional Resources

- <a href="https://docs.fortinet.com/document/lacework-forticnapp/latest/administration-guide/651014/getting-started-with-opal" target="_blank">Lacework IaC Scanning Documentation</a>
- <a href="https://github.com/andrewbearsley/lacework-iac-scan-example" target="_blank">Example Repository</a>

---

Next: [Lab 8: Code Security for Applications (SCA)](../lab-08/README.md).
