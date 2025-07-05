import json
import boto3
import typer
import os
import subprocess

from devolv.drift.aws_fetcher import get_aws_policy_document, merge_policy_documents, build_superset_policy
from devolv.drift.issues import create_approval_issue, wait_for_sync_choice
from devolv.drift.github_approvals import create_github_pr
from devolv.drift.report import detect_and_print_drift
from github import Github  # Needed for auto-close

app = typer.Typer()

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
            typer.echo("⚠️ Push failed. Trying to pull + re-push...")
            subprocess.run(["git", "pull", "--rebase", "origin", branch_name], check=True)
            subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)

        typer.echo(f"✅ Pushed branch {branch_name} to origin.")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Git command failed: {e}")
        raise typer.Exit(1)

@app.command()
def drift(
    policy_name: str = typer.Option(..., "--policy-name", help="Name of the IAM policy"),
    policy_file: str = typer.Option(..., "--file", help="Path to local policy file"),
    account_id: str = typer.Option(None, "--account-id", help="AWS Account ID (optional, auto-detected if not provided)"),
    approvers: str = typer.Option("", help="Comma-separated GitHub usernames for approval (optional)"),
    approval_anyway: bool = typer.Option(False, "--approval-anyway", help="Request approval even if no drift"),
    repo_full_name: str = typer.Option(None, "--repo", help="GitHub repo full name (e.g., org/repo)")
):
    if not account_id:
        account_id = boto3.client("sts").get_caller_identity()["Account"]
    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

    try:
        with open(policy_file) as f:
            local_doc = json.load(f)
    except FileNotFoundError:
        typer.echo(f"❌ Local policy file {policy_file} not found.")
        raise typer.Exit(1)

    aws_doc = get_aws_policy_document(policy_arn)
    drift = detect_and_print_drift(local_doc, aws_doc)

    if not drift and not approval_anyway:
        typer.echo("✅ No drift detected. Use --approval-anyway to force approval.")
        raise typer.Exit()

    repo_full_name = repo_full_name or os.getenv("GITHUB_REPOSITORY")
    if not repo_full_name:
        typer.echo("❌ GitHub repo not specified. Use --repo or set GITHUB_REPOSITORY.")
        raise typer.Exit(1)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        typer.echo("❌ GITHUB_TOKEN not set in environment.")
        raise typer.Exit(1)

    assignees = [a.strip() for a in approvers.split(",") if a.strip()]
    issue_num, _ = create_approval_issue(repo_full_name, token, policy_name, assignees=assignees)
    typer.echo(f"✅ Created issue #{issue_num} in {repo_full_name}: https://github.com/{repo_full_name}/issues/{issue_num}")

    choice = wait_for_sync_choice(repo_full_name, issue_num, token)
    iam = boto3.client("iam")

    if choice == "local->aws":
        merged_doc = merge_policy_documents(local_doc, aws_doc)
        _update_aws_policy(iam, policy_arn, merged_doc)
        typer.echo(f"✅ AWS policy {policy_arn} updated with local changes (append-only).")

    elif choice == "aws->local":
        _update_local_and_create_pr(aws_doc, policy_file, repo_full_name, policy_name, issue_num, token, "from AWS policy")

    elif choice == "aws<->local":
        superset_doc = build_superset_policy(local_doc, aws_doc)
        _update_aws_policy(iam, policy_arn, superset_doc)
        typer.echo(f"✅ AWS policy {policy_arn} updated with superset of local + AWS.")
        _update_local_and_create_pr(superset_doc, policy_file, repo_full_name, policy_name, issue_num, token, "with superset of local + AWS")

    else:
        typer.echo("⏭ No synchronization performed (skip).")

def _update_aws_policy(iam, policy_arn, policy_doc):
    versions = iam.list_policy_versions(PolicyArn=policy_arn)['Versions']
    if len(versions) >= 5:
        oldest = sorted((v for v in versions if not v['IsDefaultVersion']), key=lambda v: v['CreateDate'])[0]
        iam.delete_policy_version(PolicyArn=policy_arn, VersionId=oldest['VersionId'])
    iam.create_policy_version(
        PolicyArn=policy_arn,
        PolicyDocument=json.dumps(policy_doc),
        SetAsDefault=True
    )

def _update_local_and_create_pr(doc, policy_file, repo_full_name, policy_name, issue_num, token, description=""):
    new_content = json.dumps(doc, indent=2)
    with open(policy_file, "w") as f:
        f.write(new_content)

    branch = (
        f"{description.replace(' ', '-').replace('+', 'plus').replace('/', '-')}-policy-{policy_name}"
        .strip("-")
        .lower()
    )
    push_branch(branch)

    pr_title = f"Update {policy_file} {description}".strip()
    pr_body = f"This PR updates `{policy_file}` {description}.\n\nLinked to issue #{issue_num}.".strip()
    pr_num, pr_url = create_github_pr(repo_full_name, branch, pr_title, pr_body, issue_num=issue_num)

    typer.echo(f"✅ Created PR #{pr_num}: {pr_url}")
    typer.echo(f"💬 Commented on and closed issue #{issue_num}")

    # Auto-close issue
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_num)
    issue.create_comment(f"✅ PR created and linked: {pr_url}. Closing issue.")
    issue.edit(state="closed")
