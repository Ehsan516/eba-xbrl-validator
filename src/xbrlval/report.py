"""Rendering ValidationReports as text or JSON"""

from __future__ import annotations

from xbrlval.model import Severity, ValidationLayer, ValidationReport

_LAYER_ORDER = list(ValidationLayer)

_SEVERITY_MARK = {
    Severity.BLOCKING: "✖",
    Severity.WARNING: "⚠",
    Severity.INFO: "·",
}


def to_json(report: ValidationReport) -> str:
    return report.model_dump_json(indent=2)


def to_text(report: ValidationReport) -> str:
    lines: list[str] = []
    counts = report.counts()
    verdict = "VALID" if report.is_valid else "INVALID"
    lines.append(f"Instance : {report.instance}")
    lines.append(f"Verdict  : {verdict}")
    lines.append(
        "Findings : "
        f"{counts[Severity.BLOCKING]} blocking, "
        f"{counts[Severity.WARNING]} warning, "
        f"{counts[Severity.INFO]} info"
    )

    grouped = report.by_layer()
    for layer in _LAYER_ORDER:
        findings = grouped.get(layer)
        if not findings:
            continue
        lines.append("")
        lines.append(f"[{layer.value}] — {len(findings)} finding(s)")
        for f in findings:
            location = ""
            if f.concept or f.context_ref:
                location = f"  ({f.concept or '?'} @ {f.context_ref or '?'})"
            lines.append(f"  {_SEVERITY_MARK[f.severity]} {f.code}: {f.message}{location}")

    return "\n".join(lines)
