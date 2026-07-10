# eba-xbrl-validator

> A Python validation engine for EBA COREP/FINREP XBRL regulatory submissions, built on [Arelle](https://arelle.org).

This tool takes an XBRL instance, the file a bank or investment firm submits to a regulator and checks it against the EBA taxonomy and the EBA validation rules, then produces a structured, categorised report of every issue found: what failed, which rule, where, and how serious.

It is built on top of Arelle, the open-source XBRL processor certified by XBRL International as a Validating Processor. Arelle does the specification-level heavy lifting (XBRL 2.1, Dimensions, formula evaluation). The value this project adds sits around that core: orchestrating the validation layers, normalising Arelle's raw output into a clean domain model, categorising findings by validation layer and severity, and a small custom rule layer for checks beyond the published formula linkbase.

> **Status: early development.** The repository is being built in phases (see [Roadmap](#roadmap)). Sections describing usage reflect the target interface and are marked where not yet implemented.

---

## Background

Banks and investment firms across the EU report prudential and financial data to supervisors under two frameworks: **COREP** (Common Reporting capital, own funds, risk exposures) and **FINREP** (Financial Reporting, balance sheet, P&L). These submissions are filed as **XBRL** instances validated against the **EBA taxonomy**.

A few terms used throughout this project:

- **Instance** — the actual data file submitted. Contains *facts*.
- **Fact** — a single reported value (e.g. "Tier 1 capital = €5,000,000"), tied to a *concept* and a *context*.
- **Concept** — what is being reported, as defined in the taxonomy.
- **Context** — the entity, reporting period, and dimensional breakdown a fact applies to.
- **Taxonomy / DTS** — the schema and linkbases defining the vocabulary, relationships, and validation rules. The instance reports against an *entry point* within it.
- **Filing indicators** — EBA-specific flags declaring which templates are being reported; they drive which validation rules apply.
- **Validation rule** — a business check (e.g. row A = row B + row C), identified by codes like `v0001_m`, encoded in the taxonomy's *formula linkbase*.

## What it does

Validation runs in layers, from cheap and structural to expensive and semantic:

| Layer | Checks |
|-------|--------|
| XML well-formedness | Is the file valid XML |
| XBRL 2.1 | Structurally valid XBRL |
| Dimensions 1.0 | Dimensional consistency |
| Calculation linkbase | Declared sums add up |
| Formula linkbase | EBA `vXXXX` business rules |
| Filing rules | EBA Filing Manual conformance (encoding, duplicate facts, `decimals` usage, filing-indicator coherence) |

For each layer, the tool captures every finding and emits a structured report (JSON and human-readable text) grouped by layer and severity, with the offending concept, context, and rule code attached.

## Architecture

```
instance.xbrl ──▶ loader ──▶ Arelle (load + validate) ──▶ findings capture
                                                              │
                                          normalise into domain model
                                                              │
                                   categorise by layer + severity, enrich rule codes
                                                              │
                                        custom rule layer (project-specific checks)
                                                              │
                                              report (JSON / text / HTML)
```

## Tech stack

- **Python 3.11+**
- **[Arelle](https://arelle.org)** (`arelle-release`) — XBRL processing and spec-level validation
- **pydantic** — the report and finding domain model
- **typer** — command-line interface
- **FastAPI** *(optional)* — HTTP validation endpoint
- **pytest** — test suite over known-good and known-bad instance fixtures


## Getting started

### Prerequisites

- Python 3.11 or later
- An EBA taxonomy package and at least one sample instance (see below)

### Installation

```bash
git clone https://github.com/<your-username>/eba-xbrl-validator.git
cd eba-xbrl-validator
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### Getting taxonomy and sample data

Validation requires the EBA taxonomy locally. From the EBA *Reporting frameworks* page, choose a framework release and download:

- the **XBRL taxonomy files** package
- the **Skeleton Instances** package (sample instances, useful as test fixtures)
- the **validation rules** spreadsheet and **DPM** documents (reference)
- the **Filing Manual** (defines the filing rules)

Place taxonomy packages under `taxonomies/` and sample instances under `data/samples/`. Both are git-ignored, as taxonomy packages are large.

try start with the smallest single module/template available rather than a full framework, the complete taxonomies are large and slow to load.

## Usage

> *Target interface — implemented incrementally across the roadmap phases.*

```bash
# Validate an instance and print a report
eba-xbrl-validator validate data/samples/instance.xbrl

# Emit a JSON report
eba-xbrl-validator validate data/samples/instance.xbrl --format json --out report.json
```

## Project structure

```
eba-xbrl-validator/
├── src/xbrlval/
│   ├── config.py        # taxonomy paths, cache dir, disclosure system
│   ├── loader.py        # loads instance, resolves the taxonomy (DTS)
│   ├── validate.py      # runs validation layers, captures Arelle output
│   ├── model.py         # ValidationReport, Finding, Severity (pydantic)
│   ├── report.py        # JSON / text / HTML rendering
│   ├── rules/           # custom rule layer
│   ├── cli.py           # typer entrypoint
│   └── api.py           # optional FastAPI endpoint
├── tests/
│   └── fixtures/        # valid + deliberately broken instances
├── taxonomies/          # EBA taxonomy packages (git-ignored)
└── data/samples/        # sample instances
```

## Acknowledgements

- [Arelle](https://arelle.org) — the open-source XBRL processor this project is built on
- The [European Banking Authority](https://www.eba.europa.eu) — publisher of the COREP/FINREP frameworks, taxonomies, and validation rules

## License

[MIT](LICENSE)
