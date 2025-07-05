import os
import subprocess
from github import Github
import typer

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

def create_github_issue(repo: str, title: str, body: str, assignees: list) -> tuple:
    """
    Create a GitHub issue and return (number, url)
    """
    try:
        repo_obj = _get_github_repo(repo)
        issue = repo_obj.create_issue(title=title, body=body, assignees=assignees)
        print(f"✅ Created issue #{issue.number} in {repo}: {issue.html_url}")
        return issue.number, issue.html_url
    except Exception as e:
        print(f"❌ Failed to create issue in {repo}: {e}")
        raise

def create_github_pr(repo: str, head_branch: str, title: str, body: str, base: str = "main", issue_num: int = None) -> tuple:
    """
    Create a GitHub PR. If issue_num is provided, comment on the issue.
    Return (PR number, PR URL).
    """
    from github import Github

    try:
        repo_obj = _get_github_repo(repo)
        pr = repo_obj.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base
        )
        #print(f"✅ Created PR #{pr.number} in {repo}: {pr.html_url}")

        if issue_num:
            issue = repo_obj.get_issue(number=issue_num)
            issue.create_comment(f"A PR has been created for this sync: {pr.html_url}")
        
        return pr.number, pr.html_url

    except Exception as e:
        print(f"❌ Failed to create PR: {e}")
        raise

def push_branch(branch_name: str):
    import subprocess
    import typer

    try:
        # Create or switch to branch safely
        subprocess.run(["git", "checkout", "-B", branch_name], check=True)

        # Ensure Git identity is set
        subprocess.run(["git", "config", "user.email", "github-actions@users.noreply.github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)

        # Add, commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Update policy: {branch_name}"], check=True)

        # Try pushing
        try:
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
        except subprocess.CalledProcessError:
            typer.echo("⚠️ Initial push failed. Attempting rebase + push...")
            subprocess.run(["git", "pull", "--rebase", "origin", branch_name], check=True)
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)

        typer.echo(f"✅ Pushed branch {branch_name} to origin.")

    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Git command failed: {e}")
        raise typer.Exit(1)


