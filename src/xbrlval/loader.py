"""Loading XBRL instances through arelle
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from arelle import Cntlr, FileSource, PackageManager
from arelle.ModelXbrl import ModelXbrl

from xbrlval.config import ValidatorConfig


@dataclass
class CapturedRecord:
    #raw log record emitted by arelle during load/validation

    level: str
    code: str
    message: str
    refs: list[dict[str, Any]] = field(default_factory=list)


class _BufferHandler(logging.Handler):
    #collects arelle log records instead of printing

    def __init__(self) -> None:
        super().__init__()
        self.records: list[CapturedRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(
            CapturedRecord(
                level=record.levelname.lower(),
                code=getattr(record, "messageCode", "") or "",
                message=record.getMessage(),
                refs=list(getattr(record, "refs", []) or []),
            )
        )


class InstanceLoader:
#Owns an Arelle controller and loads instances with log capture

    def __init__(self, config: ValidatorConfig | None = None) -> None:
        self.config = config or ValidatorConfig()
        self.cntlr = Cntlr.Cntlr(logFileName="logToBuffer")
        if self.config.cache_dir is not None:
            self.cntlr.webCache.cacheDir = str(self.config.cache_dir)
        self.cntlr.webCache.workOffline = self.config.offline
        self.cntlr.startLogging(logFileName="logToBuffer")
        self._handler = _BufferHandler()
        self.cntlr.logger.addHandler(self._handler)
        self._load_packages()

    def _load_packages(self) -> None:

        PackageManager.init(self.cntlr, loadPackagesConfig=False)
        for pkg in self.config.taxonomy_packages:
            info = PackageManager.addPackage(self.cntlr, str(pkg))
            if not info:

                raise FileNotFoundError(f"Could not load taxonomy package: {pkg}")
        if self.config.taxonomy_packages:
            PackageManager.rebuildRemappings(self.cntlr)

    def load(self, instance_path: Path) -> ModelXbrl:
        #load an instance document, raises if the file doesn't exist
        if not instance_path.exists():
            raise FileNotFoundError(instance_path)
        source = FileSource.openFileSource(str(instance_path), self.cntlr)
        model_xbrl = self.cntlr.modelManager.load(source)
        return model_xbrl

    def drain_records(self) -> list[CapturedRecord]:
        #return and clear everything captured so far
        records, self._handler.records = self._handler.records, []
        return records

    def close(self, model_xbrl: ModelXbrl | None = None) -> None:
        if model_xbrl is not None:
            model_xbrl.close()
        self.cntlr.logger.removeHandler(self._handler)
