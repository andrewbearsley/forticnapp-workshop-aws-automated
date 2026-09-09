# Lab 5: Install Linux Agent

## Objectives

Agentless scanning (Lab 3) gives you periodic snapshots, but for deeper monitoring you need the agent. In this lab, we'll launch a Linux EC2 instance and install the FortiCNAPP agent (datacollector). Once running, it collects process, network, and file activity and sends it to FortiCNAPP every hour - this is how it builds behavioural baselines and detects anomalies.

## Prerequisites

- AWS account with EC2 launch permissions

## Lab Steps

### Step 1: Log into AWS Console

1. Navigate to <a href="https://aws.amazon.com/" target="_blank">https://aws.amazon.com/</a>
2. Click **Sign into console**
3. After logging in, change to your local region (e.g., **Asia Pacific (Singapore)**) using the region selector in the top right of the AWS Console

### Step 2: Create Linux EC2 Instance

1. Navigate to **EC2** service in AWS Console

![EC2 dashboard with Launch Instance button](images/aws-ec2-pre-launch.png)

2. Click **Launch Instance**
3. Configure the instance:

![Launch an instance configuration page](images/aws-ec2-launch-details.png)

   - **Name**: Enter a name (e.g., `FortiCNAPP-Linux-Agent`)
   - **Application and OS Images**: Select **Ubuntu**
   - **Instance type**: Select **t3.micro**
   - **Key pair (login)**: Select **Proceed without a key pair** (we'll use EC2 Instance Connect)
4. **Network settings**: leave the defaults as-is. The launch wizard will create a new security group (named `launch-wizard-N`) with an inbound rule for SSH from anywhere, which is what Instance Connect needs.

   > Don't switch this to "Select existing security group" and pick the VPC's `default` SG. That one only allows traffic between resources sharing the same SG, so Instance Connect won't be able to reach the instance.
5. **Configure storage**: Leave default (8 GB gp3)
6. Click **Launch Instance**

![Proceed without a key pair dialog](images/aws-ec2-launch-no-keypair.png)

7. Wait for the instance to reach **Running** status

![EC2 instance in Running state](images/aws-ec2-instance-running.png)

### Step 3: Get Agent Installation URL from FortiCNAPP

1. Log into FortiCNAPP console at <a href="https://partner-demo.lacework.net/" target="_blank">https://partner-demo.lacework.net/</a>
2. Ensure tenant is set to **FORTINETAPACDEMO**
3. Navigate to **Settings** > **Configuration** > **Agent tokens**
4. Find the **AWS Lab - Linux** agent token in the list
5. Click the **Actions** ellipsis (three dots) for the token
6. Select **Install**
7. In the installation panel, expand **Lacework Script (recommended)**
8. Click **Copy URL** to copy the installation script URL
9. Keep this URL ready - you'll use it in the next step

![Agent tokens page showing Install panel with Copy URL button](images/forticnapp-agent-install-url.png)

### Step 4: Connect to Linux EC2 Instance

1. In AWS Console, navigate to **EC2** service

![EC2 dashboard showing 1 running instance](images/aws-ec2-find-running-instance.png)

2. Click on **Instances** in the left navigation
3. Select the Linux EC2 instance you just created
4. Click **Connect**
5. Select **EC2 Instance Connect** tab
![EC2 Instance Connect page with Connect button](images/aws-ec2-instance-connect.png)

6. Click **Connect** (this will open a browser-based terminal - no key pair needed)
7. Once connected, verify system requirements:
   - Check available memory: `free -h`
   - Verify network connectivity: `ping -c 3 8.8.8.8`
   - Confirm sudo access: `sudo whoami`

### Step 5: Install Agent

In the EC2 Instance Connect terminal, run the following commands:

1. Download the installation script using the URL you copied in Step 3:
```bash
wget <paste-the-copied-url-here>
```

2. Make the script executable:
```bash
chmod +x install.sh
```

3. Execute the installation script:
```bash
sudo ./install.sh
```

The script will automatically install and configure the FortiCNAPP agent (datacollector) with the correct account and token.

### Step 6: Verify Agent Installation

1. Check the agent status using the datacollector binary:
```bash
sudo /var/lib/lacework/datacollector -status
```

This will return JSON output showing the agent status (e.g., `{"Version":2,"Datacollector":{"Status":"ACTIVE",...}}`). A status of "ACTIVE" indicates the agent is running and connected.

2. Check for agent logs:
```bash
ls -la /var/log/lacework/
```

3. Tail the agent log to see real-time activity:
```bash
sudo tail -f /var/log/lacework/datacollector.log
```
Press `Ctrl+C` to stop tailing the log.

### Step 7: Verify Agent in FortiCNAPP via CLI

Once the agent checks in (up to 1 hour), you can verify it appears in FortiCNAPP.

In the console, go to **Inventory** and look for the host by its instance ID.

If you took the optional [Lab 7](../lab-07/README.md) and have the Lacework CLI configured in CloudShell, you can also check from the command line:

```bash
lacework agent list
```

Look for your Linux instance hostname in the output. If you don't see it yet, the agent hasn't completed its first check-in - try again later.

**Note:** The local `datacollector -status` check (Step 6) confirms the agent is running on the instance. The `lacework agent list` command confirms FortiCNAPP has received the agent's check-in.

## What did we do here?

We installed the FortiCNAPP agent (datacollector) on a Linux EC2 instance. The agent monitors the host - processes, network connections, file changes, user activity - and sends that data to FortiCNAPP every hour to build a behavioural baseline.

This is the agent-based approach to workload security. Unlike the agentless scanning from Lab 3 (which takes periodic snapshots), the agent collects data continuously and reports hourly. It's how FortiCNAPP detects anomalies like unexpected processes, suspicious network connections, or lateral movement.
