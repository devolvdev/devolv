import os
import subprocess
import typer
from github import Github

def _get_github_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "❌ GITHUB_TOKEN not set in environment.\n"
            "💡 Resolution: Set the token in your environment or CI pipeline.\n"
            "👉 Example (local): export GITHUB_TOKEN=ghp_yourtoken\n"
            "👉 Example (GitHub Action): pass via input and export:\n"
            "export GITHUB_TOKEN=${{ inputs.github-token }}"
        )
    return token

def _get_github_repo(repo_full_name: str):
    gh = Github(_get_github_token())
    return gh.get_repo(repo_full_name)

def create_github_issue(repo: str, title: str, body: str, assignees: list) -> tuple:
    try:
        repo_obj = _get_github_repo(repo)
        issue = repo_obj.create_issue(title=title, body=body, assignees=assignees)
        print(f"✅ Created issue #{issue.number} in {repo}: {issue.html_url}")
        return issue.number, issue.html_url
    except Exception as e:
        print(f"❌ Failed to create issue in {repo}: {e}")
        print("💡 Resolution: Check if your GitHub token has `repo` scope and the assignees exist in the repo.")
        return None, None

def create_github_pr(repo: str, head_branch: str, title: str, body: str, base: str = "main", issue_num: int = None) -> tuple:
    try:
        repo_obj = _get_github_repo(repo)
        pr = repo_obj.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base
        )
        print(f"✅ Created PR #{pr.number} in {repo}: {pr.html_url}")

        if issue_num:
            issue = repo_obj.get_issue(number=issue_num)
            issue.create_comment(f"A PR has been created for this sync: {pr.html_url}")

        return pr.number, pr.html_url

    except Exception as e:
        print(f"❌ Failed to create PR: {e}")
        print("💡 Resolution: Ensure the GitHub token has permission to create PRs. Check branch protection rules and required approvals that may block automation PRs.")
        print(f"👉 Suggested: Manually create a PR from `{head_branch}` to `{base}` in `{repo}`.")
        return None, None

def push_branch(branch_name: str):
    try:
        subprocess.run(["git", "checkout", "-B", branch_name], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions@users.noreply.github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Update policy: {branch_name}"], check=True)

        try:
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
        except subprocess.CalledProcessError:
            typer.echo("⚠️ Initial push failed. Attempting rebase + push...")
            subprocess.run(["git", "pull", "--rebase", "origin", branch_name], check=True)
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)

        typer.echo(f"✅ Pushed branch {branch_name} to origin.")

    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Git push failed: {e}")
        typer.echo("💡 Resolution: Check if your auth token is valid, branch exists remotely, or branch protection prevents push. Try manual push:")
        typer.echo(f"👉 git push -f origin {branch_name}")
