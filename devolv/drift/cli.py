import typer
from pathlib import Path
from devolv.drift import aws_fetcher, file_loader, report
import botocore

def drift(
    policy_name: str = typer.Option(..., "--policy-name", help="IAM policy name in AWS"),
    file: str = typer.Option(..., "--file", help="Path to local policy file")
):
    try:
        local_path = Path(file)
        if not local_path.exists():
            typer.secho(f"❌ File not found: {file}", fg=typer.colors.RED)
            raise typer.Exit(1)

        local_policy = file_loader.load_policy(local_path)
        aws_policy = aws_fetcher.get_policy(policy_name)

        if aws_policy is None:
            typer.secho(f"⚠️ Could not fetch AWS policy '{policy_name}'.", fg=typer.colors.YELLOW)
            raise typer.Exit(1)

        report.generate_diff_report(local_policy, aws_policy)

    except botocore.exceptions.ClientError as e:
        error = e.response.get("Error", {})
        code = error.get("Code", "UnknownError")
        message = error.get("Message", "")

        typer.secho(f"❌ AWS API error: {code}", fg=typer.colors.RED)

        if code == "AccessDenied" and ' because ' in message:
            main, reason = message.split(' because ', 1)
            typer.echo(f"   → {main.strip()}")
            typer.echo(f"   → Reason: {reason.strip()}")
        else:
            typer.echo(f"   → {message.strip()}")

        typer.echo(f"⚠️ Could not fetch AWS policy '{policy_name}'.")
        typer.echo(f"💡 Tip: Ensure your IAM user has permission for {code}-related actions.")
        raise typer.Exit(1)

    except typer.Exit:
        raise  # Let Typer handle clean exits

    except Exception as e:
        typer.secho(f"❌ Unexpected error: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(1)
