from typer.testing import CliRunner
from devolv.cli import app
import tempfile
import json
import os
import pytest
from devolv.iam.validator.core import validate_policy_file
from devolv import __version__

runner = CliRunner()

# ---- Setup dummy policies ----

def make_policy_file(policy_dict):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
    json.dump(policy_dict, tmp)
    tmp.close()
    return tmp.name

def test_validate_file_success():
    path = make_policy_file({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::my-bucket/my-object.txt"

        }]
    })
    result = runner.invoke(app, ["validate", path])
    assert result.exit_code == 0
    os.remove(path)



def test_validate_file_error():
    path = make_policy_file({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    })
    result = runner.invoke(app, ["validate", path])
    assert result.exit_code == 1
    assert "❌" in result.output
    os.remove(path)

def test_validate_file_missing():
    result = runner.invoke(app, ["validate", "no_such_file.json"])
    assert result.exit_code == 1
    assert "not found" in result.output

def test_validate_folder_all_valid(tmp_path):
    valid = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::x"}]
    }
    for i in range(2):
        path = tmp_path / f"v{i}.json"
        path.write_text(json.dumps(valid))

    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 0
    assert "✅" in result.output

def test_validate_folder_with_errors(tmp_path):
    good = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::x"}]
    }
    bad = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    }
    (tmp_path / "good.json").write_text(json.dumps(good))
    (tmp_path / "bad.json").write_text(json.dumps(bad))

    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 1
    assert "❌" in result.output

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Devolv CLI" in result.output

def test_cli_root_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Modular DevOps Toolkit" in result.output

def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output # Adjust if dynamic version

def test_cli_unsupported_path(tmp_path):
    # Just pass a bogus path string that isn't a file or directory
    bogus_path = str(tmp_path / "definitely_not_real")
    result = runner.invoke(app, ["validate", bogus_path])
    assert result.exit_code == 1
    assert "File not found" in result.output or "Unsupported path type" in result.output


def test_cli_empty_file(tmp_path):
    file = tmp_path / "empty.json"
    file.write_text("")
    with pytest.raises(ValueError):
        validate_policy_file(str(file))

def test_cli_malformed_json(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text("{not: valid json}")
    with pytest.raises(Exception):  # You can tighten this if you want json.JSONDecodeError
        validate_policy_file(str(file))

def test_cli_folder_all_valid(tmp_path):
    file = tmp_path / "good.json"
    file.write_text('{"Version":"2012-10-17","Statement":[]}')
    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 0
    assert "No high-risk findings" in result.output


def test_cli_json_output(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text('{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":"*"}]}')
    result = runner.invoke(app, ["validate", str(file), "--json"])
    assert result.exit_code == 1
    assert result.output.strip().startswith("[")  # Should be JSON list

def test_cli_quiet_flag(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text('{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":"*"}]}')
    result = runner.invoke(app, ["validate", str(file), "--quiet"])
    # Should still print findings (quiet may suppress debug logs, not findings)
    assert result.exit_code == 1
    assert "s3:*" in result.output

def test_cli_exit_code_low_severity(tmp_path):
    # Policy that would produce only low severity finding if such exists
    # Here we force no high/error to test exit 0
    file = tmp_path / "low.json"
    file.write_text('{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*", "Resource":"*"}]}')
    result = runner.invoke(app, ["validate", str(file)])
    assert result.exit_code == 0

def test_cli_json_and_quiet_combination(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text('{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"s3:*","Resource":"*"}]}')
    result = runner.invoke(app, ["validate", str(file), "--json", "--quiet"])
    assert result.exit_code == 1
    assert result.output.strip().startswith("[")
