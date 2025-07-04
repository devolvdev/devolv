import os
from github import Github

def _get_github_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "❌ GITHUB_TOKEN not set in environment. "
            "In your Action, ensure it's passed via input and exported: "
            "export GITHUB_TOKEN=${{ inputs.github-token }}"
        )
    return token

def _get_github_repo(repo_full_name: str):
    gh = Github(_get_github_token())
    return gh.get_repo(repo_full_name)

def create_github_issue(repo: str, title: str, body: str, assignees: list) -> int:
    """
    Create a GitHub issue using the GitHub API.
    """
    try:
        repo_obj = _get_github_repo(repo)
        issue = repo_obj.create_issue(title=title, body=body, assignees=assignees)
        print(f"✅ Created issue #{issue.number} in {repo}")
        return issue.number
    except Exception as e:
        print(f"❌ Failed to create issue in {repo}: {e}")
        raise

def create_github_pr(repo: str, head_branch: str, title: str, body: str, base: str = "main") -> int:
    """
    Create a GitHub pull request using the GitHub API.
    """
    try:
        repo_obj = _get_github_repo(repo)
        pr = repo_obj.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base
        )
        print(f"✅ Created PR #{pr.number} in {repo}")
        return pr.number
    except Exception as e:
        print(f"❌ Failed to create PR in {repo}: {e}")
        raise

def push_branch(branch_name: str):
    """
    Create, commit, and push a branch with local changes to GitHub.
    """
    try:
        os.system(f"git checkout -b {branch_name}")
        os.system("git add .")
        os.system("git commit -m 'Update policy via Devolv drift'")
        os.system(f"git push origin {branch_name}")
        print(f"✅ Pushed branch {branch_name} to origin")
    except Exception as e:
        print(f"❌ Failed to push branch {branch_name}: {e}")
        raise
