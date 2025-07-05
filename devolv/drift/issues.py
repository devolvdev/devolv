from github import Github
import time

def create_approval_issue(repo_full_name, token, policy_name,assignees=None):
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)

    title = f"Approval needed for IAM policy: {policy_name}"
    body = f"Please review and approve the sync for `{policy_name}`."

    issue = repo.create_issue(
        title=title,
        body=body,
        assignees=assignees or []
    )

    print(f"✅ Created issue #{issue.number} in {repo_full_name}: {issue.html_url}")
    return issue.number, issue.html_url

def wait_for_sync_choice(repo_full_name, issue_number, token):
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    while True:
        comments = issue.get_comments()
        for comment in comments:
            content = comment.body.strip().lower()
            if content in ["local->aws", "aws->local", "aws<->local" "skip"]:
                return content
        print("Waiting for approval comment...")
        time.sleep(30)  # Poll every 30 seconds
