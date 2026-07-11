"""Local web UI + JSON endpoint for the validator"""

from __future__ import annotations

import tempfile
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from xbrlval.config import ValidatorConfig
from xbrlval.model import Severity, ValidationLayer, ValidationReport
from xbrlval.validate import validate_instance

app = FastAPI(title="EBA XBRL Validator")

_SEVERITY_STYLE = {
    Severity.BLOCKING: ("#b3261e", "blocking"),
    Severity.WARNING: ("#8a5a00", "warning"),
    Severity.INFO: ("#3b5a7a", "info"),
}

_PAGE_CSS = """
body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2.5rem auto; padding: 0 1.5rem; color: #1b1b1b; }
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
p.sub { color: #666; margin-top: 0; }
form { border: 1px solid #ddd; border-radius: 8px; padding: 1.25rem; margin-top: 1.5rem; }
label { display: block; font-weight: 600; margin-top: 1rem; }
label:first-child { margin-top: 0; }
input[type=file] { display: block; margin-top: 0.35rem; }
.hint { color: #777; font-size: 0.85rem; margin: 0.2rem 0 0; }
.checkline { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; }
.checkline label { margin: 0; font-weight: normal; }
button { margin-top: 1.25rem; padding: 0.55rem 1.4rem; border: none; border-radius: 6px;
         background: #1b6b3a; color: white; font-size: 1rem; cursor: pointer; }
button:hover { background: #155a30; }
.verdict { display: inline-block; padding: 0.15rem 0.6rem; border-radius: 5px; font-weight: 700; }
.verdict.valid { background: #e3f3e8; color: #1b6b3a; }
.verdict.invalid { background: #fbe9e7; color: #b3261e; }
.counts { color: #444; margin: 0.5rem 0 1.5rem; }
.layer { margin-top: 1.5rem; }
.layer h2 { font-size: 1rem; margin-bottom: 0.4rem; }
.finding { border-left: 4px solid #ccc; padding: 0.4rem 0.75rem; margin-bottom: 0.4rem; background: #fafafa; }
.finding .code { font-weight: 600; }
.finding .loc { color: #777; font-size: 0.85rem; }
.back { display: inline-block; margin-top: 1.5rem; color: #1b6b3a; text-decoration: none; }
"""


def _page(body: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>EBA XBRL Validator</title>
<style>{_PAGE_CSS}</style></head><body>{body}</body></html>"""


def _render_form(error: str | None = None) -> str:
    error_html = f'<p style="color:#b3261e">{escape(error)}</p>' if error else ""
    return _page(f"""
<h1>EBA XBRL Validator</h1>
<p class="sub">Upload an XBRL instance and check it against the EBA taxonomy and validation rules.</p>
{error_html}
<form action="/validate" method="post" enctype="multipart/form-data">
  <label for="instance">XBRL instance file</label>
  <input type="file" id="instance" name="instance" required>

  <label for="taxonomy_packages">Taxonomy package(s) <span class="hint">(optional, .zip)</span></label>
  <input type="file" id="taxonomy_packages" name="taxonomy_packages" multiple accept=".zip">
  <p class="hint">Leave empty to resolve from the local Arelle cache.</p>

  <label for="supporting_files">Supporting files <span class="hint">(optional)</span></label>
  <input type="file" id="supporting_files" name="supporting_files" multiple>
  <p class="hint">Any local schema/linkbase files the instance references by a relative path
     (not needed if it resolves entirely through a taxonomy package above).</p>

  <div class="checkline">
    <input type="checkbox" id="online" name="online" value="true">
    <label for="online">Allow network access to resolve the taxonomy</label>
  </div>
  <div class="checkline">
    <input type="checkbox" id="no_formula" name="no_formula" value="true">
    <label for="no_formula">Skip formula linkbase (business rule) evaluation</label>
  </div>

  <button type="submit">Validate</button>
</form>
""")


def _render_report(report: ValidationReport) -> str:
    counts = report.counts()
    verdict_class = "valid" if report.is_valid else "invalid"
    verdict_text = "VALID" if report.is_valid else "INVALID"

    layers_html = ""
    grouped = report.by_layer()
    for layer in ValidationLayer:
        findings = grouped.get(layer)
        if not findings:

            continue
        items = ""
        for f in findings:
            color, _ = _SEVERITY_STYLE[f.severity]
            location = ""
            if f.concept or f.context_ref:
                
                location = (
                    f'<div class="loc">{escape(f.concept or "?")} '
                    f'@ {escape(f.context_ref or "?")}</div>'
                )
            items += (
                f'<div class="finding" style="border-left-color:{color}">'
                f'<span class="code">{escape(f.code)}</span> — {escape(f.message)}'
                f"{location}</div>"
            )
        layers_html += f"""
<div class="layer">
  <h2>{escape(layer.value)} — {len(findings)} finding(s)</h2>
  {items}
</div>"""

    return _page(f"""
<h1>EBA XBRL Validator</h1>
<p><span class="verdict {verdict_class}">{verdict_text}</span></p>
<p class="counts">{escape(report.instance)} —
  {counts[Severity.BLOCKING]} blocking,
  {counts[Severity.WARNING]} warning,
  {counts[Severity.INFO]} info</p>
{layers_html or '<p>No findings.</p>'}
<a class="back" href="/">&larr; Validate another instance</a>
""")


async def _run_validation(
    instance: UploadFile,
    taxonomy_packages: list[UploadFile],
    supporting_files: list[UploadFile],
    online: bool,
    no_formula: bool,
) -> ValidationReport:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        instance_path = tmp_path / (instance.filename or "instance.xbrl")
        instance_path.write_bytes(await instance.read())

        for supporting in supporting_files:
            if not supporting.filename:

                continue
            (tmp_path / supporting.filename).write_bytes(await supporting.read())

        package_paths = []
        for pkg in taxonomy_packages:

            if not pkg.filename:
                continue
            pkg_path = tmp_path / pkg.filename
            pkg_path.write_bytes(await pkg.read())
            package_paths.append(pkg_path)

        config = ValidatorConfig(

            taxonomy_packages=package_paths,
            offline=not online,
            validate_formula=not no_formula,
        )
        return validate_instance(instance_path, config)


@app.get("/", response_class=HTMLResponse)
def index() -> str:

    return _render_form()


@app.post("/validate", response_class=HTMLResponse)
async def validate_form(
    instance: UploadFile = File(...),

    taxonomy_packages: list[UploadFile] = File(default=[]),
    supporting_files: list[UploadFile] = File(default=[]),
    online: bool = Form(False),
    no_formula: bool = Form(False),
) -> str:
    
    report = await _run_validation(
        instance, taxonomy_packages, supporting_files, online, no_formula
    )
    return _render_report(report)


@app.post("/api/validate")
async def validate_api(

    instance: UploadFile = File(...),

    taxonomy_packages: list[UploadFile] = File(default=[]),
    supporting_files: list[UploadFile] = File(default=[]),
    online: bool = Form(False),
    no_formula: bool = Form(False),

) -> dict:
    report = await _run_validation(
        instance, taxonomy_packages, supporting_files, online, no_formula
    )
    return report.model_dump(mode="json")
