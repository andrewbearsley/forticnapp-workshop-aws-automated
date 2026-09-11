# Lab 4: Install Linux Agent

## Objectives

Lab 3 turned on agentless scanning. That reads your account from the outside: it takes a
snapshot of each disk, finds the packages and the secrets, and tells you what is
vulnerable. It never touches the running machine.

This lab installs the **agent**, which sits inside the machine and watches it work.

| | Agentless, Lab 3 | Agent, this lab |
|---|---|---|
| Where it runs | Outside, on a copy of the disk | On the host itself |
| What it sees | What is installed | What is actually happening: processes, connections, file changes, logins |
| How often | Periodic snapshot | Continuously, reporting hourly |
| To install | Nothing | One script |

Neither replaces the other. Agentless tells you a host **could** be exploited. The agent
tells you something **is** behaving strangely on it, which is what a baseline and an
anomaly alert are built from.

You will launch a Linux EC2 instance, install the agent on it, and confirm both ends agree
it is running.

## Prerequisites

- Completed [Lab 3](../lab-03/README.md)
- AWS account with permission to launch EC2 instances
- FortiCNAPP console access, tenant **FORTINETAPACDEMO**

## Lab Steps

### Step 1: Create Linux EC2 Instance

1. Open the **EC2** service. Check the region selector reads **Asia Pacific (Singapore)**
   before you do anything else.

![EC2 dashboard, with the region selector and Launch instance button highlighted](images/aws-ec2-pre-launch.png)

2. Click **Launch instance**.

3. **Name**: `FortiCNAPP-Linux-Agent`

4. **Application and OS Images**: leave **Amazon Linux 2023** selected. It is the default,
   and the agent installer does not care which distribution you pick.

![Launch an instance page with the name entered and Amazon Linux 2023 selected](images/aws-ec2-launch-details.png)

5. **Instance type**: leave **t3.micro**.

6. **Key pair (login)**: open the dropdown and choose
   **Proceed without a key pair (Not recommended)**.

   You will connect through EC2 Instance Connect in the browser, which issues its own
   temporary key. There is nothing for you to download or keep.

![Key pair dropdown open on Proceed without a key pair](images/aws-ec2-launch-no-keypair.png)

![Instance type and key pair set, with Network settings below](images/aws-ec2-launch-details-2.png)

7. **Network settings**: leave them alone. The wizard creates a security group called
   `launch-wizard-1` allowing SSH from anywhere, which is what Instance Connect needs.

![Network settings with Create security group selected](images/aws-ec2-network-settings.png)

> [!WARNING]
> **This is the step that breaks the lab.** Do not switch to **Select existing security
> group** and pick the VPC's `default` group. That one only allows traffic between
> resources that share it, so Instance Connect cannot reach your instance and you get a
> timeout with no useful error.

8. **Configure storage**: leave the default, 8 GiB gp3.

9. Click **Launch instance**, then **View all instances**.

10. Wait for **Instance state** to read **Running**. Allow about a minute.

![Instance list showing the new instance in the Running state](images/aws-ec2-instance-running.png)

**Checkpoint:** one instance, state **Running**, and it has a public IPv4 address.

### Step 2: Get the Agent Install URL from FortiCNAPP

1. Log into FortiCNAPP console at <a href="https://partner-demo.lacework.net/" target="_blank">https://partner-demo.lacework.net/</a>
2. Ensure tenant is set to **FORTINETAPACDEMO**
3. Navigate to **Settings** > **Configuration** > **Agent tokens**
4. Type `AWS Lab - Linux` in the search box. There are dozens of tokens on this tenant, so
   searching beats scrolling.
5. Click the **Actions** ellipsis (three dots) on that row, then **Install**

![Agent tokens filtered to AWS Lab - Linux, with the Actions menu open on Install](images/forticnapp-agent-token-actions.png)

6. **Lacework Script** is already expanded. Click **Copy URL**.

   Copy the URL, not the script. The install command in the next step fetches it.

![Install panel with the Lacework Script section expanded and Copy URL highlighted](images/forticnapp-agent-install-url.png)

**Checkpoint:** you have a URL on your clipboard that starts with `https://`.

### Step 3: Connect to the Instance

1. Go to **EC2** > **Instances**.
2. Tick the checkbox next to `FortiCNAPP-Linux-Agent`.
3. Click **Connect** at the top of the page.
4. Stay on the **In web browser** tab and leave **EC2 Instance Connect** selected. It is the
   first of the four cards and it is already chosen.

![Connect to Linux instance page, with EC2 Instance Connect selected](images/aws-ec2-instance-connect.png)

5. Leave **Username** as `ec2-user`, then click **Connect**.

   A terminal opens in the browser. No key pair, no SSH client, nothing to install.

6. Confirm the shell can do what the installer needs:

```bash
sudo whoami        # must print: root
ping -c 3 8.8.8.8  # the agent needs to reach the internet
```

**Checkpoint:** `sudo whoami` prints `root` and the pings come back.

### Step 4: Install the Agent

In the EC2 Instance Connect terminal, run the following commands:

Paste the URL from Step 2 where shown. Keep the `-O install.sh`, which names the
downloaded file for you rather than trusting whatever the URL ends in.

```bash
wget -O install.sh "<paste-the-copied-url-here>"
chmod +x install.sh
sudo ./install.sh
```

The URL carries your agent token, so the script installs and registers the agent in one
go. There is nothing to configure afterwards.

> **Pasting into the browser terminal.** Use **Ctrl+V** (**Cmd+V** on a Mac). If the paste
> arrives empty, your clipboard did not survive the tab switch. Go back to Step 2 and click
> **Copy URL** again.

### Step 5: Verify on the Host

Ask the agent how it is doing:

```bash
sudo /var/lib/lacework/datacollector -status
```

It answers in JSON. The field that matters is `Status`:

```json
{"Version":2,"Datacollector":{"Status":"ACTIVE", ...}}
```

`ACTIVE` means it is running and talking to FortiCNAPP.

To watch it work:

```bash
ls -la /var/log/lacework/
sudo tail -f /var/log/lacework/datacollector.log
```

`Ctrl+C` stops the tail.

**Checkpoint:** `Status` reads `ACTIVE`.

### Step 6: Verify in FortiCNAPP

> **The agent reports hourly, so it will not appear straight away.** That is expected, not a
> failure. Carry on to Lab 5 and come back to this step later in the session.

In the console, go to **Inventory** and look for the host by its instance ID.

Once you have done [Lab 6](../lab-06/README.md) you can ask the same question from
CloudShell instead:

```bash
lacework agent list
```

Look for your instance hostname. Nothing there yet means the first check-in has not landed.

> **The two checks answer different questions.** `datacollector -status` on the host says
> the agent is running. `lacework agent list` says FortiCNAPP has heard from it. You can
> have the first without the second. That gap is almost always a security group or a route,
> not the agent.

## What did we do here?

The host now reports what it is doing, not just what is installed on it.

That is the whole difference. Agentless found the vulnerable package. The agent is what
notices the package being exploited: a process that has never run before, a connection to
somewhere this host has never talked to, a login at the wrong hour. You cannot alert on
behaviour you are not watching.

The Windows install differs enough to be worth doing once.

---

Next: [Lab 5: Install Windows Agent](../lab-05/README.md).
