import typer
import os
import json
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
        if not findings:
            typer.secho("✅ Policy is valid and passed all checks.", fg=typer.colors.GREEN)
        elif json_output:
            typer.echo(json.dumps(findings, indent=2))
        else:
            for finding in findings:
                typer.secho(
                    f"❌ {finding.get('level', '').upper()}: {finding.get('message', '')}",
                    fg=typer.colors.RED
                )
    elif os.path.isdir(path):
        findings = validate_policy_folder(path)
        if json_output:
            typer.echo(json.dumps(findings, indent=2))
        # No re-print of findings — already handled by folder validator
    else:
        typer.secho(f"❌ Unsupported path type: {path}", fg=typer.colors.RED)
        raise Exit(code=1)

    # Determine exit code
    if any(f.get("level", "").lower() in ("error", "high") for f in findings):
        raise Exit(code=1)
    else:
        raise Exit(code=0)
