"""YAML config loaders for the models sub-package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Default config directory relative to this file's package root
_PKG_ROOT = Path(__file__).parent.parent.parent.parent  # repo root
_CONFIG_DIR = _PKG_ROOT / "configs"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_insurance_config(config_dir: Path | None = None) -> dict[str, Any]:
    """Load configs/insurance_de.yml."""
    base = Path(config_dir) if config_dir else _CONFIG_DIR
    return _load_yaml(base / "insurance_de.yml")


def load_icd_sick_leave(config_dir: Path | None = None) -> dict[str, Any]:
    """Load configs/icd_sick_leave.yml."""
    base = Path(config_dir) if config_dir else _CONFIG_DIR
    return _load_yaml(base / "icd_sick_leave.yml")
