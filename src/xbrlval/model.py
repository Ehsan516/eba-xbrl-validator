#Domain model for validation results

from __future__ import annotations
from datetime import UTC, datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class Severity(StrEnum):
    """How serious a finding is.
    BLOCKING findings would cause a regulator to reject the submission
    WARING findings are reportable but not fatal
    INFO findings are informational output from the processor"""

    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


class ValidationLayer(StrEnum):
    #validation layers ordered from structral to semantic

    XML = "xml"  
    XBRL_21= "xbrl-2.1" 
    DIMENSIONS ="dimensions"
    CALCULATION= "calculation"
    FORMULA ="formula"
    FILING ="filing"
    CUSTOM ="custom"
    OTHER ="other"


class Finding(BaseModel):
    #A single validation finding, normalised from Arelle or a custom rule

    severity: Severity
    layer: ValidationLayer
    code: str = Field(description="Message/rule code.")
    message: str
    concept: str | None = Field(default=None, description="QName of the concept involved.")
    context_ref: str | None = Field(default=None, description="Context id of the fact involved.")
    source: str = Field(default="arelle", description="'arelle' or the custom rule id.")


class ValidationReport(BaseModel):
    #the full result of validating one instance
    instance: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    findings: list[Finding] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        #Valid if no blocking findings
        return not any(f.severity is Severity.BLOCKING for f in self.findings)

    def by_layer(self) -> dict[ValidationLayer, list[Finding]]:
        grouped: dict[ValidationLayer, list[Finding]] = {}
        for f in self.findings:
            grouped.setdefault(f.layer, []).append(f)
        return grouped

    def counts(self) -> dict[Severity, int]:
        counts = {s: 0 for s in Severity}
        for f in self.findings:
            counts[f.severity] += 1
        return counts
