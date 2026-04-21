"""
disease_progression.models.registry - Model registry and factory pattern.

Provides a central registry that maps model names to their constructor
classes.  Downstream code (training scripts, evaluation pipelines) can
instantiate any registered model by name without hard-coding imports:

    >>> model = ModelRegistry.create("cox_ph", penalizer=0.1)
    >>> model = ModelRegistry.create("deepsurv", in_features=32, hidden=[64, 64])
    >>> model = ModelRegistry.create("survtrace", vocab_size=5000, d_model=128)

New models are registered automatically when their modules are imported,
or can be added manually via ``ModelRegistry.register()``.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Global model registry for disease progression models.

    All models are stored in a class-level dict keyed by name.  Each
    entry maps to a callable (typically a class) that returns a model
    instance when called with keyword arguments.
    """

    _registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        model_cls: Callable[..., Any],
        description: str = "",
        default_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a model class under the given name.

        Parameters
        ----------
        name : str
            Unique model identifier (e.g. ``"cox_ph"``, ``"deepsurv"``).
        model_cls : callable
            A class or factory function that, when called with keyword
            arguments, returns a model instance.
        description : str
            Human-readable description for the model card.
        default_params : dict, optional
            Default hyperparameters passed to the constructor when none
            are specified by the caller.
        """
        cls._registry[name] = {
            "cls": model_cls,
            "description": description,
            "default_params": default_params or {},
        }
        logger.debug("Registered model: %s", name)

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> Any:
        """Instantiate a registered model by name.

        Parameters
        ----------
        name : str
            Registered model name.
        **kwargs
            Constructor arguments.  Missing arguments are filled from
            the model's ``default_params``.

        Returns
        -------
        Model instance.

        Raises
        ------
        KeyError
            If ``name`` is not in the registry.
        """
        if name not in cls._registry:
            raise KeyError(
                f"Model '{name}' not found in registry.  "
                f"Available: {cls.list_models()}"
            )
        entry = cls._registry[name]
        merged = {**entry["default_params"], **kwargs}

        # Filter kwargs to only those accepted by the constructor
        model_cls = entry["cls"]
        sig = inspect.signature(model_cls)
        valid_params = set(sig.parameters.keys())
        if not any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        ):
            merged = {k: v for k, v in merged.items() if k in valid_params}

        return model_cls(**merged)

    @classmethod
    def list_models(cls) -> List[str]:
        """Return names of all registered models."""
        return list(cls._registry.keys())

    @classmethod
    def get_info(cls, name: str) -> Dict[str, Any]:
        """Return metadata for a registered model."""
        if name not in cls._registry:
            raise KeyError(f"Model '{name}' not found.")
        entry = cls._registry[name]
        return {
            "name": name,
            "class": entry["cls"].__name__ if hasattr(entry["cls"], "__name__") else str(entry["cls"]),
            "description": entry["description"],
            "default_params": entry["default_params"],
        }

    @classmethod
    def clear(cls) -> None:
        """Remove all registered models (useful in tests)."""
        cls._registry.clear()


def auto_register(
    name: str,
    description: str = "",
    default_params: Optional[Dict[str, Any]] = None,
) -> Callable:
    """Class decorator that auto-registers a model on import.

    Usage::

        @auto_register("cox_ph", description="Cox proportional hazards")
        class CoxPHModel:
            ...
    """

    def decorator(model_cls: Type) -> Type:
        ModelRegistry.register(
            name=name,
            model_cls=model_cls,
            description=description,
            default_params=default_params or {},
        )
        return model_cls

    return decorator
