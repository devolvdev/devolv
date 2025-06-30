import pytest
import json
import yaml
import botocore
from pathlib import Path
from typer.testing import CliRunner
import typer
import re

# Import modules under test.
from devolv.drift import aws_fetcher, file_loader, comparator, report, cli, utils
from devolv.drift.cli import drift

# Mock AWS classes
class FakeSTSClient:
    def __init__(self, account_id="123456789012", raise_on=None, creds=None):
        self._account_id = account_id
        self.raise_on = raise_on
        self._creds = creds or {
            "AccessKeyId": "AKIAFAKE",
            "SecretAccessKey": "SECRETFAKE",
            "SessionToken": "TOKENFAKE"
        }
    def get_caller_identity(self):
        if self.raise_on == 'get_identity':
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "AuthError", "Message": "Auth failed"}}, "GetCallerIdentity"
            )
        return {"Account": self._account_id}
    def assume_role(self, RoleArn, RoleSessionName):
        if self.raise_on == 'assume_role':
            raise Exception("Assume role failed")
        return {"Credentials": self._creds}

class FakeIAMClient:
    def __init__(self, policy_docs=None, default_version="v1", raise_on=None):
        self.policy_docs = policy_docs or {}
        self.default_version = default_version
        self.raise_on = raise_on or {}
        self.local_policies = []
        self.aws_policies = []
    def get_policy(self, PolicyArn):
        if 'get_policy' in self.raise_on and PolicyArn in self.raise_on['get_policy']:
            code, message = self.raise_on['get_policy'][PolicyArn]
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": code, "Message": message}}, "GetPolicy"
            )
        if PolicyArn not in self.policy_docs:
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "NoSuchEntity", "Message": "Policy not found"}}, "GetPolicy"
            )
        return {"Policy": {"DefaultVersionId": self.default_version}}
    def get_policy_version(self, PolicyArn, VersionId):
        if 'get_policy_version' in self.raise_on and PolicyArn in self.raise_on['get_policy_version']:
            raise Exception("Failed to get policy version")
        return {"PolicyVersion": {"Document": self.policy_docs.get(PolicyArn)}}
    def get_paginator(self, operation_name):
        assert operation_name == 'list_policies'
        return self
    def paginate(self, Scope):
        if Scope == 'Local':
            yield {"Policies": self.local_policies}
        elif Scope == 'AWS':
            yield {"Policies": self.aws_policies}
        else:
            yield {"Policies": []}

@pytest.fixture(autouse=True)
def patch_boto_clients(monkeypatch):
    def fake_client(service_name):
        raise AssertionError(f"Unexpected boto3.client call for {service_name}")
    monkeypatch.setattr("boto3.client", fake_client)
    monkeypatch.setattr(aws_fetcher, "boto3", aws_fetcher.boto3)
    monkeypatch.setattr(utils, "boto3", utils.boto3)
    return

def test_get_policy_with_direct_arn(monkeypatch):
    fake_iam = FakeIAMClient(policy_docs={"arn:aws:iam::123:policy/test": {"Statement": [1, 2, 3]}})
    fake_sts = FakeSTSClient(account_id="123")
    monkeypatch.setattr("boto3.client", lambda svc: fake_iam if svc == "iam" else fake_sts)
    doc = aws_fetcher.get_policy(policy_arn="arn:aws:iam::123:policy/test")
    assert doc == {"Statement": [1, 2, 3]}

def test_get_policy_with_name_success(monkeypatch):
    fake_iam = FakeIAMClient(policy_docs={"arn:aws:iam::123:policy/policyname": {"Statement": [{"Sid": "Stmt"}]}})
    fake_sts = FakeSTSClient(account_id="123")
    monkeypatch.setattr("boto3.client", lambda svc: fake_iam if svc == "iam" else fake_sts)
    result = aws_fetcher.get_policy(policy_name="policyname")
    assert result == {"Statement": [{"Sid": "Stmt"}]}

def test_get_policy_name_in_local_list(monkeypatch):
    fake_sts = FakeSTSClient(account_id="111")
    fake_iam = FakeIAMClient(policy_docs={"arn:aws:iam::111:policy/found_local": {"foo": "bar"}})
    fake_iam.local_policies = [{"PolicyName": "found", "Arn": "arn:aws:iam::111:policy/found_local"}]
    monkeypatch.setattr("boto3.client", lambda svc: fake_iam if svc == "iam" else fake_sts)
    res = aws_fetcher.get_policy(policy_name="found")
    assert res == {"foo": "bar"}

