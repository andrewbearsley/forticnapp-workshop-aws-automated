# Lab 11: Code Security for Applications (SCA)

## Objectives

Your application's security is only as strong as its dependencies. In this lab, we'll scan application code for vulnerabilities in third-party packages, hard-coded credentials, and license risks using FortiCNAPP's SCA scanner. We'll also generate a Software Bill of Materials (SBOM) - increasingly required for compliance, and essential for knowing your exposure when the next major vulnerability drops.

## Prerequisites

- Completed [Lab 8: Install Lacework CLI and Terraform](../lab-08/README.md)
- Lacework CLI configured with FortiCNAPP credentials
- AWS CloudShell access

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

![CloudShell with lacework version output](../lab-09/images/aws-cloudshell-lacework-version.png)

### Step 3: Install the SCA Component

Install the Lacework SCA scanning component:

```bash
lacework component install sca
```

This installs the Software Composition Analysis scanner that can analyze application dependencies, detect vulnerabilities, and identify license risks.

### Step 4: Update the SCA Component (Optional)

If the component is already installed, update it to ensure you have the latest version:

```bash
lacework component update sca
```

### Step 5: Clone the Example Repository

Clone the repository containing application code with intentional security issues:

```bash
cd ~
git clone https://github.com/andrewbearsley/lacework-sca-scan-example.git
cd lacework-sca-scan-example
```

This repository contains JavaScript/TypeScript application code with various security vulnerabilities, weaknesses, and license risks that FortiCNAPP can detect.

### Step 6: Scan the Application Code

Run the SCA scan on the current directory:

```bash
lacework sca scan .
```

To upload results to the FortiCNAPP platform, add `--save-results=true` (requires git metadata, which the cloned repo has):

```bash
lacework sca scan . --save-results=true
```

> **Note:** Unlike the IaC scanner (which uploads by default), SCA does not upload unless you pass `--save-results=true`. Even with the flag, uploaded results will not appear in **Risk Center > Code Security > Applications > Assessments** unless the repository is onboarded via **Code Security > Add integration** (GitHub/GitLab/Bitbucket connector) or the scan runs from a registered CI/CD pipeline. A CLI scan from CloudShell or a developer laptop alone won't surface in this view - this lab focuses on demonstrating the scanner locally.

### Step 7: Review Scan Results

The scan output will show:
- Summary statistics (artifacts analyzed, vulnerabilities found, secrets detected, etc.)
- **Vulnerabilities**: List of CVEs with severity levels (Critical, High, Medium, Low)
  - Direct and transitive dependencies affected
  - CVE IDs and descriptions
- **Weaknesses**: Common Weakness Enumeration (CWE) findings
  - Hard-coded credentials
  - SQL injection vulnerabilities
  - Authentication issues
  - And more
- License risks detected
- Copyrights detected

Review the findings and note:
- How many critical and high severity vulnerabilities were found
- What types of weaknesses are present (hard-coded credentials, SQL injection, etc.)
- Which packages have the most vulnerabilities
- How many secrets were detected

### Step 8: Generate Software Bill of Materials (SBOM)

Generate a Software Bill of Materials in CycloneDX JSON format:

```bash
lacework sca scan ./ -f cdx-json -o sbom.json
```

This creates an SBOM file that lists all dependencies and their versions, which can be used for:
- Compliance reporting
- Supply chain security tracking
- Dependency management
- Security audits

View the generated SBOM:

```bash
cat sbom.json
```

## What did we do here?

We scanned application code for security issues - not infrastructure this time, but the application itself. The SCA scanner found vulnerabilities in third-party packages (CVEs), hard-coded credentials, SQL injection risks, and license compliance issues.

We also generated a Software Bill of Materials (SBOM). This is increasingly required for compliance and supply chain security - it's a complete inventory of every dependency in your application and its version. When the next Log4j-style vulnerability drops, you can instantly check which of your applications are affected.

## Additional Resources

- <a href="https://docs.fortinet.com/document/lacework-forticnapp/latest/administration-guide/433465/software-composition-analysis-sca" target="_blank">Lacework SCA Scanning Documentation</a>
- <a href="https://github.com/andrewbearsley/lacework-sca-scan-example" target="_blank">Example Repository</a>


