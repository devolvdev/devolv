from github import Github
import time

def create_approval_issue(repo_full_name, token, policy_name):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    body = (
        f"Drift detected for policy `{policy_name}`.\n\n"
        "Please comment:\n"
        "- `local->aws` to sync local changes to AWS\n"
        "- `aws->local` to sync AWS changes to local file\n"
        "- `skip` to do nothing"
    )
    issue = repo.create_issue(
        title=f"Devolv Drift Sync Approval Needed: {policy_name}",
        body=body
    )
    return issue.number

def wait_for_sync_choice(repo_full_name, issue_number, token):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    while True:
        comments = issue.get_comments()
        for comment in comments:
            content = comment.body.strip().lower()
            if content in ["local->aws", "aws->local", "skip"]:
                return content
        print("Waiting for approval comment...")
        time.sleep(30)  # Poll every 30 seconds