def test_get_policy_in_aws_managed_list(monkeypatch):
    fake_sts = FakeSTSClient(account_id="222")
    fake_iam = FakeIAMClient(policy_docs={"arn:aws:iam::222:policy/aws_managed": {"v": 1}})
    fake_iam.aws_policies = [{"PolicyName": "aws", "Arn": "arn:aws:iam::222:policy/aws_managed"}]
    monkeypatch.setattr("boto3.client", lambda svc: fake_iam if svc == "iam" else fake_sts)
    res = aws_fetcher.get_policy(policy_name="aws")
    assert res == {"v": 1}

def test_get_policy_not_found_returns_none(monkeypatch):
    fake_sts = FakeSTSClient(account_id="999")
    fake_iam = FakeIAMClient(policy_docs={})
    monkeypatch.setattr("boto3.client", lambda svc: fake_iam if svc == "iam" else fake_sts)
    res = aws_fetcher.get_policy(policy_name="none")
    assert res is None

def test_get_policy_unexpected_error(monkeypatch, capsys):
    fake_sts = FakeSTSClient(account_id="000", raise_on='get_identity')
    fake_iam = FakeIAMClient(policy_docs={})
    monkeypatch.setattr("boto3.client", lambda svc: fake_iam if svc == "iam" else fake_sts)
    res = aws_fetcher.get_policy(policy_name="foo")
    captured = capsys.readouterr()
    assert "AWS API error during policy fetch" in captured.out
    assert res is None

def test_load_json_valid(tmp_path):
    data = {"foo": "bar", "num": 42}
    json_file = tmp_path / "policy.json"
    json_file.write_text(json.dumps(data))
    result = file_loader.load_policy(json_file)
    assert result == data

def test_load_yaml_valid(tmp_path):
    data = {"alpha": 1, "beta": {"nested": True}}
    yaml_file = tmp_path / "policy.yaml"
    yaml_file.write_text(yaml.dump(data))
    result = file_loader.load_policy(yaml_file)
    assert result == data

def test_compare_policies_equal():
    a = {"a": [1, 2, 3], "b": {"x": 10}}
    b = {"b": {"x": 10}, "a": [3, 2, 1]}
    diff = comparator.compare_policies(a, b)
    assert not diff

def test_compare_policies_difference():
    a = {"key": "old", "list": [1,2]}
    b = {"key": "new", "list": [2,1,3]}
    diff = comparator.compare_policies(a, b)
    assert diff.get('values_changed') or diff.get('iterable_item_added')

def test_clean_policy_removes_empty():
    policy = {"Statement": [{}, {"Action": "s3", "Effect": "Allow"}, {}]}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned["Statement"] == [{"Action": "s3", "Effect": "Allow"}]

def test_clean_policy_non_dict():
    policy = "not a dict"
    assert report.clean_policy(policy) == policy

def test_generate_diff_report_no_diff(capsys):
    policy = {"A": 1}
    report.generate_diff_report(policy, {"A": 1})
    captured = capsys.readouterr()
    assert "No drift detected" in captured.out

def test_generate_diff_report_with_diff(capsys):
    local = {"A": 1}
    aws = {"A": 2}
    report.generate_diff_report(local, aws)
    captured = capsys.readouterr()
    out = captured.out
    assert "--- local" in out and "+++ aws" in out
    assert re.search(r'-\s+"A":\s*1', out)
    assert re.search(r'\+\s+"A":\s*2', out)

def test_generate_diff_report_addition(capsys):
    local = {}
    aws = {"A": 5}
    report.generate_diff_report(local, aws)
    captured = capsys.readouterr()
    out = captured.out
    assert re.search(r'\+\s+"A":\s*5', out)

def test_generate_diff_report_deletion(capsys):
    local = {"B": 10}
    aws = {}
    report.generate_diff_report(local, aws)
    captured = capsys.readouterr()
    out = captured.out
    assert re.search(r'-\s+"B":\s*10', out)

@pytest.fixture
def runner():
    app = typer.Typer()
    app.command()(cli.drift)
    return CliRunner(), app

