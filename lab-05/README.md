# Lab 5: Install Windows Agent

## Objectives

Most enterprise environments run a mix of Linux and Windows. In this lab, we'll install the FortiCNAPP agent on a Windows EC2 instance. The process is different (RDP, PowerShell, MSI package), but the result is the same - continuous workload monitoring and anomaly detection for your Windows fleet.

## Prerequisites

- AWS account with EC2 launch permissions

## Lab Steps

### Step 1: Log into AWS Console

1. Navigate to <a href="https://aws.amazon.com/" target="_blank">https://aws.amazon.com/</a>
2. Click **Sign into console**
3. After logging in, change to your local region (e.g., **Asia Pacific (Singapore)**) using the region selector in the top right of the AWS Console

### Step 2: Create Windows EC2 Instance

1. Navigate to **EC2** service in AWS Console

![EC2 dashboard with Launch Instance button](images/aws-ec2-pre-launch.png)

2. Click **Launch Instance**
3. Configure the instance:

![Launch an instance configuration page for Windows](images/aws-ec2-launch-details.png)

   - **Name**: Enter a name (e.g., `FortiCNAPP-Windows-Agent`)
   - **Application and OS Images**: Select **Microsoft Windows Server** (Windows Server 2022 or later)
   - **Instance type**: Select **c5.large**
   - **Key pair (login)**: 
     - Click **Create new key pair**
     - Enter a key pair name (e.g., `forticnapp-windows-key`)
     - Select **RSA** as the key pair type
     - Select **.pem** format
     - Click **Create key pair**
     - **Important**: Download the key pair file and save it securely - you'll need it to retrieve the Windows password
4. **Network settings**: leave the defaults as-is. The launch wizard will create a new security group (named `launch-wizard-N`) with an inbound rule for RDP from anywhere, which is what you need to connect.

   > Don't switch this to "Select existing security group" and pick the VPC's `default` SG. That one only allows traffic between resources sharing the same SG, so your RDP client won't be able to reach the instance.
![Instance type, key pair, and network settings](images/aws-ec2-launch-details-2.png)

5. **Configure storage**: Leave default (30 GB gp3)
6. Click **Launch Instance**
7. Wait for the instance to reach **Running** status

![Windows EC2 instance in Running state](images/aws-ec2-instance-running.png)

### Step 3: Get Windows Password and Connect

1. In AWS Console, navigate to **EC2** service
2. Click on **Instances** in the left navigation
3. Select the Windows EC2 instance you just created
4. Click **Connect**
5. Select **RDP Client** tab

![RDP client connection page with Get Password button](images/aws-ec2-rdp-connect.png)

6. Click **Get Password** (you may need to wait for a few minutes after the instance is running)
7. Upload your key pair file (.pem) to decrypt the password
8. Copy the **Administrator password**
9. Click **Download remote desktop file** to download the RDP connection file
10. Open the downloaded RDP file:
    - **Windows**: Double-click the file to open it in Remote Desktop Connection
    - **Mac**: Right-click and open with Windows app (previously known as Microsoft Remote Desktop app)
