import json
import os
import subprocess
import boto3
import typer
from github import Github
from datetime import datetime

from devolv.drift.aws_fetcher import (
    get_aws_policy_document,
    merge_policy_documents,
    build_superset_policy,
)
from devolv.drift.issues import create_approval_issue, wait_for_sync_choice
from devolv.drift.github_approvals import create_github_pr
from devolv.drift.report import print_drift_diff, normalize_statement

app = typer.Typer()

def push_branch(branch_name: str):
    try:
        subprocess.run(["git", "checkout", "-B", branch_name], check=True)
        subprocess.run(["git", "config", "user.email", "github-actions@users.noreply.github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Update policy: {branch_name}"], check=True)
        subprocess.run(["git", "push", "--set-upstream", "origin", branch_name], check=True)
        typer.echo(f"✅ Pushed branch {branch_name} to origin.")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Git command failed: {e}")
        raise typer.Exit(1)

def close_issue(repo_full_name, token, issue_num, comment):
    gh = Github(token)
    repo = gh.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_num)
    issue.create_comment(comment)
    issue.edit(state="closed")

def detect_drift(local_doc, aws_doc) -> bool:
    local_statements = {
        json.dumps(normalize_statement(s), sort_keys=True)
        for s in local_doc.get("Statement", [])
    }
    aws_statements = {
        json.dumps(normalize_statement(s), sort_keys=True)
        for s in aws_doc.get("Statement", [])
    }
    missing_in_local = aws_statements - local_statements
    if missing_in_local:
        typer.echo("❌ Drift detected: Local is missing permissions present in AWS.")
        return True
    typer.echo("✅ No removal drift detected (local may have extra permissions; that's fine).")
    return False

@app.command()
def drift(
    policy_name: str = typer.Option(..., "--policy-name"),
    policy_file: str = typer.Option(..., "--file"),
    account_id: str = typer.Option(None, "--account-id"),
    approvers: str = typer.Option("", help="Comma-separated GitHub usernames for approval"),
    approval_anyway: bool = typer.Option(False, "--approval-anyway"),
    repo_full_name: str = typer.Option(None, "--repo")
):
    iam = boto3.client("iam")
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
    drift_detected = detect_drift(local_doc, aws_doc)

    repo_full_name = repo_full_name or os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    if not repo_full_name:
        typer.echo("❌ GitHub repo not specified.")
        raise typer.Exit(1)
    if not token:
        typer.echo("❌ GITHUB_TOKEN not set.")
        raise typer.Exit(1)
    assignees = [a.strip() for a in approvers.split(",") if a.strip()]

    if drift_detected:
        print_drift_diff(local_doc, aws_doc)
        issue_num, _ = create_approval_issue(repo_full_name, token, policy_name, assignees=assignees)
        typer.echo(f"✅ Approval issue created: https://github.com/{repo_full_name}/issues/{issue_num}")
        choice = wait_for_sync_choice(repo_full_name, issue_num, token, allowed_approvers=assignees)
        _handle_choice(choice, local_doc, aws_doc, iam, policy_arn, repo_full_name, token, policy_file, policy_name, issue_num)
    else:
        if approval_anyway:
            issue_num, _ = create_approval_issue(repo_full_name, token, policy_name, assignees=assignees, approval_anyway=True)
            typer.echo(f"✅ Forced approval issue created: https://github.com/{repo_full_name}/issues/{issue_num}")
            choice = wait_for_sync_choice(repo_full_name, issue_num, token, allowed_approvers=assignees, approval_anyway=True)
            if choice == "approve":
                _update_aws_policy(iam, policy_arn, local_doc)
                typer.echo(f"✅ AWS policy {policy_arn} updated as approved.")
                close_issue(repo_full_name, token, issue_num, "✅ Approved and applied. Closing issue.")
            else:
                typer.echo("❌ Approval rejected. Exiting.")
                close_issue(repo_full_name, token, issue_num, "❌ Rejected. Closing issue.")
                raise typer.Exit(1)
        else:
            _update_aws_policy(iam, policy_arn, local_doc)
            typer.echo(f"✅ AWS policy {policy_arn} updated to include any local additions.")
            typer.echo("✅ No forced approval requested. Exiting.")

def _handle_choice(choice, local_doc, aws_doc, iam, policy_arn, repo, token, policy_file, policy_name, issue_num):
    if choice == "local->aws":
        merged_doc = merge_policy_documents(local_doc, aws_doc)
        _apply_aws_update_and_close(iam, policy_arn, merged_doc, repo, token, issue_num, "✅ AWS updated with local changes.")
    elif choice == "aws->local":
        _update_local_and_create_pr(aws_doc, policy_file, repo, policy_name, issue_num, token, "from AWS policy")
    elif choice == "aws<->local":
        superset_doc = build_superset_policy(local_doc, aws_doc)
        _apply_aws_update_and_close(iam, policy_arn, superset_doc, repo, token, issue_num, "✅ Superset applied.")
        _update_local_and_create_pr(superset_doc, policy_file, repo, policy_name, issue_num, token, "with superset of local + AWS")
    else:
        typer.echo("⏭ No synchronization performed (skip).")
        close_issue(repo, token, issue_num, "⏭ No sync chosen. Closing issue.")

def _apply_aws_update_and_close(iam, policy_arn, doc, repo, token, issue_num, message):
    _update_aws_policy(iam, policy_arn, doc)
    close_issue(repo, token, issue_num, message)

def _update_aws_policy(iam, policy_arn, policy_doc):
    sids = [stmt.get("Sid") for stmt in policy_doc.get("Statement", []) if "Sid" in stmt]
    if len(sids) != len(set(sids)):
        raise ValueError("❌ Merged policy would produce duplicate SIDs. Cannot update AWS policy.")
    current_version_id = iam.get_policy(PolicyArn=policy_arn)["Policy"]["DefaultVersionId"]
    current_doc = iam.get_policy_version(PolicyArn=policy_arn, VersionId=current_version_id)["PolicyVersion"]["Document"]
    if policy_doc == current_doc:
        print("✅ Merged policy is identical to existing AWS policy. No update needed.")
        return
    versions = iam.list_policy_versions(PolicyArn=policy_arn)["Versions"]
    if len(versions) >= 5:
        oldest = sorted((v for v in versions if not v["IsDefaultVersion"]), key=lambda v: v["CreateDate"])[0]
        iam.delete_policy_version(PolicyArn=policy_arn, VersionId=oldest["VersionId"])
    iam.create_policy_version(
        PolicyArn=policy_arn,
        PolicyDocument=json.dumps(policy_doc),
        SetAsDefault=True
    )
    print(f"✅ AWS policy {policy_arn} updated successfully.")

def _update_local_and_create_pr(doc, policy_file, repo_full_name, policy_name, issue_num, token, description=""):
    with open(policy_file, "w") as f:
        f.write(json.dumps(doc, indent=2))
    branch = f"drift-sync-{policy_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}".replace(' ', '-').replace('+', 'plus').replace('/', '-').strip('-').lower()
    push_branch(branch)
    pr_title = f"Update {policy_file} {description}"
    pr_body = f"This PR updates `{policy_file}` {description}.\n\nLinked to issue #{issue_num}."
    pr_num, pr_url = create_github_pr(repo_full_name, branch, pr_title, pr_body, issue_num=issue_num)
    if not pr_num:
        typer.echo("⚠️ PR creation failed. Manual PR needed.")
    close_issue(repo_full_name, token, issue_num, f"✅ PR created and linked: {pr_url}. Closing issue.")