def test_cli_drift_detected(runner, tmp_path, monkeypatch):
    runner_obj, app = runner
    local = {"A": 1}
    aws = {"A": 2}
    file = tmp_path / "policy.json"
    file.write_text(json.dumps(local))
    monkeypatch.setattr(aws_fetcher, "get_policy", lambda policy_name=None: aws)
    result = runner_obj.invoke(app, ["--policy-name", "test", "--file", str(file)])
    assert result.exit_code == 0
    assert "--- local" in result.stdout
    assert "+++ aws" in result.stdout

# Cover CLI main logic: exception in report
def test_cli_report_exception(runner, tmp_path, monkeypatch):
    runner_obj, app = runner
    local = {"X": 1}
    aws = {"X": 2}
    file = tmp_path / "p.json"
    file.write_text(json.dumps(local))
    monkeypatch.setattr(aws_fetcher, "get_policy", lambda policy_name=None: aws)
    monkeypatch.setattr(report, "generate_diff_report", lambda l, a: (_ for _ in ()).throw(Exception("Render fail")))
    result = runner_obj.invoke(app, ["--policy-name", "x", "--file", str(file)])
    assert result.exit_code == 1
    assert "Unexpected error: Render fail" in result.stdout

# Cover aws_fetcher: list policies fallback
def test_get_policy_list_fallback(monkeypatch):
    class FakeSTS:
        def get_caller_identity(self):
            return {"Account": "123"}

    class FakeIAM:
        def __init__(self):
            self.called_arn = None
        def get_policy(self, PolicyArn):
            self.called_arn = PolicyArn
            if PolicyArn == "arn:aws:iam::123:policy/fallback":
                return {"Policy": {"DefaultVersionId": "v1"}}
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "NoSuchEntity", "Message": "Policy not found"}}, "GetPolicy"
            )
        def get_policy_version(self, PolicyArn, VersionId):
            return {"PolicyVersion": {"Document": {"from": "list"}}}
        def get_paginator(self, operation_name):
            return self
        def paginate(self, Scope):
            if Scope == "Local":
                yield {"Policies": [{"PolicyName": "fallback", "Arn": "arn:aws:iam::123:policy/fallback"}]}
            else:
                yield {"Policies": []}

    monkeypatch.setattr("boto3.client", lambda svc: FakeIAM() if svc == "iam" else FakeSTS())
    result = aws_fetcher.get_policy(policy_name="fallback")
    assert result == {"from": "list"}



# Cover utils: assume_role bad credentials
def test_assume_role_incomplete_creds(monkeypatch):
    class FakeSTS:
        def assume_role(self, RoleArn, RoleSessionName):
            return {"Credentials": {
                "AccessKeyId": None,
                "SecretAccessKey": None,
                "SessionToken": None
            }}
    monkeypatch.setattr("boto3.client", lambda svc: FakeSTS())
    # Optionally patch boto3.Session to avoid creating real session
    import boto3
    monkeypatch.setattr(boto3, "Session", lambda **kwargs: type("FakeSession", (), {
        "get_credentials": lambda self: type("C", (), {
            "access_key": kwargs.get("aws_access_key_id"),
            "secret_key": kwargs.get("aws_secret_access_key"),
            "token": kwargs.get("aws_session_token"),
        })()
    })())
    session = utils.assume_role("arn:aws:iam::123:role/test")
    creds = session.get_credentials()
    assert creds.access_key is None


# Cover report.py fallback diff line
def test_generate_diff_report_odd_lines(capsys):
    local = {"A": 1}
    aws = {"A": 2}
    # Patch difflib to yield weird lines
    import difflib
    real_diff = difflib.unified_diff
    def fake_diff(*args, **kwargs):
        return iter(["??? odd line"])
    difflib.unified_diff = fake_diff
    report.generate_diff_report(local, aws)
    captured = capsys.readouterr()
    assert "odd line" in captured.out
    difflib.unified_diff = real_diff

def test_cli_access_denied_no_because(monkeypatch, tmp_path):
    runner = CliRunner()
    app = cli.typer.Typer()
    app.command()(cli.drift)

    file = tmp_path / "test.json"
    file.write_text(json.dumps({"A": 1}))

    err = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "No permission"}},
        "GetPolicy"
    )
    monkeypatch.setattr(aws_fetcher, "get_policy", lambda *args, **kwargs: (_ for _ in ()).throw(err))
    result = runner.invoke(app, ["--policy-name", "pol", "--file", str(file)])
    assert result.exit_code == 1
    assert "AWS API error: AccessDenied" in result.stdout
    assert "No permission" in result.stdout

