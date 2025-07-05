import boto3
import json

def get_aws_policy_document(policy_arn: str) -> dict:
    """
    Fetch the JSON document of the default version of a managed IAM policy.
    """
    iam = boto3.client("iam")
    policy = iam.get_policy(PolicyArn=policy_arn)['Policy']
    default_version = policy['DefaultVersionId']
    version = iam.get_policy_version(PolicyArn=policy_arn, VersionId=default_version)
    return version['PolicyVersion']['Document']

def merge_policy_documents(local_doc: dict, aws_doc: dict) -> dict:
    """
    Merge statements by appending any local-only statements to the AWS document.
    This is an "append-only" merge (we do not delete existing AWS statements).
    """
    aws_stmts = aws_doc.get("Statement", [])
    local_stmts = local_doc.get("Statement", [])
    merged = list(aws_stmts)  # copy existing AWS statements
    for stmt in local_stmts:
        if stmt not in aws_stmts:
            merged.append(stmt)
    aws_doc["Statement"] = merged
    return aws_doc

def build_superset_policy(local_doc: dict, aws_doc: dict) -> dict:
    """
    Combine local and AWS policy documents into a superset without duplicate statements.
    """
    local_statements = local_doc.get("Statement", [])
    aws_statements = aws_doc.get("Statement", [])

    seen = set()
    combined = []

    for stmt in local_statements + aws_statements:
        stmt_str = json.dumps(stmt, sort_keys=True)
        if stmt_str not in seen:
            seen.add(stmt_str)
            combined.append(stmt)

    return {
        "Version": "2012-10-17",
        "Statement": combined
    }
