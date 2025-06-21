import typer
from devolv.iam.validator.core import validate_policy_file

app = typer.Typer(help="IAM Validator CLI")

@app.command("file")
def validate_file(path: str):
    """
    Validate an AWS IAM policy file (JSON or YAML).
    """
    findings = validate_policy_file(path)
    if not findings:
        typer.secho("✅ Policy is valid and passed all checks.", fg=typer.colors.GREEN)
    else:
        for finding in findings:
            typer.secho(f"❌ {finding['level'].upper()}: {finding['message']}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
