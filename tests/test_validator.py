
import json

def _find_statement_line(stmt, raw_lines):
    if raw_lines is None:
        return None
    stmt_text = json.dumps(stmt, indent=2).splitlines()[0].strip()
    for i, line in enumerate(raw_lines):
        if stmt_text in line:
            return i + 1
    return None

def check_wildcard_actions(policy, raw_lines=None):
    statements = policy.get("Statement", [])
    if not isinstance(statements, list):
        statements = [statements]

    for stmt in statements:
        if stmt.get("Effect", "Allow") != "Allow":
            continue

        actions = stmt.get("Action", [])
        resources = stmt.get("Resource", [])

        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]

        for a in actions:
            if a == "*" or a.endswith(":*"):
                line_num = _find_statement_line(stmt, raw_lines)
                if any(r == "*" for r in resources):
                    return {
                        "id": "IAM001",
                        "level": "high",
                        "message": (
                            f"Policy uses wildcard action '{a}' with wildcard resource '*' — overly permissive."
                            + (f" Statement starts at line {line_num}." if line_num else "")
                        )
                    }
                else:
                    return {
                        "id": "IAM001",
                        "level": "high",
                        "message": (
                            f"Policy uses wildcard action '{a}' — overly permissive."
                            + (f" Statement starts at line {line_num}." if line_num else "")
                        )
                    }
    return None

def check_passrole_wildcard(policy, raw_lines=None):
    statements = policy.get("Statement", [])
    if not isinstance(statements, list):
        statements = [statements]

    for stmt in statements:
        if stmt.get("Effect", "Allow") != "Allow":
            continue

        actions = stmt.get("Action", [])
        resources = stmt.get("Resource", [])

        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]

        if "iam:PassRole" in actions and "*" in resources:
            line_num = _find_statement_line(stmt, raw_lines)
            return {
                "id": "IAM002",
                "level": "high",
                "message": (
                    f"iam:PassRole with wildcard resource '*' can lead to privilege escalation."
                    + (f" Statement starts at line {line_num}." if line_num else "")
                )
            }
    return None

RULES = [
    {
        "id": "IAM001",
        "level": "high",
        "description": "Wildcard in Action (e.g. * or service:*) is overly permissive",
        "check": check_wildcard_actions,
    },
    {
        "id": "IAM002",
        "level": "high",
        "description": "PassRole with wildcard Resource",
        "check": check_passrole_wildcard,
    },
]



import tempfile
import json
import os
from devolv.iam.validator.core import validate_policy_file

def create_temp_policy(policy):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        return f.name

def test_policy_with_wildcard_action():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_safe_policy_passes():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::example"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert not findings
    os.remove(temp_path)

def test_passrole_wildcard_resource():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "iam:PassRole", "Resource": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("passrole" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_with_suffix_wildcard_action():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "arn:aws:s3:::example"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_statement_as_dict():
    policy = {
        "Version": "2012-10-17",
        "Statement": {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "arn:aws:s3:::example"
        }
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_deny_policy_ignored():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert not findings
    os.remove(temp_path)

def test_passrole_deny_ignored():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Deny", "Action": "iam:PassRole", "Resource": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert not findings
    os.remove(temp_path)

def test_multiple_statements_mixed():
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:*", "Resource": "arn:aws:s3:::example"},
            {"Effect": "Allow", "Action": "iam:PassRole", "Resource": "*"},
            {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::example/file"}
        ]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert len(findings) >= 2
    os.remove(temp_path)

def test_policy_no_resource_field():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_with_list_of_resources():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": ["*", "arn:aws:s3:::example"]}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_with_mixed_effects():
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Deny", "Action": "*", "Resource": "*"},
            {"Effect": "Allow", "Action": "*", "Resource": "*"}
        ]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_case_insensitive_passrole():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "IAM:PASSROLE", "Resource": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("passrole" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_no_statement_field():
    policy = {
        "Version": "2012-10-17"
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert findings == [] or not findings
    os.remove(temp_path)

def test_policy_empty_statement_list():
    policy = {
        "Version": "2012-10-17",
        "Statement": []
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert findings == [] or not findings
    os.remove(temp_path)

def test_policy_allow_empty_action_resource():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert findings == [] or not findings
    os.remove(temp_path)

def test_policy_service_wildcard_mixed_case():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "S3:*", "Resource": "*"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert any("permissive" in str(f.get("message", "")).lower() for f in findings)
    os.remove(temp_path)

def test_policy_passrole_specific_resource():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "iam:PassRole", "Resource": "arn:aws:iam::123456789012:role/MyRole"}]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert not findings
    os.remove(temp_path)

def test_policy_multiple_statements_all_safe():
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::example/file"},
            {"Effect": "Allow", "Action": "ec2:DescribeInstances", "Resource": "*"}
        ]
    }
    temp_path = create_temp_policy(policy)
    findings = validate_policy_file(temp_path)
    assert not findings
    os.remove(temp_path)

