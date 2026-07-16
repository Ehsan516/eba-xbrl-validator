from pathlib import Path

from typer.testing import CliRunner

from xbrlval.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()


def test_validate_batch_over_explicit_files():
    result = runner.invoke(
        app,
        [
            "validate-batch",
            "--no-formula",
            str(FIXTURES / "valid_instance.xbrl"),
            str(FIXTURES / "broken_instance.xbrl"),
        ],
    )
    assert result.exit_code == 1
    assert "Batch verdict : INVALID" in result.stdout
    assert "Instances     : 2 (1 valid, 1 invalid)" in result.stdout


def test_validate_batch_over_directory_skips_non_instance_files():
    result = runner.invoke(
        app, ["validate-batch", "--no-formula", "--format", "json", str(FIXTURES)]
    )
    assert result.exit_code == 1
    assert '"demo.xsd"' not in result.stdout


def test_validate_batch_all_valid_exits_zero():
    result = runner.invoke(
        app,
        ["validate-batch", "--no-formula", str(FIXTURES / "valid_instance.xbrl")],
    )
    assert result.exit_code == 0
    assert "Batch verdict : VALID" in result.stdout