11. When prompted, enter the **Administrator password** you copied in step 8
12. **Note**: You may see a certificate warning when connecting - this is normal for EC2 instances. Click **Continue** to proceed.
13. If the credentials don't work:
    - Wait a few more minutes - Windows instances can take 3-5 minutes to fully initialize
    - Make sure you copied the password correctly (it's case-sensitive)
    - Try clicking **Get Password** again in the AWS Console to refresh
    - Ensure you're using **Administrator** (with capital A) as the username

14. If the RDP client can't connect at all (times out, "couldn't connect to the remote PC"):
    - Your local network is probably blocking outbound TCP 3389. Test with PowerShell: `Test-NetConnection -ComputerName <instance-public-ip> -Port 3389`. If `TcpTestSucceeded : False`, that's your problem.
    - **FortiSASE** (and most corporate VPN/secure-access agents) blocks RDP by default. Disconnect FortiSASE and try again.
    - Other usual offenders: corporate firewalls, hotel/conference WiFi, some ISPs. Easiest workaround is to tether to a phone hotspot.
14. Once connected, open **PowerShell as Administrator**:
    - Right-click the **Start** button and select **Windows PowerShell (Admin)** or **Terminal (Admin)**
    - Or search for "PowerShell" in the Start menu, right-click it, and select **Run as administrator**
    - Or press **Windows key + X** and select **Windows PowerShell (Admin)** or **Terminal (Admin)**

### Step 4: Get Agent Installation Information from FortiCNAPP

1. Log into FortiCNAPP console at <a href="https://partner-demo.lacework.net/" target="_blank">https://partner-demo.lacework.net/</a>
2. Ensure tenant is set to **FORTINETAPACDEMO**
3. Navigate to **Settings** > **Agent tokens**
4. Type `AWS Lab - Windows` in the search box. Take care to pick the Windows token, not the
   Linux one from Lab 4.
5. Click the **Actions** ellipsis (three dots) on that row, then **Install**

![Agent tokens filtered to AWS Lab - Windows, with the Actions menu open on Install](images/forticnapp-agent-token-actions.png)

6. The Windows panel offers different packages to the Linux one. You need two URLs from it:

![Install panel showing Lacework Powershell Script, MSI Package, ARM Template and Packer for AWS](images/forticnapp-agent-install-url.png)

   - **Lacework Powershell Script** is already expanded. Click **Copy URL** and keep it.
   - Expand **MSI Package** and click its **Copy URL**. This one becomes the `MSIURL`
     parameter later.

**Checkpoint:** you have two URLs, and you know which is which.
   - **Important**: Also copy the **Access Token** value shown in the installation panel (you'll need this for the AccessToken parameter)
8. Keep the PowerShell script URL, MSI URL, and Access Token ready - you'll use them in the next step

### Step 5: Install Agent

On the Windows EC2 instance (via RDP, in PowerShell as Administrator):

1. Download the installation package using the URL you copied in Step 4:
```powershell
Invoke-WebRequest -Uri "<paste-the-copied-url-here>" -OutFile "install.zip"
```

2. Extract the ZIP file:
```powershell
Expand-Archive -Path "install.zip" -DestinationPath "install" -Force
```

3. Navigate to the extracted folder and check the contents:
```powershell
cd install
ls
```

4. Navigate into the `signed-scripts` directory:
```powershell
cd signed-scripts
```

5. Execute the installation script with all required parameters:
   - Replace `<your-token>` with the Access Token you copied from FortiCNAPP
   - Replace `<msi-url>` with the MSI URL you copied from the MSI Package section
```powershell
.\Install-LWDataCollector.ps1 -AccessToken "<your-token>" -ServerURL "https://partner-demo.lacework.net" -MSIURL "<msi-url>"
```

The script will automatically install and configure the FortiCNAPP agent with the correct account and token.

### Step 6: Verify Agent Installation

1. Check the agent service status (the service is named `LWDataCollector`):
```powershell
Get-Service -Name LWDataCollector
```

2. Check the agent installation directory:
```powershell
ls C:\ProgramData\Lacework\
```

3. Check for agent logs:
```powershell
ls C:\ProgramData\Lacework\Logs\
```

### Step 7: Verify Agent in FortiCNAPP

Once the agent checks in (up to 1 hour), you can verify it appears in FortiCNAPP.

In the console, go to **Inventory** and look for the host by its instance ID.

If you took [Lab 6](../lab-06/README.md) and have the Lacework CLI configured in CloudShell, you can also check from the command line:

```bash
lacework agent list
```

Look for your Windows instance hostname in the output. If you don't see it yet, the agent hasn't completed its first check-in - try again later.

## What did we do here?

We installed the FortiCNAPP agent on a Windows EC2 instance - the same concept as Lab 4, but for Windows workloads. The agent runs as the LWDataCollector service and provides the same continuous monitoring: processes, network connections, file changes, and user activity.

The installation process is different (PowerShell script + MSI package instead of a bash script), but the result is the same - real-time workload visibility in FortiCNAPP. This matters because most enterprise environments run a mix of Linux and Windows, and you need coverage across both.
