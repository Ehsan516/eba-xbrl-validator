from pathlib import Path

import pytest

from xbrlval.config import ValidatorConfig
from xbrlval.model import Severity, ValidationLayer
from xbrlval.validate import categorise_layer, validate_instance

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def config() -> ValidatorConfig:
    #the demo fixture taxonomy has no formula linkbase,skipping it keeps suite fast
    return ValidatorConfig(offline=True, validate_formula=False)


def test_valid_instance_is_valid(config):

    report = validate_instance(FIXTURES / "valid_instance.xbrl", config)
    assert report.is_valid
    assert not [f for f in report.findings if f.severity is Severity.BLOCKING]


def test_broken_instance_is_invalid(config):

    report = validate_instance(FIXTURES / "broken_instance.xbrl", config)
    assert not report.is_valid


def test_broken_instance_dangling_context_caught_by_arelle(config):
    report = validate_instance(FIXTURES / "broken_instance.xbrl", config)
    xbrl_errors = [
        
        f for f in report.findings
        if f.layer is ValidationLayer.XBRL_21 and f.severity is Severity.BLOCKING
    ]
    assert any("context" in f.message.lower() for f in xbrl_errors)


def test_broken_instance_duplicate_fact_caught_by_custom_rule(config):
    report = validate_instance(FIXTURES / "broken_instance.xbrl", config)
    codes = [f.code for f in report.findings]
    assert "XV-001" in codes
    assert "XV-002" in codes


def test_custom_findings_carry_location(config):
    report = validate_instance(FIXTURES / "broken_instance.xbrl", config)
    dup = next(f for f in report.findings if f.code == "XV-001")
    assert dup.concept == "demo:TierOneCapital"
    assert dup.context_ref == "c1"


def test_missing_file_raises(config):
    with pytest.raises(FileNotFoundError):
        validate_instance(FIXTURES / "does_not_exist.xbrl", config)


@pytest.mark.parametrize(
    ("code", "layer"),
    [
        ("xmlSchema:syntax", ValidationLayer.XML),
        ("xbrl.4.6.1:itemContextRef", ValidationLayer.XBRL_21),
        ("xbrldie:PrimaryItemDimensionallyInvalidError", ValidationLayer.DIMENSIONS),
        ("message:v0001_m", ValidationLayer.FORMULA),
        ("EBA.1.6", ValidationLayer.FILING),
        ("somethingUnknown", ValidationLayer.OTHER),
    ],
)
def test_categorise_layer(code, layer):
    assert categorise_layer(code) is layer
