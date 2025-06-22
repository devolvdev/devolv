from typer.testing import CliRunner
from devolv.cli import app
import tempfile
import json
import os

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
        "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::bucket/*"}]
    })
    result = runner.invoke(app, ["validate", "file", path])
    assert result.exit_code == 0
    assert "✅" in result.output
    os.remove(path)

def test_validate_file_error():
    path = make_policy_file({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
    })
    result = runner.invoke(app, ["validate", "file", path])
    assert result.exit_code == 1
    assert "❌" in result.output
    os.remove(path)

def test_validate_file_missing():
    result = runner.invoke(app, ["validate", "file", "no_such_file.json"])
    assert result.exit_code == 1
    assert "File not found" in result.output

def test_validate_folder_all_valid(tmp_path):
    valid = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "arn:aws:s3:::x"}]
    }
    for i in range(2):
        path = tmp_path / f"v{i}.json"
        path.write_text(json.dumps(valid))

    result = runner.invoke(app, ["validate", "folder", str(tmp_path)])
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

    result = runner.invoke(app, ["validate", "folder", str(tmp_path)])
    assert result.exit_code == 1
    assert "❌" in result.output

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Devolv CLI" in result.output

def test_cli_root_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Devolv CLI - Modular DevOps Toolkit" in result.output

def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "v0.1.0" in result.output