# Extra CLI path coverage: unknown exception triggers fallback
def test_cli_unknown_exception(monkeypatch, tmp_path):
    runner = CliRunner()
    app = cli.typer.Typer()
    app.command()(cli.drift)

    file = tmp_path / "test.json"
    file.write_text(json.dumps({"A": 1}))

    monkeypatch.setattr(aws_fetcher, "get_policy", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Boom")))
    result = runner.invoke(app, ["--policy-name", "pol", "--file", str(file)])
    assert result.exit_code == 1
    assert "Unexpected error: Boom" in result.stdout

# Extra aws_fetcher fallback: AWS managed policy list
def test_get_policy_aws_managed_list(monkeypatch):
    class FakeSTS:
        def get_caller_identity(self):
            return {"Account": "123"}

    class FakeIAM:
        def get_policy(self, PolicyArn):
            if PolicyArn == "arn:aws:iam::123:policy/awsfallback":
                return {"Policy": {"DefaultVersionId": "v1"}}
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "NoSuchEntity", "Message": "Policy not found"}}, "GetPolicy"
            )
        def get_policy_version(self, PolicyArn, VersionId):
            return {"PolicyVersion": {"Document": {"from": "aws-managed"}}}
        def get_paginator(self, operation_name):
            return self
        def paginate(self, Scope):
            if Scope == "AWS":
                yield {"Policies": [{"PolicyName": "awsfallback", "Arn": "arn:aws:iam::123:policy/awsfallback"}]}
            else:
                yield {"Policies": []}

    monkeypatch.setattr("boto3.client", lambda svc: FakeIAM() if svc == "iam" else FakeSTS())
    res = aws_fetcher.get_policy(policy_name="awsfallback")
    assert res == {"from": "aws-managed"}


# Report.py: cover clean_policy with no Statement key
def test_clean_policy_no_statement_key():
    policy = {"Effect": "Allow"}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned == policy


def test_cli_aws_policy_none(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    runner = CliRunner()
    app = typer.Typer()
    app.command()(drift)

    file = tmp_path / "file.json"
    file.write_text(json.dumps({"foo": "bar"}))

    monkeypatch.setattr(aws_fetcher, "get_policy", lambda *a, **k: None)
    result = runner.invoke(app, ["--policy-name", "mypol", "--file", str(file)])
    assert result.exit_code == 1
    assert "Could not fetch AWS policy" in result.stdout

def test_cli_access_denied_because(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    runner = CliRunner()
    app = typer.Typer()
    app.command()(drift)

    file = tmp_path / "file.json"
    file.write_text(json.dumps({"foo": "bar"}))

    err = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Access denied because test reason"}},
        "GetPolicy"
    )
    monkeypatch.setattr(aws_fetcher, "get_policy", lambda *a, **k: (_ for _ in ()).throw(err))
    result = runner.invoke(app, ["--policy-name", "mypol", "--file", str(file)])
    assert result.exit_code == 1
    assert "AWS API error: AccessDenied" in result.stdout
    assert "Reason: test reason" in result.stdout

def test_cli_typer_exit(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    runner = CliRunner()
    app = typer.Typer()
    app.command()(drift)

    file = tmp_path / "file.json"
    file.write_text(json.dumps({"foo": "bar"}))

    def fake_get_policy(*a, **k):
        raise typer.Exit(1)

    monkeypatch.setattr(aws_fetcher, "get_policy", fake_get_policy)
    result = runner.invoke(app, ["--policy-name", "mypol", "--file", str(file)])
    assert result.exit_code == 1

def test_clean_policy_all_empty_statements():
    policy = {"Statement": [{}, {}]}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned["Statement"] == []

def test_generate_diff_report_empty_inputs(capsys):
    report.generate_diff_report({}, {})
    out = capsys.readouterr().out
    assert "No drift detected" in out

def test_get_policy_no_match_final_none(monkeypatch):
    class FakeSTS:
        def get_caller_identity(self):
            return {"Account": "123"}
    class FakeIAM:
        def get_policy(self, PolicyArn):
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "NoSuchEntity", "Message": "Not found"}}, "GetPolicy"
            )
        def get_paginator(self, operation_name):
            return self
        def paginate(self, Scope):
            yield {"Policies": []}
    monkeypatch.setattr("boto3.client", lambda svc: FakeIAM() if svc == "iam" else FakeSTS())
    res = aws_fetcher.get_policy(policy_name="nomatch")
    assert res is None

