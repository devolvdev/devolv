import boto3
import json
from collections import defaultdict

def get_aws_policy_document(policy_arn: str) -> dict:
    """
    Fetch the JSON document of the default version of a managed IAM policy.
    """
    iam = boto3.client("iam")
    policy = iam.get_policy(PolicyArn=policy_arn)['Policy']
    default_version = policy['DefaultVersionId']
    version = iam.get_policy_version(PolicyArn=policy_arn, VersionId=default_version)
    return version['PolicyVersion']['Document']

def _combine_statements(docs):
    combined = defaultdict(lambda: {"Sid": None, "Effect": None, "Action": None, "Resource": set()})

    for doc in docs:
        for stmt in doc.get("Statement", []):
            key = (
                stmt.get("Sid"),
                stmt.get("Effect"),
                json.dumps(stmt.get("Action"), sort_keys=True)
            )

            combined_stmt = combined[key]
            combined_stmt["Sid"] = stmt.get("Sid")
            combined_stmt["Effect"] = stmt.get("Effect")
            combined_stmt["Action"] = stmt.get("Action")

            resources = stmt.get("Resource")
            if not isinstance(resources, list):
                resources = [resources]
            
            combined_stmt["Resource"].update(resources)

    result = []
    for stmt in combined.values():
        result.append({
            "Sid": stmt["Sid"],
            "Effect": stmt["Effect"],
            "Action": stmt["Action"],
            "Resource": sorted(stmt["Resource"])
        })

    return result

def merge_policy_documents(local_doc: dict, aws_doc: dict) -> dict:
    """
    Merge local and AWS policy documents: append any local-only permissions while
    merging resources under same Sid + Effect + Action where possible.
    """
    merged_statements = _combine_statements([aws_doc, local_doc])
    return {
        "Version": "2012-10-17",
        "Statement": merged_statements
    }

def build_superset_policy(local_doc: dict, aws_doc: dict) -> dict:
    """
    Build a superset of local + AWS policy, merging where possible.
    """
    merged_statements = _combine_statements([local_doc, aws_doc])
    return {
        "Version": "2012-10-17",
        "Statement": merged_statements
    }
