"""
_settings.py — Application settings loaded from environment variables and YAML config files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    config_dir: Path = Field(default=Path("configs"))
    cache_dir: Path = Field(default=Path(".cache/medrisk_fetch"))
    log_level: str = "INFO"
    log_file: Path | None = None

    model_config = {"env_prefix": "MEDRISK_FETCH_", "env_file": ".env", "extra": "ignore"}

    # Lazily loaded YAML data
    _sources_data: dict | None = None
    _studies_data: dict | None = None
    _filters_data: dict | None = None

    def sources(self) -> dict:
        if self._sources_data is None:
            self._sources_data = self._load_yaml("sources.yml")
        return self._sources_data  # type: ignore[return-value]

    def studies(self) -> dict:
        if self._studies_data is None:
            self._studies_data = self._load_yaml("studies.yml")
        return self._studies_data  # type: ignore[return-value]

    def filters(self) -> dict:
        if self._filters_data is None:
            self._filters_data = self._load_yaml("filters.yml")
        return self._filters_data  # type: ignore[return-value]

    def _load_yaml(self, filename: str) -> dict:
        path = self.config_dir / filename
        if not path.exists():
            return {}
        with open(path) as fh:
            return yaml.safe_load(fh) or {}

    def configure_logging(self) -> None:
        handlers: list[Any] = [logging.StreamHandler()]
        if self.log_file:
            handlers.append(logging.FileHandler(self.log_file))
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            handlers=handlers,
        )
