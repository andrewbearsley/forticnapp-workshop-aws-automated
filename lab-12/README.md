# Lab 12: Clean Up All Workshop Resources

This lab provides a cleanup script that removes every workshop resource, on both the FortiCNAPP side and the AWS side.

> **Warning**: this script assumes a disposable workshop AWS account. It sweeps every enabled region and removes all EC2 instances, key pairs and non-default security groups in the account, not only the ones the workshop created, along with every FortiCNAPP integration pointing at that AWS account. Do not run it in an account that hosts anything you want to keep.

## Why both sides need cleaning

Labs 2 and 3 create the integration record in the FortiCNAPP console **first**, then launch CloudFormation to build the AWS side. CloudFormation never owns that record.

That means deleting the CloudFormation stack removes the S3 bucket, the cross-account IAM role and the ECS scanner, but leaves the FortiCNAPP integration in place. It keeps polling on schedule, finds a bucket that no longer exists, and reports:

```
Data loading error: Unable to access scan results within storage bucket
```

Lab 9 does not have this problem, because Terraform owns its integrations in state and `terraform destroy` removes both sides.

Deleting the stack is not enough. The FortiCNAPP integration has to be deleted through FortiCNAPP, which is what Step 2 of the script does.

## Instructions

1. Open AWS CloudShell in your browser.

2. Copy the entire contents of [cloudshell_cleanup.sh](cloudshell_cleanup.sh) using the copy button.

![Copy script to clipboard from GitHub](images/github-copy-script-to-clipboard.png)

3. Paste the script into the CloudShell terminal and press Enter.

4. Wait for the script to complete. It may take several minutes, especially when deleting CloudFormation stacks and S3 buckets. Sweeping every region adds time even when most regions are empty.

5. **Verify in the FortiCNAPP console.** Navigate to **Settings** > **Integrations** > **Cloud accounts** and confirm your AWS account is no longer listed. If anything remains, select it and click **Delete**.

## What the script does, in order

The order matters. The FortiCNAPP integrations are removed while the Lacework CLI and its credentials still exist, and the local CloudShell artifacts are only cleaned up at the very end.

| Step | Action |
|---|---|
| 1 | `terraform destroy` for the Lab 9 deployment, which removes its own integrations and AWS resources |
| 2 | Delete any remaining FortiCNAPP cloud integrations for this AWS account (Labs 2 and 3) |
| 3 | Per region: terminate EC2 instances, delete CloudFormation stacks, delete CloudTrail trails, delete key pairs, delete non-default security groups |
| 4 | Empty and delete Lacework-related S3 buckets, resolving each bucket's own region |
| 5 | Remove CloudShell artifacts: Terraform and Lacework binaries, cloned repos, config files, `.bashrc` edits |

## Notes

- The script runs non-interactively and disables the AWS CLI pager to prevent prompts.
- It continues past individual failures rather than aborting, so one stuck resource does not strand the rest of the cleanup.
- CloudFormation stack deletions wait for completion before proceeding.
- Stack matching is case-insensitive, handles names containing spaces, and deletes every matching root stack rather than just one. Lab 3 lets you name the stack freely, and a redeploy after a failed attempt leaves two.
- Nested stacks are skipped, since deleting the root stack removes them.
- S3 bucket deletion handles versioned objects and delete markers.
- The default security group is preserved.

## Troubleshooting

**An integration is still listed in FortiCNAPP after the script runs.**
The script needs the Lacework CLI (installed in Labs 4 and 8) and valid credentials to deregister integrations. If you skipped those labs, or the CLI could not authenticate, delete the integration manually: **Settings** > **Integrations** > **Cloud accounts** > select > **Delete**.

**A CloudFormation stack failed to delete.**
Usually a non-empty S3 bucket blocking it. The script retries while retaining the blocked resource, then Step 4 sweeps the bucket. Re-run the script once to clear the remainder.

**A security group would not delete.**
It is still attached to an instance that has not finished terminating. Wait a minute and re-run the script.

**Other failures.**
Check AWS permissions for the CloudShell user, and verify the resources exist before cleanup. Some resources need manual deletion if dependencies prevent automated removal.
