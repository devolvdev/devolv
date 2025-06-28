import json

def _find_statement_line(stmt, raw_lines):
    if not raw_lines:
        return None

    effect = stmt.get("Effect")
    actions = stmt.get("Action", [])
    resources = stmt.get("Resource", [])

    if isinstance(actions, str):
        actions = [actions]
    if isinstance(resources, str):
        resources = [resources]

    # Scan for Action lines directly
    for i in range(len(raw_lines)):
        if any(a in raw_lines[i] for a in actions):
            # Look ahead for Resource in next few lines
            block = "\n".join(raw_lines[i:i+5])
            if any(r in block for r in resources):
                return i + 1

    # Fallback: look for Effect + Action in block
    for i in range(len(raw_lines)):
        if f'"Effect": "{effect}"' in raw_lines[i] or f"'Effect': '{effect}'" in raw_lines[i]:
            block = "\n".join(raw_lines[i:i+10])
            if any(a in block for a in actions) and any(r in block for r in resources):
                return i + 1

    return None

def check_wildcard_actions(policy, raw_lines=None):
    findings = []
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
                findings.append({
                    "id": "IAM001",
                    "level": "high",
                    "message": (
                        f"Policy uses overly permissive action '{a}' "
                        + (f"with resource {resources}" if resources else "without resource scope")
                        + (f". Statement starts at line {line_num}." if line_num else "")
                    )
                })
    return findings


def check_passrole_wildcard(policy, raw_lines=None):
    findings = []
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

        if any(a.lower() == "iam:passrole" for a in actions) and "*" in resources:
            line_num = _find_statement_line(stmt, raw_lines)
            findings.append({
                "id": "IAM002",
                "level": "high",
                "message": (
                    f"iam:PassRole with wildcard Resource ('*') can lead to privilege escalation."
                    + (f" Statement starts at line {line_num}." if line_num else "")
                )
            })
    return findings

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
