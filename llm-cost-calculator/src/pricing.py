"""Load and query LLM pricing data from YAML configuration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "pricing_2026.yml"


@dataclass(frozen=True)
class APIModelPricing:
    """Pricing for an API-hosted model."""

    model_id: str
    display_name: str
    provider: str
    input_per_1m: float
    output_per_1m: float


@dataclass(frozen=True)
class SelfHostedModelPricing:
    """Pricing for a self-hosted model on rented GPUs."""

    model_id: str
    display_name: str
    provider: str
    gpu_cost_per_hour: float
    tokens_per_second: float
    overhead_fraction: float


ModelPricing = APIModelPricing | SelfHostedModelPricing


class PricingDatabase:
    """In-memory pricing catalog loaded from a YAML file."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._config_path = config_path or _DEFAULT_CONFIG
        self._models: dict[str, ModelPricing] = {}
        self._load()

    def _load(self) -> None:
        """Parse the YAML config and populate the model registry."""
        logger.info("Loading pricing from %s", self._config_path)
        with open(self._config_path, "r") as fh:
            data = yaml.safe_load(fh)

        for provider_key, provider_data in data["providers"].items():
            for model_id, model_data in provider_data["models"].items():
                if model_data["type"] == "api":
                    self._models[model_id] = APIModelPricing(
                        model_id=model_id,
                        display_name=model_data["display_name"],
                        provider=provider_data["display_name"],
                        input_per_1m=float(model_data["input_per_1m"]),
                        output_per_1m=float(model_data["output_per_1m"]),
                    )
                elif model_data["type"] == "self_hosted":
                    self._models[model_id] = SelfHostedModelPricing(
                        model_id=model_id,
                        display_name=model_data["display_name"],
                        provider=provider_data["display_name"],
                        gpu_cost_per_hour=float(model_data["gpu_cost_per_hour"]),
                        tokens_per_second=float(model_data["tokens_per_second"]),
                        overhead_fraction=float(model_data["overhead_fraction"]),
                    )
                else:
                    logger.warning("Unknown model type %r for %s", model_data["type"], model_id)

        logger.info("Loaded %d models", len(self._models))

    def get(self, model_id: str) -> ModelPricing:
        """Return pricing for a model, raising KeyError if not found."""
        if model_id not in self._models:
            available = ", ".join(sorted(self._models.keys()))
            raise KeyError(f"Model {model_id!r} not found. Available: {available}")
        return self._models[model_id]

    def list_models(self) -> list[str]:
        """Return all available model identifiers."""
        return sorted(self._models.keys())

    def list_api_models(self) -> list[str]:
        """Return model identifiers for API-hosted models only."""
        return sorted(
            mid for mid, m in self._models.items() if isinstance(m, APIModelPricing)
        )

    def list_self_hosted_models(self) -> list[str]:
        """Return model identifiers for self-hosted models only."""
        return sorted(
            mid for mid, m in self._models.items() if isinstance(m, SelfHostedModelPricing)
        )
