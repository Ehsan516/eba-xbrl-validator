"""rules registered in custom_rules run over a loaded instance"""

from __future__ import annotations

from arelle.ModelXbrl import ModelXbrl

from xbrlval.model import Finding
from xbrlval.rules import custom_rules
from xbrlval.rules.base import all_rules


def run_custom_rules(model_xbrl: ModelXbrl) -> list[Finding]:
    findings: list[Finding] = []
    for r in all_rules():
        findings.extend(r.check(model_xbrl))
    return findings
