from devolv.iam.validator.core import validate_policy_file
import tempfile
import json

def test_policy_with_wildcard_action():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    }
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as f:
        json.dump(policy, f)
        f.flush()
        findings = validate_policy_file(f.name)
        assert any("Wildcard in Action" in f["message"] for f in findings)

def test_safe_policy_passes():
    policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::example"}]
    }
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as f:
        json.dump(policy, f)
        f.flush()
        findings = validate_policy_file(f.name)
        assert findings == []
