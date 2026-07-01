"""Command-line interface
wiring it up to Arelle is Phase 1 of roadmap.
"""

from pathlib import Path

import typer

from xbrlval import __version__

app = typer.Typer(
    help="Validate EBA COREP/FINREP XBRL submissions.",
    add_completion=False,
)


@app.command()
def version() -> None:
    """Print the tool version."""
    typer.echo(f"eba-xbrl-validator {__version__}")


@app.command()
def validate(
    instance: Path = typer.Argument(..., help="Path to the XBRL instance file."),
) -> None:
    """Validate an XBRL instance against the EBA taxonomy and rules."""
    typer.echo(f"Not yet implemented — would validate: {instance}")
    raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
