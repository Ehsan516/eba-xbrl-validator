"""Project-specific validation rules. The first two mirror real EBA Filing Manual concerns: duplicate facts are
prohibited in filings, and numeric facts are expected to declare their precision via the decimals attribute
"""

from __future__ import annotations

from collections.abc import Iterator

from arelle.ModelXbrl import ModelXbrl

from xbrlval.model import Finding, Severity, ValidationLayer
from xbrlval.rules.base import rule


@rule
class NoDuplicateFacts:
    """Filings must not report the same concept twice in the same context/unit."""

    rule_id = "XV-001"
    description = "Duplicate facts (same concept, context, and unit) are prohibited."

    def check(self, model_xbrl: ModelXbrl) -> Iterator[Finding]:
        seen: dict[tuple, str] = {}
        for fact in model_xbrl.facts:
            if fact.qname is None or fact.contextID is None:
                continue
            key = (fact.qname, fact.contextID, fact.unitID)
            if key in seen:
                yield Finding(
                    severity=Severity.BLOCKING,
                    layer=ValidationLayer.CUSTOM,
                    code=self.rule_id,
                    message=(
                        f"Duplicate fact for concept {fact.qname} in context "
                        f"'{fact.contextID}' (values '{seen[key]}' and '{fact.value}')."
                    ),
                    concept=str(fact.qname),
                    context_ref=fact.contextID,
                    source=self.rule_id,
                )
            else:
                seen[key] = fact.value


@rule
class NumericFactsDeclareDecimals:
    """Numeric facts should state their precision with a decimals attribute."""

    rule_id = "XV-002"
    description = "Numeric facts must carry a decimals attribute."

    def check(self, model_xbrl: ModelXbrl) -> Iterator[Finding]:
        for fact in model_xbrl.facts:
            if fact.isNumeric and not fact.isNil and fact.decimals is None:
                yield Finding(
                    severity=Severity.WARNING,
                    layer=ValidationLayer.CUSTOM,
                    code=self.rule_id,
                    message=f"Numeric fact {fact.qname} has no decimals attribute.",
                    concept=str(fact.qname),
                    context_ref=fact.contextID,
                    source=self.rule_id,
                )
