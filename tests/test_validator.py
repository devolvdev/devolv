import tempfile
import json
import os
from devolv.iam.validator.core import validate_policy_file

def test_policy_with_wildcard_action():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert any("wildcard" in f["message"].lower() for f in findings)
    os.remove(temp_path)

def test_safe_policy_passes():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::example"}]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert not findings
    os.remove(temp_path)

def test_empty_file_raises_error():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        validate_policy_file(temp_path)
        assert False, "Expected ValueError for empty file"
    except ValueError as e:
        assert "empty" in str(e).lower()
    finally:
        os.remove(temp_path)

def test_missing_file_handled():
    missing_path = "non_existent_policy.json"
    try:
        validate_policy_file(missing_path)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass

def test_passrole_with_wildcard_resource():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*"
        }]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert any("passrole" in f["message"].lower() for f in findings)
    os.remove(temp_path)


def test_rule_wildcard_action_star():
    # Should trigger IAM001
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "*",
            "Resource": "arn:aws:s3:::example"
        }]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert any("wildcard" in f["message"].lower() and "action" in f["message"].lower() for f in findings)
    os.remove(temp_path)

def test_rule_wildcard_action_suffix():
    # Should also trigger IAM001
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::example"
        }]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert any("wildcard" in f["message"].lower() for f in findings)
    os.remove(temp_path)

def test_rule_passrole_with_wildcard_resource():
    # Should trigger IAM002
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*"
        }]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert any("passrole" in f["message"].lower() for f in findings)
    os.remove(temp_path)

def test_statement_as_dict_not_list():
    policy = {
        "Version": "2012-10-17",
        "Statement": {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "arn:aws:s3:::x"
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert any("wildcard" in f["message"].lower() for f in findings)
    os.remove(temp_path)

def test_deny_wildcard_action_not_flagged():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Deny",
            "Action": "*",
            "Resource": "*"
        }]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert not findings, "Deny with wildcard should not trigger findings"
    os.remove(temp_path)


def test_deny_passrole_wildcard_not_flagged():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Deny",
            "Action": "iam:PassRole",
            "Resource": "*"
        }]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(policy, f)
        temp_path = f.name

    findings = validate_policy_file(temp_path)
    assert not findings, "Deny PassRole with wildcard should not trigger findings"
    os.remove(temp_path)
