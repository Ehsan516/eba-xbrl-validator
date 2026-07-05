from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ValidatorConfig(BaseModel):
    """how an instance is loaded and validated
    offline: if True, never touch the network; everything must resolve
    from packages or the cache for reproducible runs.
    validate_formula: run formula linkbase evaluation (the EBA business rules).
    """

    taxonomy_packages: list[Path] = Field(default_factory=list)
    cache_dir: Path | None = None
    offline: bool = True
    validate_formula: bool = True
    validate_calc: bool = True
    disclosure_system: str | None = None
