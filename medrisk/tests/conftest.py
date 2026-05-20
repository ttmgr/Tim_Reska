"""Shared test fixtures for MedRisk."""

import pytest


@pytest.fixture
def rng():
    """Reproducible random state for tests."""
    import numpy as np

    return np.random.default_rng(42)
