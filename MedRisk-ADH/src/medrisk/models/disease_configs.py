"""Disease-specific CTMC configurations for MedRisk-ADH.

Provides a registry of pre-configured disease progression models. Each
DiseaseConfig packages state definitions, transition intensities, and
metadata needed to instantiate a MultistateModel for a specific disease.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from medrisk.models.multistate import MultistateModel


@dataclass(frozen=True)
class DiseaseConfig:
    """Configuration for a disease-specific CTMC model.

    Attributes:
        name: Disease identifier (e.g., "cardiovascular", "alzheimer").
        n_states: Number of states in the Markov chain.
        state_names: Mapping from state index to human-readable name.
        absorbing_states: Set of absorbing state indices.
        allowed_transitions: List of (from, to) state pairs.
        default_intensities: Default transition intensity values.
        event_types: Possible event types for this disease.
        colors: RGBA fill colors for chart rendering (one per state).
        line_colors: Hex line colors for chart rendering (one per state).
    """

    name: str
    n_states: int
    state_names: dict[int, str]
    absorbing_states: frozenset[int]
    allowed_transitions: list[tuple[int, int]]
    default_intensities: dict[tuple[int, int], float]
    event_types: list[str]
    colors: list[str] = field(default_factory=list)
    line_colors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cardiovascular (wraps existing constants from multistate.py / synthetic.py)
# ---------------------------------------------------------------------------

CARDIOVASCULAR_CONFIG = DiseaseConfig(
    name="cardiovascular",
    n_states=5,
    state_names={
        0: "Healthy",
        1: "Risk factors",
        2: "Chronic condition",
        3: "Complication",
        4: "Major event",
    },
    absorbing_states=frozenset({4}),
    allowed_transitions=[
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 3),
        (2, 4),
        (3, 4),
    ],
    default_intensities={
        (0, 1): 0.08,
        (1, 2): 0.06,
        (1, 0): 0.02,
        (2, 3): 0.04,
        (3, 4): 0.03,
        (2, 4): 0.01,
    },
    event_types=["death", "mi", "stroke", "hf", "ckd_progression"],
    colors=[
        "rgba(72, 187, 120, 0.5)",   # green
        "rgba(66, 153, 225, 0.5)",    # blue
        "rgba(237, 137, 54, 0.5)",    # orange
        "rgba(229, 62, 62, 0.5)",     # red
        "rgba(26, 32, 44, 0.5)",      # dark
    ],
    line_colors=["#48bb78", "#4299e1", "#ed8936", "#e53e3e", "#1a202c"],
)


# ---------------------------------------------------------------------------
# Alzheimer's Disease
# ---------------------------------------------------------------------------
# States follow clinical staging:
#   0: Normal Cognition (NC)
#   1: Subjective Cognitive Decline (SCD)
#   2: Mild Cognitive Impairment (MCI)
#   3: Mild Alzheimer's Disease
#   4: Moderate Alzheimer's Disease
#   5: Severe Alzheimer's Disease
#   6: Death (absorbing)
#
# Transition rates calibrated to published literature:
#   - MCI to mild AD: ~15% annual conversion (Petersen et al., NEJM 2018)
#   - Mild to moderate AD: ~4 year mean sojourn (Brookmeyer et al.)
#   - Moderate to severe AD: ~3 year mean sojourn
#   - Severe AD to death: ~2 year mean survival
# ---------------------------------------------------------------------------

ALZHEIMER_CONFIG = DiseaseConfig(
    name="alzheimer",
    n_states=7,
    state_names={
        0: "Normal Cognition",
        1: "Subjective Cognitive Decline",
        2: "Mild Cognitive Impairment",
        3: "Mild AD",
        4: "Moderate AD",
        5: "Severe AD",
        6: "Death",
    },
    absorbing_states=frozenset({6}),
    allowed_transitions=[
        (0, 1),  # NC -> SCD
        (1, 2),  # SCD -> MCI
        (2, 3),  # MCI -> Mild AD
        (3, 4),  # Mild -> Moderate AD
        (4, 5),  # Moderate -> Severe AD
        (5, 6),  # Severe AD -> Death
        (3, 6),  # Mild AD -> Death (competing risk)
        (4, 6),  # Moderate AD -> Death (competing risk)
    ],
    default_intensities={
        (0, 1): 0.04,   # NC -> SCD: ~25yr mean sojourn
        (1, 2): 0.08,   # SCD -> MCI: ~12yr mean sojourn
        (2, 3): 0.15,   # MCI -> Mild AD: ~6-7yr (15% annual conversion)
        (3, 4): 0.25,   # Mild -> Moderate: ~4yr mean sojourn
        (4, 5): 0.33,   # Moderate -> Severe: ~3yr mean sojourn
        (5, 6): 0.50,   # Severe -> Death: ~2yr mean survival
        (3, 6): 0.02,   # Mild AD direct mortality
        (4, 6): 0.05,   # Moderate AD direct mortality
    },
    event_types=["death", "institutionalization", "cognitive_decline"],
    colors=[
        "rgba(72, 187, 120, 0.5)",    # green — normal cognition
        "rgba(144, 205, 244, 0.5)",   # light blue — SCD
        "rgba(66, 153, 225, 0.5)",    # blue — MCI
        "rgba(237, 187, 54, 0.5)",    # yellow — mild AD
        "rgba(237, 137, 54, 0.5)",    # orange — moderate AD
        "rgba(229, 62, 62, 0.5)",     # red — severe AD
        "rgba(26, 32, 44, 0.5)",      # dark — death
    ],
    line_colors=[
        "#48bb78", "#90cdf4", "#4299e1", "#edbb36",
        "#ed8936", "#e53e3e", "#1a202c",
    ],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DISEASE_REGISTRY: dict[str, DiseaseConfig] = {
    "cardiovascular": CARDIOVASCULAR_CONFIG,
    "alzheimer": ALZHEIMER_CONFIG,
}


def build_model(config: DiseaseConfig) -> MultistateModel:
    """Create a MultistateModel from a DiseaseConfig with default intensities.

    Args:
        config: Disease configuration.

    Returns:
        A fitted MultistateModel ready for inference.
    """
    model = MultistateModel(
        allowed_transitions=config.allowed_transitions,
        n_states=config.n_states,
        absorbing_states=set(config.absorbing_states),
        state_names=dict(config.state_names),
    )
    model.set_intensities(dict(config.default_intensities))
    return model
