import json
import difflib
from rich.console import Console
from rich.text import Text
import typer

def clean_policy(policy):
    """
    Remove empty statements ({} entries) from the policy's 'Statement' list.
    """
    if isinstance(policy, dict) and "Statement" in policy:
        statements = policy.get("Statement", [])
        if isinstance(statements, list):
            policy["Statement"] = [s for s in statements if s]
    return policy

def generate_diff_report(local_policy, aws_policy):
    """
    Generate a Git-style unified diff report for two IAM policies (local vs AWS),
    with inline highlights for changed parts of a line.
    """
    console = Console()

    # Clean out empty statements to reduce noise
    if isinstance(local_policy, dict):
        local_policy = clean_policy(local_policy)
    if isinstance(aws_policy, dict):
        aws_policy = clean_policy(aws_policy)

    # Convert dicts to pretty-printed JSON strings
    if isinstance(local_policy, dict):
        local_str = json.dumps(local_policy, indent=2, sort_keys=True)
    else:
        local_str = str(local_policy)

    if isinstance(aws_policy, dict):
        aws_str = json.dumps(aws_policy, indent=2, sort_keys=True)
    else:
        aws_str = str(aws_policy)

    # Split into lines
    local_lines = local_str.splitlines(keepends=False)
    aws_lines = aws_str.splitlines(keepends=False)

    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        local_lines,
        aws_lines,
        fromfile="local",
        tofile="aws",
        lineterm=""
    ))

    if not diff_lines:
        console.print("✅ No drift detected: Policies match.", style="green")
        return

    console.print("❌ Drift detected — see diff below", style="bold red")
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]

        if line.startswith('---') or line.startswith('+++'):
            console.print(Text(line, style="bold"))
        elif line.startswith('@@'):
            console.print(Text(line, style="cyan"))
        elif line.startswith('-'):
            # Check if next line is a '+', for possible inline diff
            if (i + 1 < len(diff_lines)) and diff_lines[i + 1].startswith('+'):
                next_line = diff_lines[i + 1]
                old_content = line[1:].rstrip('\n')
                new_content = next_line[1:].rstrip('\n')

                # Use SequenceMatcher for inline diff
                matcher = difflib.SequenceMatcher(None, old_content, new_content)
                old_text = Text("-", style="red")
                new_text = Text("+", style="green")

                for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                    if tag == 'equal':
                        old_text.append(old_content[i1:i2], style="red")
                        new_text.append(new_content[j1:j2], style="green")
                    elif tag == 'replace':
                        old_text.append(old_content[i1:i2], style="bold white on red")
                        new_text.append(new_content[j1:j2], style="bold black on green")
                    elif tag == 'delete':
                        old_text.append(old_content[i1:i2], style="bold white on red")
                    elif tag == 'insert':
                        new_text.append(new_content[j1:j2], style="bold black on green")

                console.print(old_text)
                console.print(new_text)
                i += 1  # Skip next line since it's handled
            else:
                console.print(Text(line, style="red"))
        elif line.startswith('+'):
            console.print(Text(line, style="green"))
        elif line.startswith(' '):
            console.print(Text(line, style="bright_black"))
        else:
            console.print(Text(line))  # Fallback for any edge case lines
        i += 1
    raise typer.Exit(1)
