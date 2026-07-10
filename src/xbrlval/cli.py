from __future__ import annotations
from pathlib import Path
import typer
from xbrlval import __version__
from xbrlval.config import ValidatorConfig
from xbrlval.report import to_json, to_text
from xbrlval.validate import validate_instance

app = typer.Typer(
    help="Validate EBA XBRL submission",
    add_completion=False,
)


@app.command()
def version() -> None:
    """Print tool version"""
    typer.echo(f"eba-xbrl-validator {__version__}")


@app.command()
def validate(
    instance: Path = typer.Argument(..., help="Path to the XBRL instance file"),
    taxonomy_package: list[Path] = typer.Option(
        [], "--taxonomy-package", "-t",
        help="Taxonomy package zip(s), e.g. the EBA framework release",
    ),
    cache_dir: Path = typer.Option(
        None, "--cache-dir", help="Arelle web cache directory"
    ),
    online: bool = typer.Option(
        False, "--online", help="allow network access to resolve taxonomy files"
    ),
    no_formula: bool = typer.Option(
        False, "--no-formula", help="Skip formula linkbase evaluation"
    ),
    output_format: str = typer.Option(
        "text", "--format", "-f", help="Report format: text or json"
    ),
    out: Path = typer.Option(
        None, "--out", "-o", help="Write the report to a file instead of stdout."
    ),
) -> None:
    """Validate an XBRL instance against the EBA taxonomy and rules."""
    config = ValidatorConfig(
        taxonomy_packages=taxonomy_package,
        cache_dir=cache_dir,
        offline=not online,
        validate_formula=not no_formula,
    )
    report = validate_instance(instance, config)
    rendered = to_json(report) if output_format == "json" else to_text(report)

    if out is not None:
        out.write_text(rendered, encoding="utf-8")
        typer.echo(f"Report written to {out}")
    else:
        typer.echo(rendered)

    raise typer.Exit(code=0 if report.is_valid else 1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
