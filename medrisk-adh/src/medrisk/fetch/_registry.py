"""
_registry.py — Decorator-based adapter registry.

Usage:
    @register
    class MyAdapter(AbstractAdapter):
        source_name = "my_source"
        ...

    cls = get_adapter_class("my_source")
"""

from __future__ import annotations

from medrisk.fetch.adapters.base import AbstractAdapter

_REGISTRY: dict[str, type[AbstractAdapter]] = {}


def register(cls: type[AbstractAdapter]) -> type[AbstractAdapter]:
    """Register an adapter class by its source_name. Used as a class decorator."""
    _REGISTRY[cls.source_name] = cls
    return cls


def get_adapter_class(source_name: str) -> type[AbstractAdapter]:
    if source_name not in _REGISTRY:
        raise KeyError(
            f"No adapter registered for source '{source_name}'. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[source_name]


def list_sources() -> list[str]:
    """Return sorted list of registered source names."""
    return sorted(_REGISTRY)
