import boto3

def assume_role(role_arn, session_name="DevolvDriftSession"):
    client = boto3.client("sts")
    response = client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    creds = response["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
