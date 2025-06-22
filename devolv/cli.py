import typer
from devolv.iam.validator.cli import app as validate_app

app = typer.Typer(help="Devolv CLI - Modular DevOps Toolkit")
app.add_typer(validate_app, name="validate")

if __name__ == "__main__":  # pragma: no cover
    app()

@app.command("version")
def version():
    """Print CLI version."""
    typer.echo("Devolv v0.1.0")
