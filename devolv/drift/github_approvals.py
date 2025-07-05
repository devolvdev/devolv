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

def create_github_issue(repo: str, policy_name: str, assignees: list, drift_detected: bool = True) -> tuple:
    """
    Create a GitHub issue with dynamic body based on drift_detected.
    Returns (issue number, issue URL)
    """
    try:
        repo_obj = _get_github_repo(repo)
        approver_list = ", ".join([f"@{a}" for a in assignees]) if assignees else "anyone"

        title = f"Approval needed for IAM policy: {policy_name}"
        if drift_detected:
            body = (
                f"Please review and approve the sync for `{policy_name}`.\n\n"
                f"✅ **Allowed approvers:** {approver_list}\n\n"
                "**Reply with one of the following commands to proceed:**\n"
                "- `local->aws` → Apply local policy changes to AWS\n"
                "- `aws->local` → Update local policy file from AWS\n"
                "- `aws<->local` → Sync both ways (superset, update AWS + local)\n"
                "- `skip` → Skip this sync"
            )
        else:
            body = (
                f"Please review and approve the current state for `{policy_name}` (✅ No drift detected).\n\n"
                f"✅ **Allowed approvers:** {approver_list}\n\n"
                "**Reply with one of the following commands to proceed:**\n"
                "- `accept` → Approve the current state, no further action\n"
                "- `reject` → Reject the current state (no changes will be made)"
            )

        issue = repo_obj.create_issue(title=title, body=body, assignees=assignees)
        print(f"✅ Created issue #{issue.number} in {repo}: {issue.html_url}")
        return issue.number, issue.html_url

    except Exception as e:
        print(f"❌ Failed to create issue in {repo}: {e}")
        raise

def create_github_pr(repo: str, head_branch: str, title: str, body: str, base: str = "main", issue_num: int = None) -> tuple:
    """
    Create a GitHub PR. Optionally comments on linked issue.
    Returns (PR number, PR URL)
    """
    try:
        repo_obj = _get_github_repo(repo)
        pr = repo_obj.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base
        )

        if issue_num:
            issue = repo_obj.get_issue(number=issue_num)
            issue.create_comment(f"✅ PR created and linked: {pr.html_url}")

        print(f"✅ Created PR #{pr.number} in {repo}: {pr.html_url}")
        return pr.number, pr.html_url

    except Exception as e:
        print(f"❌ Failed to create PR in {repo}: {e}")
        raise

def push_branch(branch_name: str):
    """
    Create, commit to, and push a git branch, rebasing if needed.
    """
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
            try:
                subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
            except subprocess.CalledProcessError:
                # Ignore error on second push
                pass

        typer.echo(f"✅ Pushed branch {branch_name} to origin.")

    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Git command failed: {e}")
        raise typer.Exit(1)
