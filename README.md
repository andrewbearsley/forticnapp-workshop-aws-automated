# FortiCNAPP Workshop: AWS Integration (Automated Configuration)

Hands-on labs for integrating FortiCNAPP with AWS using **automated configuration**.

This is the fast path. FortiCNAPP builds the whole integration for you from temporary
credentials, so you onboard an AWS account in one wizard instead of running two
CloudFormation stacks by hand.

> Looking for the CloudFormation and Terraform version? See the
> <a href="https://github.com/andrewbearsley/forticnapp-workshop-aws-integration" target="_blank">original AWS integration workshop</a>.
> The two workshops reach the same end state. This one takes fewer steps.

## Why automated configuration

You give FortiCNAPP short-lived AWS credentials. FortiCNAPP then:

1. Validates your permissions and finds resources it can reuse.
2. Generates a Terraform plan for your account.
3. Applies the plan to create the IAM roles, buckets, keys and queues it needs.
4. Registers the integration and validates it.
5. Discards the temporary credentials and runs on the cross-account role.

Two things matter for a workshop. If any integration type fails, FortiCNAPP rolls back
**all** of them, so nobody ends up half onboarded. And every resource it creates carries
the `lacework_tag` and `lacework_integration` tags, so cleanup is a tag search.

Source: <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/123850/automated-configuration" target="_blank">FortiCNAPP Administration Guide, "Automated configuration"</a>

## Prerequisites

- AWS account with administrator access (a disposable workshop account)
- FortiCNAPP console access, tenant **FORTINETAPACDEMO**
- A browser. The core path needs no CLI and no local tooling.

## Core path

Work through these in order. Allow about three hours.

- [Lab 1: Hands-on Cloud Security with FortiCNAPP](lab-01/README.md)
- [Lab 2: Get Temporary AWS Credentials](lab-02/README.md)
- [Lab 3: Onboard AWS with Automated Configuration](lab-03/README.md)
- [Lab 4: Install Linux Agent](lab-04/README.md)
- [Lab 5: Install Windows Agent](lab-05/README.md)
- [Lab 6: Install the Lacework CLI](lab-06/README.md)
- [Lab 7: Code Security for Infrastructure as Code (IaC)](lab-07/README.md)
- [Lab 8: Code Security for Applications (SCA)](lab-08/README.md)
- [Lab 9: Clean Up Workshop Resources](lab-09/README.md)

Labs 1 to 5 cover the cloud side: onboard the account, then put agents on workloads. Lab 6
installs the CLI, which Labs 7 and 8 need. Those two shift left into the code, scanning
Terraform for misconfiguration and application dependencies for vulnerabilities.

Everything runs in a browser and AWS CloudShell. Nothing is installed on your laptop.

## Optional: advanced track

Take these when a customer wants onboarding through a pipeline rather than a wizard.

- [Lab 10: Install Terraform](lab-10/README.md)
- [Lab 11: Install Integrations via Terraform](lab-11/README.md)
- [Lab 12: Scripted Cleanup of All Workshop Resources](lab-12/README.md)

## Which path do I run?

| Audience | Path |
|---|---|
| Partner enablement, first look, short session | Labs 1 to 5, then Lab 9 to clean up |
| Developer or DevSecOps audience | Full core path. Labs 7 and 8 are the draw. |
| Customer running onboarding through a pipeline | Core path, then Labs 10 and 11 |

## Resources

- <a href="https://docs.fortinet.com/product/forticnapp" target="_blank">FortiCNAPP Documentation</a>
- <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/123850/automated-configuration" target="_blank">Automated configuration</a>
- <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/331296/obtaining-temporary-cloud-account-credentials" target="_blank">Obtaining temporary cloud account credentials</a>

## Contributing

For questions or improvements, open an issue or submit a pull request.
