def check_wildcard_actions(policy):
    statements = policy.get("Statement", [])
    if not isinstance(statements, list):
        statements = [statements]
    for stmt in statements:
        if stmt.get("Effect", "Allow") != "Allow":
            continue  # Skip Deny statements
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        if any(a == "*" or a.endswith(":*") for a in actions):
            return "Policy uses wildcard in Action, which is overly permissive."
    return None

def check_passrole_wildcard(policy):
    statements = policy.get("Statement", [])
    if not isinstance(statements, list):
        statements = [statements]
    for stmt in statements:
        if stmt.get("Effect", "Allow") != "Allow":
            continue  # Skip Deny statements
        actions = stmt.get("Action", [])
        resources = stmt.get("Resource", [])
        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]
        if "iam:PassRole" in actions and "*" in resources:
            return "iam:PassRole with wildcard resource can lead to privilege escalation."
    return None

RULES = [
    {
        "id": "IAM001",
        "level": "high",
        "description": "Wildcard in Action",
        "check": check_wildcard_actions
    },
    {
        "id": "IAM002",
        "level": "high",
        "description": "PassRole with wildcard Resource",
        "check": check_passrole_wildcard
    }
]
