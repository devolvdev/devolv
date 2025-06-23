import typer
import os
from typer import Exit
from devolv.iam.validator.core import validate_policy_file
from devolv.iam.validator.folder import validate_policy_folder

def validate(
    path: str,
    json_output: bool = typer.Option(False, "--json", help="Output findings in JSON format"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress debug logs"),
):
    if not os.path.exists(path):
        typer.secho(f"❌ Path not found: {path}", fg=typer.colors.RED)
        raise Exit(code=1)

    if os.path.isfile(path):
        findings = validate_policy_file(path)
        if not findings:
            typer.secho("✅ Policy is valid and passed all checks.", fg=typer.colors.GREEN)
            raise Exit(code=0)
        for finding in findings:
            typer.secho(f"❌ {finding['level'].upper()}: {finding['message']}", fg=typer.colors.RED)
        raise Exit(code=1)

    elif os.path.isdir(path):
        findings = validate_policy_folder(path)
        if not findings:
            typer.secho("✅ All policies passed validation.", fg=typer.colors.GREEN)
            raise Exit(code=0)
        for finding in findings:
            typer.secho(f"❌ {finding['level'].upper()}: {finding['message']}", fg=typer.colors.RED)
        if any(f["level"] == "error" for f in findings):
            raise Exit(code=1)
        raise Exit(code=0)

    else:
        typer.secho(f"❌ Unsupported path type: {path}", fg=typer.colors.RED)
        raise Exit(code=1)
