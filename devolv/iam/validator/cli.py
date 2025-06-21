import typer
from devolv.iam.validator.core import validate_policy_file

file_app = typer.Typer(help="Commands to validate IAM policy files.")

@file_app.command("file")
def validate_file(path: str):
    """
    Validate an AWS IAM policy file (JSON or YAML).
    """
    try:
        findings = validate_policy_file(path)
    except FileNotFoundError:
        typer.secho(f"❌ File not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"❌ Unexpected error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not findings:
        typer.secho("✅ Policy is valid and passed all checks.", fg=typer.colors.GREEN)
    else:
        typer.secho("⚠️ Issues found in the policy:", fg=typer.colors.YELLOW)
        for finding in findings:
            typer.secho(f" - {finding['level'].upper()}: {finding['message']}", fg=typer.colors.RED)
        raise typer.Exit(code=2)

