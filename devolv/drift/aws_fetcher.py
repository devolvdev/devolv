import boto3
import botocore

def get_policy(policy_name=None, policy_arn=None):
    client = boto3.client("iam")
    sts_client = boto3.client("sts")

    try:
        if policy_arn:
            # Directly fetch by provided ARN
            return _fetch_policy_document(client, policy_arn)

        # No ARN provided → try to construct ARN
        account_id = sts_client.get_caller_identity()["Account"]
        constructed_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

        try:
            return _fetch_policy_document(client, constructed_arn)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] not in ["NoSuchEntity", "AccessDenied"]:
                raise  # Unexpected error, re-raise

            # Fallthrough to attempt list-based discovery
            pass

        # Fallback: attempt to list policies (if permission allows)
        paginator = client.get_paginator('list_policies')
        for page in paginator.paginate(Scope='Local'):
            for policy in page['Policies']:
                if policy['PolicyName'] == policy_name:
                    return _fetch_policy_document(client, policy['Arn'])

        # As last attempt, try AWS-managed policies
        for page in paginator.paginate(Scope='AWS'):
            for policy in page['Policies']:
                if policy['PolicyName'] == policy_name:
                    return _fetch_policy_document(client, policy['Arn'])

        # Not found at all
        return None

    except botocore.exceptions.ClientError as e:
        error = e.response.get("Error", {})
        code = error.get("Code", "UnknownError")
        message = error.get("Message", "")
        print(f"❌ AWS API error during policy fetch: {code} — {message}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during policy fetch: {str(e)}")
        return None

def _fetch_policy_document(client, policy_arn):
    policy_meta = client.get_policy(PolicyArn=policy_arn)
    version_id = policy_meta["Policy"]["DefaultVersionId"]
    version = client.get_policy_version(
        PolicyArn=policy_arn,
        VersionId=version_id
    )
    return version["PolicyVersion"]["Document"]
