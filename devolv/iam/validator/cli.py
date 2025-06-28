import typer
import os
import json
import ast
from typer import Exit
from devolv.iam.validator.core import validate_policy_file
from devolv.iam.validator.folder import validate_policy_folder

app = typer.Typer(help="IAM Policy Validator CLI")

@app.command("validate")
def validate(
    path: str,
    json_output: bool = typer.Option(False, "--json", help="Output findings in JSON format"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress debug logs"),
):
    if not os.path.exists(path):
        typer.secho(f"❌ File not found: {path}", fg=typer.colors.RED)
        raise Exit(code=1)

    findings = []
    if os.path.isfile(path):
        findings = validate_policy_file(path)
    elif os.path.isdir(path):
        findings = validate_policy_folder(path)
    else:
        typer.secho(f"❌ Unsupported path type: {path}", fg=typer.colors.RED)
        raise Exit(code=1)

    if not findings:
        msg = (
            "✅ Policy is valid and passed all checks."
            if os.path.isfile(path)
            else "✅ All policies passed validation."
        )
        typer.secho(msg, fg=typer.colors.GREEN)
        raise Exit(code=0)

    if json_output:
        typer.echo(json.dumps(findings, indent=2))
    else:
        for finding in findings:
            msg = finding.get('message', '')
            try:
                inner_findings = ast.literal_eval(msg) if isinstance(msg, str) else msg
                if isinstance(inner_findings, list):
                    for inner in inner_findings:
                        typer.secho(
                            f"❌ {inner.get('level', '').upper()}: {inner.get('message', '')}",
                            fg=typer.colors.RED
                        )
                else:
                    typer.secho(
                        f"❌ {finding.get('level', '').upper()}: {msg}",
                        fg=typer.colors.RED
                    )
            except Exception:
                typer.secho(
                    f"❌ {finding.get('level', '').upper()}: {msg}",
                    fg=typer.colors.RED
                )

    if any(f.get("level", "").lower() in ("error", "high") for f in findings):
        raise Exit(code=1)
    else:
        raise Exit(code=0)
