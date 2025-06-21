import json
import yaml
from pathlib import Path
from devolv.iam.validator.rules import RULES

def load_policy(path: str):
    with open(path, "r") as f:
        if path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f)
        return json.load(f)

def validate_policy_file(path: str):
    data = load_policy(path)
    findings = []
    for rule in RULES:
        result = rule["check"](data)
        if result:
            findings.append({
                "id": rule["id"],
                "level": rule["level"],
                "message": result
            })
    return findings