def test_cli_file_not_found(monkeypatch):
    from typer.testing import CliRunner
    runner = CliRunner()
    app = typer.Typer()
    app.command()(cli.drift)
    result = runner.invoke(app, ["--policy-name", "foo", "--file", "nonexistent.json"])
    assert result.exit_code == 1
    assert "File not found" in result.stdout

def test_clean_policy_all_statements_empty():
    policy = {"Statement": [{}, {}]}
    cleaned = report.clean_policy(policy)
    assert cleaned["Statement"] == []

def test_clean_policy_no_statement():
    policy = {"Effect": "Allow"}
    cleaned = report.clean_policy(policy)
    assert cleaned == policy

def test_get_policy_unexpected_client_error(monkeypatch, capsys):
    class FakeSTS:
        def get_caller_identity(self):
            return {"Account": "123"}
    class FakeIAM:
        def get_policy(self, PolicyArn):
            return {"Policy": {"DefaultVersionId": "v1"}}
        def get_policy_version(self, PolicyArn, VersionId):
            return {"PolicyVersion": {"Document": {}}}

    def fake_fetch_policy_document(client, policy_arn):
        raise botocore.exceptions.ClientError(
            {"Error": {"Code": "SomeOtherError", "Message": "Unexpected error"}},
            "GetPolicy"
        )

    monkeypatch.setattr("boto3.client", lambda svc: FakeIAM() if svc == "iam" else FakeSTS())
    monkeypatch.setattr(aws_fetcher, "_fetch_policy_document", fake_fetch_policy_document)

    res = aws_fetcher.get_policy(policy_name="unexpected")
    assert res is None
    out = capsys.readouterr().out
    assert "AWS API error during policy fetch: SomeOtherError" in out
    assert "Unexpected error" in out



def test_get_policy_top_level_exception(monkeypatch, capsys):
    class FakeSTS:
        def get_caller_identity(self):
            raise Exception("Top level boom")
    class FakeIAM:
        def get_policy(self, PolicyArn):
            return {}
    monkeypatch.setattr("boto3.client", lambda svc: FakeIAM() if svc == "iam" else FakeSTS())
    res = aws_fetcher.get_policy(policy_name="oops")
    assert res is None
    out = capsys.readouterr().out
    assert "Unexpected error during policy fetch" in out

def test_clean_policy_mixed_empty_statements():
    policy = {"Statement": [{}, {"Action": "s3:*", "Effect": "Allow"}]}
    cleaned = report.clean_policy(policy)
    assert cleaned["Statement"] == [{"Action": "s3:*", "Effect": "Allow"}]

def test_clean_policy_removes_empty_statements():
    from devolv.drift import report
    # Statement list with empty dicts only
    policy = {"Statement": [{}, {}]}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned["Statement"] == []

def test_get_policy_triggers_unexpected_client_error(monkeypatch):
    from devolv.drift import aws_fetcher
    class FakeSTS:
        def get_caller_identity(self):
            return {"Account": "123"}
    class FakeIAM:
        def get_policy(self, PolicyArn):
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "SomeOtherError", "Message": "Boom"}}, "GetPolicy"
            )
    monkeypatch.setattr("boto3.client", lambda svc: FakeIAM() if svc == "iam" else FakeSTS())
    result = aws_fetcher.get_policy(policy_name="oops")
    assert result is None

def test_clean_policy_no_statements_key():
    from devolv.drift import report
    policy = {"Effect": "Allow"}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned == policy

def test_clean_policy_all_empty_statements():
    from devolv.drift import report
    policy = {"Statement": [{}, {}]}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned["Statement"] == []

def test_clean_policy_no_statement_key():
    from devolv.drift import report
    policy = {"Effect": "Allow"}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned == policy

def test_clean_policy_all_empty_statements():
    from devolv.drift import report
    policy = {"Statement": [{}, {}]}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned["Statement"] == []

def test_clean_policy_no_statement_key():
    from devolv.drift import report
    policy = {"Effect": "Allow"}
    cleaned = report.clean_policy(policy.copy())
    assert cleaned == policy
