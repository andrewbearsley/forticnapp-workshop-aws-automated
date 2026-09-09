# Lab 4: Install Lacework CLI and Trigger Inventory Scan

Normally, FortiCNAPP collects resource inventory on a scheduled cycle (up to 24 hours). To avoid waiting, we can trigger an immediate scan from the Lacework CLI!

## Objectives

FortiCNAPP collects resource inventory on a scheduled cycle that can take up to 24 hours. We don't want to wait that long. In this lab, we'll install the Lacework CLI in AWS CloudShell, verify our integrations from Lab 3 are working, and trigger an immediate inventory scan so compliance data starts populating right away.

## Prerequisites

- AWS account access
- FortiCNAPP account credentials
- Completed [Lab 3: Onboard AWS with Automated Configuration](../lab-03/README.md)

## Lab Steps

### Step 1: Log into AWS Console and Open CloudShell

1. Navigate to <a href="https://aws.amazon.com/" target="_blank">https://aws.amazon.com/</a>
2. Click **Sign into console**
3. After logging in, change to your local region (e.g., **Asia Pacific (Singapore)**) using the region selector in the top right of the AWS Console
4. Click the **CloudShell** icon in the top navigation bar (cloud icon with `>_` symbol)
5. Wait for CloudShell to initialize (this may take a minute the first time)
6. Once CloudShell opens, you'll have a Linux-based terminal environment ready to use

### Step 2: Set Up Installation Directory

Create a bin directory in your home folder and add it to your PATH:

```bash
mkdir -p "$HOME/bin"
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Install Lacework CLI

In the CloudShell terminal, run:

```bash
curl https://raw.githubusercontent.com/lacework/go-sdk/main/cli/install.sh | bash -s -- -d "$HOME/bin"
```

This will download and install the Lacework CLI tool to your home bin directory.

![CloudShell showing Lacework CLI successfully installed](images/cloudshell-lacework-cli-installed.png)

### Step 4: Download API Key from FortiCNAPP

An existing service user **AWS Lab** has been pre-configured with the necessary permissions. Download the API key for this user:

1. Log into FortiCNAPP console at <a href="https://partner-demo.lacework.net/" target="_blank">https://partner-demo.lacework.net/</a>
2. Ensure tenant is set to **FORTINETAPACDEMO**
3. Navigate to **Settings** > **Configuration** > **API keys**
4. Click on the **Service user API keys** tab
5. Find the API key for the **AWS Lab** service user
6. Click on the ellipsis (three dots) next to the API key and select **Download** to download the key as JSON

![API keys page showing Service user API keys with Download option](images/forticnapp-download-api-key.png)

7. Open the downloaded JSON file and note the values. Keep these credentials ready for the next step

### Step 5: Configure CLI

In CloudShell, run:

```bash
lacework configure
```

Enter your FortiCNAPP account credentials when prompted. These values are taken from the JSON file downloaded in the previous step:

```json
{
  "keyId": "FORTINET_5DFDAF3B...",
  "secret": "_f1b528...",
  "account": "partner-demo.lacework.net",
  "subAccount": "fortinetapacdemo"
}
```

- **Account**: `partner-demo.lacework.net` (the `account` value from the JSON file)
- **API Key**: The `keyId` value from the JSON file
- **API Secret**: The `secret` value from the JSON file
- **Sub-Account** (if prompted): The `subAccount` value from the JSON file

### Step 6: Verify CLI Installation and List Integrations

```bash
lacework version
lacework cloud-account list
```

You should see entries for your AWS account including:
- `AwsCfg` (Configuration integration from Lab 3)

You will not see `AwsCtSqs`. Lab 3 leaves CloudTrail out, because discovery fails on any
account inside an AWS Organization that has an organization trail. See the troubleshooting
section in [Lab 3](../lab-03/README.md).
- `AwsSidekick` (Agentless Workload Scanning from Lab 3)

### Step 7: Trigger Inventory Scan

Normally, FortiCNAPP collects resource inventory on a scheduled cycle (up to 24 hours). To avoid waiting, you can trigger an immediate scan.

```bash
lacework compliance aws scan
```

This triggers a resource inventory collection for all integrated AWS accounts. The scan will run in the background and takes 1-2 hours to complete. Once finished, compliance reports and resource inventory data will be populated in the FortiCNAPP console.

**Note:** Only one scan can run at a time. If another student has already triggered a scan, your request will be ignored until the current scan completes.

## What did we do here?

We installed the Lacework CLI in CloudShell and connected it to FortiCNAPP using an API key. This gives us command-line access to FortiCNAPP - useful for automation, scripting, and doing things the console can't do.

The big win here was triggering an inventory scan immediately. Normally FortiCNAPP collects resource inventory on a scheduled cycle that can take up to 24 hours. Instead of waiting, we kicked it off manually so compliance data starts populating right away.
