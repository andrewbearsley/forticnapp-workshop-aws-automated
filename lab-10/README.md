# Lab 10: Code Security for Infrastructure as Code (IaC)

## Objectives

The best time to catch a misconfigured security group or unencrypted S3 bucket is before it gets deployed - not after it's running in production. In this lab, we'll scan Terraform code for security issues using FortiCNAPP's IaC scanner. This is shift-left security: finding misconfigurations in code so they never reach AWS.

## Prerequisites

- Completed [Lab 8: Install Lacework CLI and Terraform](../lab-08/README.md)
- Lacework CLI configured with FortiCNAPP credentials
- AWS CloudShell access

## Lab Steps

### Step 1: Open AWS CloudShell

1. Log into AWS Console at <a href="https://aws.amazon.com/" target="_blank">https://aws.amazon.com/</a>
2. Change to your local region (e.g., **Asia Pacific (Singapore)**) using the region selector in the top right
3. Click the **CloudShell** icon in the top navigation bar
4. Wait for CloudShell to initialize

### Step 2: Clone the Example Repository

Clone the repository containing Terraform code with intentional security issues:

```bash
cd ~
git clone https://github.com/andrewbearsley/lacework-iac-scan-example.git
cd lacework-iac-scan-example/example-terraform
```

This repository contains Terraform configurations with various security issues that FortiCNAPP can detect.

### Step 3: Verify Lacework CLI Configuration

Ensure your Lacework CLI is still configured:

```bash
lacework version
```

If you need to reconfigure, run:

```bash
lacework configure
```

### Step 4: Install the IaC Component

Install the Lacework IaC scanning component:

```bash
lacework component install iac
```

This installs the Infrastructure as Code scanner that can analyze Terraform, CloudFormation, and other IaC formats.

### Step 5: Update the IaC Component (Optional)

If the component is already installed, update it to ensure you have the latest version:

```bash
lacework component update iac
```

### Step 6: Scan the Terraform Code

Run the IaC scan on the current directory:

```bash
lacework iac scan
```

This will:
- Analyze the Terraform files in the current directory
- Detect security misconfigurations and vulnerabilities
- Upload the scan results to FortiCNAPP (controlled by `--upload`, default `true`)
- Display findings in the terminal

> **Note:** The CLI uploads results to the FortiCNAPP platform, but they will not appear in **Risk Center > Code Security > Infrastructure (IaC) > Assessments** unless the repository is onboarded via **Code Security > Add integration** (GitHub/GitLab/Bitbucket connector) or the scan runs from a registered CI/CD pipeline. A CLI scan from CloudShell or a developer laptop alone won't surface in this view - this lab focuses on demonstrating the scanner locally.

### Step 7: Review Scan Results

The scan output will show:
- Total number of findings
- Policy IDs and severity levels (Critical, High, Medium, Low)
- File paths and line numbers where issues are found
- Whether each finding passed or failed
- Upload reference for viewing results in the FortiCNAPP console

Review the findings and note:
- How many critical and high severity issues were found
- What types of security issues are present (encryption, access controls, networking, etc.)
- Which files contain the most security issues

## What did we do here?

We shifted security left by scanning Terraform code before it gets deployed. The IaC scanner analysed the example repository and found over 100 security issues - things like unencrypted storage, overly permissive security groups, and missing access controls.

The point is to catch these misconfigurations in code, not in production. If this were part of a CI/CD pipeline, those findings would show up as pull request comments before the code ever reaches AWS. Fix it in the code, not after the breach.

## Additional Resources

- <a href="https://docs.fortinet.com/document/lacework-forticnapp/latest/administration-guide/651014/getting-started-with-opal" target="_blank">Lacework IaC Scanning Documentation</a>
- <a href="https://github.com/andrewbearsley/lacework-iac-scan-example" target="_blank">Example Repository</a>



