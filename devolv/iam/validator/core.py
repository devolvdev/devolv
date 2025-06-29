import json
import yaml
from devolv.iam.validator.rules import RULES

def load_policy(path: str):
    with open(path, "r") as f:
        content = f.read()
        if not content.strip():
            raise ValueError("Policy file is empty.")
        f.seek(0)
        if path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f), content.splitlines()
        return json.load(f), content.splitlines()

def validate_policy_file(path: str):
    data, raw_lines = load_policy(path)
    findings = []
    for rule in RULES:
        findings.extend(rule["check"](data, raw_lines=raw_lines))
    return findings

