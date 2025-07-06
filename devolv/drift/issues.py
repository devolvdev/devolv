from github import Github
import time

def create_approval_issue(repo_full_name, token, policy_name, assignees=None, approval_anyway=False):
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)

    approver_list = ", ".join([f"@{a}" for a in assignees]) if assignees else "anyone"

    if approval_anyway:
        title = f"Approval needed (forced) for IAM policy: {policy_name}"
        body = (
            f"Approval is required even though no drift was detected for `{policy_name}`.\n\n"
            f"✅ **Allowed approvers:** {approver_list}\n\n"
            "**Reply with one of the following commands to proceed:**\n"
            "- `approve` → Approve current policy state; apply local additions\n"
            "- `reject` → Reject; no changes applied"
        )
    else:
        title = f"Approval needed for IAM policy: {policy_name}"
        body = (
            f"Please review and approve the sync for `{policy_name}`.\n\n"
            f"✅ **Allowed approvers:** {approver_list}\n\n"
            "**Reply with one of the following commands to proceed:**\n"
            "- `local->aws` → Apply local policy changes to AWS\n"
            "- `aws->local` → Update local policy file from AWS\n"
            "- `aws<->local` → Sync both ways (superset, update AWS + local)\n"
            "- `skip` → Skip this sync"
        )

    issue = repo.create_issue(
        title=title,
        body=body,
        assignees=assignees or []
    )

    return issue.number, issue.html_url



def wait_for_sync_choice(repo_full_name, issue_number, token, allowed_approvers=None, approval_anyway=False):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    allowed_approvers = [a.lower() for a in (allowed_approvers or [])]

    while True:
        comments = issue.get_comments()
        for comment in comments:
            commenter = comment.user.login.lower()
            content = comment.body.strip().lower()

            if allowed_approvers and commenter not in allowed_approvers:
                print(f"Ignoring comment from unauthorized user: {commenter}")
                continue

            if approval_anyway:
                if content in ["approve", "reject"]:
                    return content
            else:
                if content in ["local->aws", "aws->local", "aws<->local", "skip"]:
                    return content

        print("Waiting for approval comment...")
        time.sleep(30)


