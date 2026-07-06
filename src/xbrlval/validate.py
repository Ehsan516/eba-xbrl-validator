"""Validation orchestration and normalisation
"""

from __future__ import annotations

from pathlib import Path

from arelle import Validate, XbrlConst
from arelle.ModelFormulaObject import FormulaOptions

from xbrlval.config import ValidatorConfig
from xbrlval.loader import CapturedRecord, InstanceLoader
from xbrlval.model import Finding, Severity, ValidationLayer, ValidationReport
from xbrlval.rules import run_custom_rules


_LAYER_PREFIXES: list[tuple[tuple[str, ...], ValidationLayer]] = [
    (("lxml.", "xmlSchema", "xml.", "ioError", "FileNotLoadable"), ValidationLayer.XML),
    (("xbrl.", "xbrle."), ValidationLayer.XBRL_21),
    (("xbrldte", "xbrldie", "xbrldi"), ValidationLayer.DIMENSIONS),
    (("calc", "xbrl.5.2.5.2"), ValidationLayer.CALCULATION),
    (("message:", "formula:", "xbrlfe", "xfie", "valueAssertion"), ValidationLayer.FORMULA),
    (("EBA.", "EIOPA.", "filing"), ValidationLayer.FILING),
]

_SEVERITY_BY_LEVEL = {
    "critical": Severity.BLOCKING,
    "error": Severity.BLOCKING,
    "warning": Severity.WARNING,
    "info": Severity.INFO,
    "debug": Severity.INFO,
}


def categorise_layer(code: str) -> ValidationLayer:
    for prefixes, layer in _LAYER_PREFIXES:
        if code.startswith(prefixes):
            return layer
    return ValidationLayer.OTHER


def normalise(record: CapturedRecord) -> Finding:
    #turn one raw arelle log record into a finding
    concept = None
    context_ref = None
    for ref in record.refs:
        props = dict(ref.get("customAttributes", {}) or {})
        concept = concept or props.get("conceptQname")
        context_ref = context_ref or props.get("contextRef")
    return Finding(
        severity=_SEVERITY_BY_LEVEL.get(record.level, Severity.INFO),
        layer=categorise_layer(record.code),
        code=record.code or "unknown",
        message=record.message,
        concept=concept,
        context_ref=context_ref,
        source="arelle",
    )


def validate_instance(
    instance_path: Path,
    config: ValidatorConfig | None = None,
) -> ValidationReport:
    #Validate one instance and return the report
    config = config or ValidatorConfig()
    report = ValidationReport(instance=str(instance_path))

    loader = InstanceLoader(config)
    model_xbrl = None
    try:
        model_xbrl = loader.load(instance_path)

        loaded_ok = model_xbrl is not None and model_xbrl.modelDocument is not None
        if loaded_ok:
            manager = model_xbrl.modelManager
            manager.validate = True
            manager.validateCalcs = config.validate_calc
            manager.formulaOptions = FormulaOptions()
            manager.formulaOptions.formulaAction = (
                "run" if config.validate_formula else "none"
            )
            if config.disclosure_system:
                manager.disclosureSystem.select(config.disclosure_system)
            Validate.validate(model_xbrl)

        for record in loader.drain_records():
            report.findings.append(normalise(record))

        if loaded_ok:
            report.findings.extend(run_custom_rules(model_xbrl))
    finally:
        loader.close(model_xbrl)

    return report
