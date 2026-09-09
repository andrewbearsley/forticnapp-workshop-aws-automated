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

Work through these in order. Allow about 90 minutes.

- [Lab 1: Hands-on Cloud Security with FortiCNAPP](lab-01/README.md)
- [Lab 2: Get Temporary AWS Credentials](lab-02/README.md)
- [Lab 3: Onboard AWS with Automated Configuration](lab-03/README.md)
- [Lab 4: Install Linux Agent](lab-04/README.md)
- [Lab 5: Install Windows Agent](lab-05/README.md)
- [Lab 6: Clean Up Workshop Resources](lab-06/README.md)

## Optional: advanced track

Take these when you want the infrastructure as code path, or when a customer runs
onboarding through a pipeline. They need AWS CloudShell and the Lacework CLI.

- [Lab 7: Install Lacework CLI and Trigger Inventory Scan](lab-07/README.md)
- [Lab 8: Install Lacework CLI and Terraform](lab-08/README.md)
- [Lab 9: Install Integrations via Terraform](lab-09/README.md)
- [Lab 10: Code Security for Infrastructure as Code (IaC)](lab-10/README.md)
- [Lab 11: Code Security for Applications (SCA)](lab-11/README.md)
- [Lab 12: Scripted Cleanup of All Workshop Resources](lab-12/README.md)

## Which path do I run?

| Audience | Path |
|---|---|
| Partner enablement, first look, short session | Core path only |
| Customer running onboarding through a pipeline | Core path, then Labs 8 and 9 |
| Developer or DevSecOps audience | Core path, then Labs 10 and 11 |

## Resources

- <a href="https://docs.fortinet.com/product/forticnapp" target="_blank">FortiCNAPP Documentation</a>
- <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/123850/automated-configuration" target="_blank">Automated configuration</a>
- <a href="https://docs.fortinet.com/document/forticnapp/latest/administration-guide/331296/obtaining-temporary-cloud-account-credentials" target="_blank">Obtaining temporary cloud account credentials</a>

## Contributing

For questions or improvements, open an issue or submit a pull request.
