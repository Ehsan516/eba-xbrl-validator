# eba-xbrl-validator

> A Python validation engine for EBA COREP/FINREP XBRL regulatory submissions, built on [Arelle](https://arelle.org).

This tool takes an XBRL instance — the file a bank or investment firm submits to a regulator — and checks it against the EBA taxonomy and the EBA validation rules, then produces a structured, categorised report of every issue found: what failed, which rule, where, and how serious.

It is built on top of Arelle, the open-source XBRL processor certified by XBRL International as a Validating Processor. Arelle does the specification-level heavy lifting (2.1, Dimensions, formula evaluation). The  project helps orchestrating the validation layers, normalising Arelle's raw output into a clean domain model, categorising findings by validation layer and severity, and a small custom rule layer for checks beyond the published formula linkbase.

> **Status: early development.** The repository is being built in phases (see [Roadmap](#roadmap)) so far. Sections describing usage reflect the target interface and are marked where not yet implemented.

---

## Background

Banks and investment firms across the EU report prudential and financial data to supervisors under two frameworks: **COREP** (Common Reporting — capital, own funds, risk exposures) and **FINREP** (Financial Reporting — balance sheet, P&L). These submissions are filed as **XBRL** instances validated against the **EBA taxonomy**.

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

| XML well-formedness | Is the file valid XML |
| XBRL 2.1 | Structurally valid XBRL |
| Dimensions 1.0 | Dimensional consistency |
| Calculation linkbase | Declared sums add up |
| Formula linkbase | EBA `vXXXX` business rules |
| Filing rules | EBA Filing Manual conformance (encoding, duplicate facts, `decimals` usage, filing-indicator coherence) |

For each layer, the tool captures every finding and emits a structured report (JSON and human-readable text) grouped by layer and severity, with the offending concept, context, and rule code attached.


## Tech stack

- **Python 3.11+**
- **[Arelle](https://arelle.org)** (`arelle-release`) — XBRL processing and spec-level validation
- **pydantic** — the report and finding domain model
- default command-line interface

## Roadmap

- [ ] **Phase 0** — Validate a sample instance by hand via the Arelle CLI; learn the moving parts
- [ ] **Phase 1** — Wrap Arelle's Python API; capture validation messages programmatically
- [ ] **Phase 2** — Define the report domain model; emit JSON and text
so far


## Acknowledgements

- [Arelle](https://arelle.org) — the open-source XBRL processor this project is built on
- The [European Banking Authority](https://www.eba.europa.eu) — publisher of the COREP/FINREP frameworks, taxonomies, and validation rules

## License

[MIT](LICENSE)
