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
