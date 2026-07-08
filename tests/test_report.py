import json

from xbrlval.model import Finding, Severity, ValidationLayer, ValidationReport
from xbrlval.report import to_json, to_text


def make_report() -> ValidationReport:
    return ValidationReport(
        instance="demo.xbrl",
        findings=[
            Finding(
                severity=Severity.BLOCKING,
                layer=ValidationLayer.XBRL_21,
                code="xbrl.4.6.1:itemContextRef",
                message="Item demo:TotalAssets must have a context",
            ),
            Finding(
                severity=Severity.WARNING,
                layer=ValidationLayer.CUSTOM,
                code="XV-002",
                message="Numeric fact has no decimals attribute.",
                concept="demo:TierOneCapital",
                context_ref="c1",
                source="XV-002",
            ),
        ],
    )


def test_text_report_contains_verdict_and_codes():
    text = to_text(make_report())
    assert "INVALID" in text
    assert "xbrl.4.6.1:itemContextRef" in text
    assert "XV-002" in text
    assert "demo:TierOneCapital @ c1" in text


def test_json_report_round_trips():
    payload = json.loads(to_json(make_report()))
    assert payload["instance"] == "demo.xbrl"
    assert len(payload["findings"]) == 2
    assert payload["findings"][0]["severity"] == "blocking"
    assert payload["findings"][1]["layer"] == "custom"
