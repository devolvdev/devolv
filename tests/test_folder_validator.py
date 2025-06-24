import os
import tempfile
import pytest
import json
from pathlib import Path
from devolv.iam.validator.folder import validate_policy_folder

VALID_POLICY = '''
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "s3:ListBucket",
    "Resource": "arn:aws:s3:::example_bucket"
  }]
}
'''

INVALID_POLICY = '''
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
  }]
}
'''

@pytest.fixture
def temp_policy_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

def test_validate_folder_all_valid(temp_policy_dir):
    (temp_policy_dir / "valid1.json").write_text(VALID_POLICY)
    (temp_policy_dir / "valid2.json").write_text(VALID_POLICY)

    result = validate_policy_folder(str(temp_policy_dir))
    assert result == []  # all valid, no findings

def test_validate_folder_some_invalid(temp_policy_dir):
    (temp_policy_dir / "good.json").write_text(VALID_POLICY)
    (temp_policy_dir / "bad.json").write_text(INVALID_POLICY)

    result = validate_policy_folder(str(temp_policy_dir))
    assert any(f["level"] == "high" for f in result)
    assert any("wildcard" in f["message"] for f in result)

def test_validate_folder_empty(temp_policy_dir):
    result = validate_policy_folder(str(temp_policy_dir))
    assert len(result) == 1
    assert result[0]["level"] == "warning"
    assert "No policy files found" in result[0]["message"]

def test_validate_folder_not_exist():
    result = validate_policy_folder("non_existent_folder_123")
    assert len(result) == 1
    assert result[0]["level"] == "error"
    assert "not found" in result[0]["message"]

def test_folder_with_malformed_json(tmp_path):
    (tmp_path / "bad.json").write_text('{"Version": "2012-10-17", "Statement": [INVALID_JSON')
    result = validate_policy_folder(str(tmp_path))
    assert any("failed" in f["message"] for f in result)

def test_folder_with_yaml_file(tmp_path):
    good_yaml = """
Version: "2012-10-17"
Statement:
  - Effect: "Allow"
    Action: "s3:GetObject"
    Resource: "arn:aws:s3:::bucket/*"
"""
    (tmp_path / "good.yaml").write_text(good_yaml)
    result = validate_policy_folder(str(tmp_path))
    assert result == []  # no findings

def test_folder_with_good_and_bad_files(tmp_path):
    good = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::x"}]
    }
    (tmp_path / "good.json").write_text(json.dumps(good))
    (tmp_path / "broken.json").write_text('INVALID')
    result = validate_policy_folder(str(tmp_path))
    assert any("failed" in f["message"] for f in result)
