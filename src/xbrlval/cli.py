from __future__ import annotations
import sys
from pathlib import Path
import typer
from xbrlval import __version__
from xbrlval.config import ValidatorConfig
from xbrlval.report import to_json, to_json_batch, to_text, to_text_batch
from xbrlval.validate import validate_batch, validate_instance

_INSTANCE_SUFFIXES = {".xbrl", ".xml"}

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


@app.command("validate-batch")
def validate_batch_cmd(
    instances: list[Path] = typer.Argument(
        ..., help="XBRL instance files, or directories to scan for .xbrl/.xml files"
    ),
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
    """Validate multiple XBRL instances in one run and print a combined report."""
    paths: list[Path] = []
    for p in instances:
        if p.is_dir():
            paths.extend(
                sorted(q for q in p.iterdir() if q.suffix.lower() in _INSTANCE_SUFFIXES)
            )
        else:
            paths.append(p)

    if not paths:
        typer.echo("No instance files found.", err=True)
        raise typer.Exit(code=1)

    config = ValidatorConfig(
        taxonomy_packages=taxonomy_package,
        cache_dir=cache_dir,
        offline=not online,
        validate_formula=not no_formula,
    )
    batch = validate_batch(paths, config)
    rendered = to_json_batch(batch) if output_format == "json" else to_text_batch(batch)

    if out is not None:
        out.write_text(rendered, encoding="utf-8")
        typer.echo(f"Report written to {out}")
    else:
        typer.echo(rendered)

    raise typer.Exit(code=0 if batch.is_valid else 1)


@app.command()
def ui(
    host: str = typer.Option("127.0.0.1", help="Interface to bind"),
    port: int = typer.Option(8000, help="Port to serve on"),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Don't open a browser window automatically"
    ),
) -> None:
    """Launch the local web UI."""
    try:
        from xbrlval.webui import main as run_ui
    except ImportError:
        typer.echo(
            "The web UI requires the 'api' extra: pip install 'eba-xbrl-validator[api]'",
            err=True,
        )
        raise typer.Exit(code=1) from None

    run_ui(host=host, port=port, open_browser=not no_browser)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    app()


if __name__ == "__main__":
    main()
