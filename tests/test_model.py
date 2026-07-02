from xbrlval.model import Finding, Severity, ValidationLayer, ValidationReport


def make_finding(severity: Severity, layer=ValidationLayer.XBRL_21, code="x") -> Finding:
    return Finding(severity=severity, layer=layer, code=code, message="msg")


def test_report_with_no_findings_is_valid():
    report = ValidationReport(instance="i.xbrl")
    assert report.is_valid


def test_warnings_do_not_invalidate():
    report = ValidationReport(instance="i.xbrl", findings=[make_finding(Severity.WARNING)])
    assert report.is_valid


def test_blocking_finding_invalidates():
    report = ValidationReport(instance="i.xbrl", findings=[make_finding(Severity.BLOCKING)])
    assert not report.is_valid


def test_by_layer_groups_findings():
    report = ValidationReport(
        instance="i.xbrl",
        findings=[
            make_finding(Severity.INFO, ValidationLayer.XML),
            make_finding(Severity.INFO, ValidationLayer.XML),
            make_finding(Severity.INFO, ValidationLayer.CUSTOM),
        ],
    )
    grouped = report.by_layer()
    assert len(grouped[ValidationLayer.XML]) == 2
    assert len(grouped[ValidationLayer.CUSTOM]) == 1


def test_counts_by_severity():
    report = ValidationReport(
        instance="i.xbrl",
        findings=[
            make_finding(Severity.BLOCKING),
            make_finding(Severity.WARNING),
            make_finding(Severity.WARNING),
        ],
    )
    counts = report.counts()
    assert counts[Severity.BLOCKING] == 1
    assert counts[Severity.WARNING] == 2
    assert counts[Severity.INFO] == 0
