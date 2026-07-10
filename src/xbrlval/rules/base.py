"""adding a rule is one class in custom_rules.py with no wiring elsewhere
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol

from arelle.ModelXbrl import ModelXbrl

from xbrlval.model import Finding


class Rule(Protocol):
    rule_id: str
    description: str

    def check(self, model_xbrl: ModelXbrl) -> Iterator[Finding]: ...


_REGISTRY: list[Rule] = []


def rule(cls: type) -> type:
    """Class decorator: instantiate and register a rule."""
    _REGISTRY.append(cls())
    return cls


def all_rules() -> Iterable[Rule]:
    return tuple(_REGISTRY)
