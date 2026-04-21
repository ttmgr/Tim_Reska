"""
disease_progression.models - Survival and disease progression models.

Model zoo:
    - ``cox_deepsurv``: Classical Cox PH (lifelines) and DeepSurv (pycox).
    - ``deephit``: DeepHit / Dynamic-DeepHit for discrete-time survival
      with competing risks (pycox).
    - ``multistate``: Continuous-time Markov multistate model with
      transition intensity estimation and state occupation probabilities.
    - ``survtrace``: SurvTRACE-style transformer survival model with
      self-attention encoder and competing-risks survival head (PyTorch).
    - ``registry``: Model factory for instantiating models by name.
"""

from disease_progression.models.registry import ModelRegistry

__all__ = ["ModelRegistry"]
