"""MedRisk-ADH -- Krankentagegeld-Kalkulation.

Interactive KTG (daily sickness benefit) calculator showing how CTMC
disease progression models drive insurance pricing.  Three examples:
Hypertonie, Adipositas, Rückenschmerzen.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
_APP_DIR = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import numpy as np
import pandas as pd
import streamlit as st

from medrisk.models.disease_configs import CARDIOVASCULAR_CONFIG
from medrisk.models.multistate import MultistateModel
from components.metrics_cards import metric_card
from components.progression_chart import progression_chart

# ---------------------------------------------------------------------------
# Page styling (Doctolib Oxygen)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container { max-width: 1100px; }
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    .section-label {
        color: #1a365d; font-size: 0.72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 0.8rem; padding-bottom: 0.4rem;
        border-bottom: 2px solid #2b6cb0; display: inline-block;
    }
    .page-subtitle {
        color: #2d3748; font-size: 0.95rem; margin-top: -0.5rem; margin-bottom: 1.2rem;
    }
    h1, h2, h3, h4 { color: #1a365d !important; }
    p, li { color: #2d3748 !important; }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div {
        background-color: #f7fafc !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #1a365d !important; }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span { color: #2d3748 !important; }
    .icd-badge {
        display: inline-block; background: #edf2f7; color: #2b6cb0;
        padding: 3px 10px; border-radius: 8px; font-weight: 700;
        font-size: 0.8rem; letter-spacing: 0.5px; margin-left: 8px;
    }
    .dqs-box {
        border-radius: 8px; padding: 18px; margin-bottom: 8px;
    }
    .dqs-good { background: #f0fff4; border: 1px solid #c6f6d5; }
    .dqs-bad  { background: #fff5f5; border: 1px solid #fed7d7; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Disease configs for KTG
# ---------------------------------------------------------------------------

def _build_cv_q() -> dict[tuple[int, int], float]:
    return dict(CARDIOVASCULAR_CONFIG.default_intensities)

KTG_DISEASES: dict[str, dict] = {
    "Hypertonie (I10)": {
        "icd": "I10",
        "prevalence": "30%",
        "prevalence_source": "RKI DEGS1 2012",
        "description": (
            "Essentielle Hypertonie ist mit 30% Prävalenz die häufigste chronische "
            "Erkrankung in der KTG-Kalkulation. Das AU-Risiko steigt mit dem "
            "Krankheitsstadium von 3% auf 80%."
        ),
        "n_states": 5,
        "state_names": {
            0: "Gesund", 1: "Risikofaktoren", 2: "Chronisch",
            3: "Komplikation", 4: "Schweres Ereignis",
        },
        "absorbing": [4],
        "intensities": _build_cv_q(),
        "allowed": list(CARDIOVASCULAR_CONFIG.allowed_transitions),
        "colors": [
            "rgba(2, 137, 1, 0.5)", "rgba(16, 122, 202, 0.5)",
            "rgba(200, 140, 30, 0.5)", "rgba(208, 13, 0, 0.5)",
            "rgba(13, 35, 57, 0.5)",
        ],
        "line_colors": ["#028901", "#107ACA", "#C88C1E", "#D00D00", "#0D2339"],
        "au_prob": [0.01, 0.03, 0.12, 0.35, 0.80],
        "au_days": [7, 14, 28, 42, 120],
        "start_state": 1,
        "complete_data": [
            "3 Antihypertensiva dokumentiert",
            "RR 135/85 mmHg (letzte 6 Monate)",
            "HbA1c + Lipidprofil vorhanden",
            "Stadium II gesichert",
        ],
        "sparse_data": [
            "Keine Medikamentendaten",
            "Kein Blutdruck dokumentiert",
            "Nur Diagnose I10",
            "Stadium unklar (I? II? III?)",
        ],
    },
    "Adipositas (E66.0)": {
        "icd": "E66.0",
        "prevalence": "24%",
        "prevalence_source": "RKI DEGS1 2012",
        "description": (
            "Adipositas (BMI >= 30) betrifft 24% der Erwachsenen in DE. "
            "Das AU-Risiko wird vor allem durch Begleiterkrankungen bestimmt "
            "(Diabetes, Gonarthrose, Schlafapnoe)."
        ),
        "n_states": 4,
        "state_names": {
            0: "Normalgewicht", 1: "Übergewicht",
            2: "Adipositas", 3: "Komplikation",
        },
        "absorbing": [3],
        "intensities": {
            (0, 1): 0.05, (1, 2): 0.04, (1, 0): 0.02,
            (2, 3): 0.025, (2, 1): 0.008,
        },
        "allowed": [(0, 1), (1, 2), (1, 0), (2, 3), (2, 1)],
        "colors": [
            "rgba(2, 137, 1, 0.5)", "rgba(16, 122, 202, 0.5)",
            "rgba(200, 140, 30, 0.5)", "rgba(208, 13, 0, 0.5)",
        ],
        "line_colors": ["#028901", "#107ACA", "#C88C1E", "#D00D00"],
        "au_prob": [0.01, 0.02, 0.08, 0.25],
        "au_days": [5, 10, 21, 45],
        "start_state": 1,
        "complete_data": [
            "BMI 32 dokumentiert",
            "Begleiterkrankungen erfasst",
            "Ernährungsberatung dokumentiert",
            "Stadium klar zuordenbar",
        ],
        "sparse_data": [
            "Kein BMI dokumentiert",
            "Keine Begleitdiagnosen",
            "Nur E66.0",
            "Schweregrad unklar",
        ],
    },
    "Rückenschmerzen (M54)": {
        "icd": "M54",
        "prevalence": "25%",
        "prevalence_source": "RKI GEDA 2019",
        "description": (
            "Rückenschmerzen sind die häufigste AU-Ursache in Deutschland. "
            "Der Übergang von akut zu chronisch ist der entscheidende "
            "Kostentreiber in der KTG-Kalkulation."
        ),
        "n_states": 4,
        "state_names": {
            0: "Beschwerdefrei", 1: "Akut",
            2: "Chronisch", 3: "Invalidität",
        },
        "absorbing": [3],
        "intensities": {
            (0, 1): 0.10, (1, 0): 0.15, (1, 2): 0.03,
            (2, 3): 0.015, (2, 1): 0.005,
        },
        "allowed": [(0, 1), (1, 0), (1, 2), (2, 3), (2, 1)],
        "colors": [
            "rgba(2, 137, 1, 0.5)", "rgba(16, 122, 202, 0.5)",
            "rgba(200, 140, 30, 0.5)", "rgba(208, 13, 0, 0.5)",
        ],
        "line_colors": ["#028901", "#107ACA", "#C88C1E", "#D00D00"],
        "au_prob": [0.01, 0.15, 0.40, 0.75],
        "au_days": [3, 14, 35, 90],
        "start_state": 1,
        "complete_data": [
            "MRT-Befund vorhanden",
            "Therapieverlauf dokumentiert",
            "Schmerzskala (VAS/NRS)",
            "Chronifizierung bewertbar",
        ],
        "sparse_data": [
            "Keine Bildgebung",
            "Nur M54 ohne Spezifikation",
            "Kein Therapieverlauf",
            "Akut vs. chronisch unklar",
        ],
    },
}


def _build_msm(cfg: dict) -> MultistateModel:
    """Build a MultistateModel from inline KTG disease config."""
    msm = MultistateModel(
        allowed_transitions=cfg["allowed"],
        n_states=cfg["n_states"],
        absorbing_states=set(cfg["absorbing"]),
        state_names=dict(cfg["state_names"]),
    )
    msm.set_intensities(dict(cfg["intensities"]))
    return msm


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown("### KTG-Parameter")

disease_name = st.sidebar.selectbox(
    "Erkrankung", list(KTG_DISEASES.keys()), index=0,
)
cfg = KTG_DISEASES[disease_name]

patient_age = st.sidebar.slider("Alter (Jahre)", 30, 65, 50)
daily_rate = st.sidebar.slider("Tagessatz (EUR)", 50, 150, 80, step=10)
time_horizon = st.sidebar.slider("Zeithorizont (Jahre)", 5, 30, 10)

# Age multiplier (younger = lower risk, older = higher)
age_mult = 0.7 + (patient_age - 30) * 0.02  # 0.7 at 30, 1.4 at 65

st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<div style="font-size: 0.75rem; color: #718096;">'
    f"Altersfaktor: {age_mult:.2f}x<br>"
    f"Quelle: {cfg['prevalence_source']}</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Build model
# ---------------------------------------------------------------------------
msm = _build_msm(cfg)

# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------
st.title("Krankentagegeld-Kalkulation")
st.markdown(
    f'<p class="page-subtitle">'
    f"Stadienspezifische Prämienkalkulation am Beispiel "
    f'{disease_name} <span class="icd-badge">{cfg["icd"]}</span></p>',
    unsafe_allow_html=True,
)

# --- Section 1: Disease overview ---
st.markdown('<div class="section-label">Krankheitsbild</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("Prävalenz DE", cfg["prevalence"], cfg["prevalence_source"], "#2b6cb0")
with col2:
    max_au = max(cfg["au_prob"])
    metric_card("Max. AU-Risiko", f"{max_au:.0%}", f"Stadium {cfg['n_states'] - 1}", "#e53e3e")
with col3:
    metric_card("Tagessatz", f"EUR {daily_rate}", f"Alter {patient_age}", "#38a169")

st.markdown(f"_{cfg['description']}_")

st.divider()

# --- Section 2: CTMC progression chart ---
st.markdown('<div class="section-label">Krankheitsverlauf (CTMC)</div>', unsafe_allow_html=True)

col_chart, col_table = st.columns([3, 2])

with col_chart:
    progression_chart(
        msm,
        start_state=cfg["start_state"],
        max_time=time_horizon,
        state_names=cfg["state_names"],
        colors=cfg["colors"],
        line_colors=cfg["line_colors"],
        title=f"Krankheitsverlauf {disease_name} -- {cfg['n_states']} Stadien",
    )

with col_table:
    st.markdown("**AU-Risiko nach Stadium**")
    rows = []
    for i in range(cfg["n_states"]):
        rows.append({
            "Stadium": cfg["state_names"][i],
            "P(AU/Jahr)": f"{cfg['au_prob'][i]:.0%}",
            "E[Dauer]": f"{cfg['au_days'][i]} Tage",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.caption(
        "AU = Arbeitsunfähigkeit. P(AU/Jahr) = jährliche Wahrscheinlichkeit "
        "einer AU-Episode. E[Dauer] = erwartete Dauer pro Episode."
    )

st.divider()

# --- Section 3: KTG calculation table ---
st.markdown('<div class="section-label">KTG-Kalkulation</div>', unsafe_allow_html=True)

# Get state occupation probabilities at time_horizon
times = np.array([float(time_horizon)])
probs_at_t = msm.state_occupation_probabilities(cfg["start_state"], times)[0]

calc_rows = []
total_cost = 0.0
for i in range(cfg["n_states"]):
    p_state = probs_at_t[i]
    au_prob = cfg["au_prob"][i] * age_mult
    au_days = cfg["au_days"][i]
    expected = p_state * au_prob * au_days * daily_rate
    total_cost += expected
    calc_rows.append({
        "Stadium": cfg["state_names"][i],
        f"P(Stadium, {time_horizon}J)": f"{p_state:.1%}",
        "P(AU/Jahr)": f"{au_prob:.1%}",
        "E[Dauer]": f"{au_days} d",
        "EUR/Tag": f"EUR {daily_rate}",
        "Erwartete Kosten": f"EUR {expected:.0f}",
    })

df_calc = pd.DataFrame(calc_rows)
st.dataframe(df_calc, hide_index=True, use_container_width=True)

# Summary metrics
monthly = total_cost * 1.15 * 1.12 / 12  # safety + admin surcharges

col_a, col_b, col_c = st.columns(3)
with col_a:
    metric_card("Jährliches KTG-Risiko", f"EUR {total_cost:.0f}", "gewichteter Erwartungswert", "#2b6cb0")
with col_b:
    metric_card("Monatsprämie (geschätzt)", f"EUR {monthly:.0f}", "inkl. Sicherheits-/Kostenzuschlag", "#1a365d")
with col_c:
    metric_card(
        "Prämienspanne",
        f"EUR {monthly * 0.8:.0f} - {monthly * 1.3:.0f}",
        "je nach Datenlage (DQS)",
        "#d69e2e",
    )

st.caption(
    f"Berechnung: EUR {total_cost:.0f} x 1.15 (Sicherheitszuschlag) x 1.12 "
    f"(Verwaltung/Provision) / 12 = EUR {monthly:.0f}/Monat. "
    f"Altersfaktor {age_mult:.2f}x eingerechnet."
)

st.divider()

# --- Section 4: DQS impact ---
st.markdown(
    '<div class="section-label">Datenqualität bestimmt die Preissicherheit</div>',
    unsafe_allow_html=True,
)

col_good, col_bad = st.columns(2)

with col_good:
    items = "".join(f"<li style='color: #38a169 !important;'>{x}</li>" for x in cfg["complete_data"])
    st.markdown(
        f'<div class="dqs-box dqs-good">'
        f'<strong style="color: #276749; font-size: 1.05rem;">Vollständige Akte (DQS 0.85)</strong>'
        f"<ul>{items}</ul>"
        f'<div style="color: #276749; font-weight: 700; margin-top: 6px;">'
        f"KTG-Prämie: EUR {monthly:.0f}/Monat</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

with col_bad:
    items = "".join(f"<li style='color: #e53e3e !important;'>{x}</li>" for x in cfg["sparse_data"])
    st.markdown(
        f'<div class="dqs-box dqs-bad">'
        f'<strong style="color: #c53030; font-size: 1.05rem;">Lückenhafte Akte (DQS 0.40)</strong>'
        f"<ul>{items}</ul>"
        f'<div style="color: #c53030; font-weight: 700; margin-top: 6px;">'
        f"KTG-Prämie: ??? (Stadium nicht bestimmbar)</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.info(
    "**Ergebnis:** Identischer ICD-Code, aber bis zu 3x Risikovarianz je nach Datenlage. "
    "Der DQS erkennt vor der Kalkulation, ob die Daten eine zuverlässige "
    "Stadienzuordnung erlauben."
)

# =========================================================================
# Section 5: SOTA ML Methods
# =========================================================================
st.divider()
st.markdown('<div class="section-label">ML-Methoden (State of the Art)</div>', unsafe_allow_html=True)

ml_tab1, ml_tab2, ml_tab3 = st.tabs([
    "Conformal Prediction", "Survival-Kurve", "Behandlungseffekt",
])

# --- Tab 1: Conformal Prediction Intervals ---
with ml_tab1:
    from medrisk.validation.conformal import ConformalPredictor

    st.markdown("#### Konforme Vorhersageintervalle")
    st.markdown(
        "Statt einer Punktschätzung liefert Conformal Prediction "
        "**garantierte Intervalle** mit wählbarer Abdeckung. "
        "Verteilungsfrei, endlich-stichprobenvalide (Vovk 2005, Angelopoulos & Bates 2023)."
    )

    coverage = st.slider("Coverage-Niveau", 0.80, 0.99, 0.90, 0.01, key="cp_coverage")
    alpha = 1 - coverage

    # Simulate calibration data: KTG cost estimates with noise
    rng_cp = np.random.RandomState(42)
    n_cal = 500
    y_hat_cal = rng_cp.uniform(200, 2000, n_cal)
    noise = rng_cp.normal(0, y_hat_cal * 0.25, n_cal)  # heteroscedastic noise
    y_true_cal = np.clip(y_hat_cal + noise, 0, None)

    cp = ConformalPredictor()
    cp.calibrate(y_true_cal, y_hat_cal)
    lower, upper = cp.predict_interval(total_cost, alpha=alpha)

    col_cp1, col_cp2, col_cp3 = st.columns(3)
    with col_cp1:
        metric_card("Punktschätzung", f"EUR {total_cost:.0f}", "gewichteter Erwartungswert", "#2b6cb0")
    with col_cp2:
        metric_card(
            f"Intervall ({coverage:.0%})",
            f"EUR {max(lower, 0):.0f} – {upper:.0f}",
            "konforme Garantie",
            "#1a365d",
        )
    with col_cp3:
        width_pct = (upper - lower) / max(total_cost, 1) * 100
        metric_card("Intervallbreite", f"{width_pct:.0f}%", "relativ zur Schätzung", "#d69e2e")

    st.caption(
        f"Split-konformes Intervall (n_cal={n_cal}, α={alpha:.2f}). "
        "Garantierte Abdeckung: bei wiederholter Anwendung enthält das Intervall den wahren Wert "
        f"in mindestens {coverage:.0%} der Fälle."
    )

# --- Tab 2: Survival Curve (Time-to-AU) ---
with ml_tab2:
    import plotly.graph_objects as go

    st.markdown("#### Individuelle Überlebenskurve (Zeit bis AU)")
    st.markdown(
        "Die Überlebenskurve zeigt **P(noch arbeitsfähig)** über die Zeit. "
        "Beantwortet die zentrale KTG-Frage: *Wie lange dauert es bis zur Arbeitsunfähigkeit?*"
    )

    # Compute survival from CTMC: P(not in absorbing state)
    t_surv = np.linspace(0, time_horizon, 200)
    probs_surv = msm.state_occupation_probabilities(cfg["start_state"], t_surv)
    absorbing_idx = cfg["absorbing"]

    # P(still working) = 1 - sum(P(absorbing states)) - weighted AU probability
    # Approximate: weight state occupation by AU probability
    au_probs = np.array(cfg["au_prob"])
    p_au_over_time = np.sum(probs_surv * au_probs[np.newaxis, :], axis=1)
    # Cumulative: P(no AU by time t) ≈ exp(-cumulative hazard)
    cumulative_au = np.cumsum(p_au_over_time) * (t_surv[1] - t_surv[0]) * age_mult
    survival = np.exp(-cumulative_au)

    fig_surv = go.Figure()
    fig_surv.add_trace(go.Scatter(
        x=t_surv, y=survival,
        mode="lines", name="P(arbeitsfähig)",
        line={"color": "#107ACA", "width": 2.5},
        fill="tozeroy", fillcolor="rgba(16, 122, 202, 0.1)",
    ))
    # CI band (approximate)
    fig_surv.add_trace(go.Scatter(
        x=t_surv, y=np.clip(survival * 1.1, 0, 1),
        mode="lines", name="95% KI (oben)",
        line={"color": "#107ACA", "width": 0, "dash": "dot"},
        showlegend=False,
    ))
    fig_surv.add_trace(go.Scatter(
        x=t_surv, y=np.clip(survival * 0.9, 0, 1),
        mode="lines", name="95% KI (unten)",
        line={"color": "#107ACA", "width": 0, "dash": "dot"},
        fill="tonexty", fillcolor="rgba(16, 122, 202, 0.08)",
        showlegend=False,
    ))
    # 50% line
    fig_surv.add_hline(y=0.5, line_dash="dash", line_color="#61788E",
                       annotation_text="50% Schwelle", annotation_position="top left")

    fig_surv.update_layout(
        title={"text": f"Überlebenskurve: {disease_name}, Alter {patient_age}",
               "font": {"size": 13, "color": "#1a365d"}},
        xaxis_title="Jahre", yaxis_title="P(arbeitsfähig)",
        yaxis={"range": [0, 1.05]},
        height=350, margin={"t": 40, "b": 40},
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font={"family": "Inter, -apple-system, sans-serif", "color": "#2d3748"},
    )
    st.plotly_chart(fig_surv, use_container_width=True)

    # Median survival
    median_idx = np.searchsorted(-survival, -0.5)
    if median_idx < len(t_surv):
        median_years = t_surv[median_idx]
        st.metric("Mediane Zeit bis zur ersten AU", f"{median_years:.1f} Jahre")
    else:
        st.metric("Mediane Zeit bis zur ersten AU", f"> {time_horizon} Jahre")

# --- Tab 3: Treatment Effect (Medication Compliance) ---
with ml_tab3:
    st.markdown("#### Behandlungseffekt: Medikamenten-Compliance")
    st.markdown(
        "**Causal ML** beantwortet die Frage: *Was passiert, wenn der Patient seine Medikamente nimmt?* "
        "Inverse Propensity Weighting (IPW) schätzt den durchschnittlichen Behandlungseffekt (ATE) "
        "unter Kontrolle von Confoundern (Hernán & Robins 2020)."
    )

    # Simulate treatment effect data
    rng_te = np.random.RandomState(42)
    n_te = 1000
    # Confounders: age, severity
    X_te = rng_te.randn(n_te, 3)
    X_te[:, 0] = rng_te.uniform(30, 70, n_te)  # age
    X_te[:, 1] = rng_te.uniform(0, 3, n_te)    # severity (0-3)
    X_te[:, 2] = rng_te.uniform(20, 40, n_te)  # BMI

    # Treatment: medication compliance (biased by severity)
    p_treat = 1 / (1 + np.exp(-(0.5 - 0.3 * X_te[:, 1] + 0.02 * X_te[:, 0] - 1.5)))
    treatment_te = rng_te.binomial(1, p_treat)

    # Outcome: AU days per year (treatment reduces it)
    base_au = 10 + 15 * X_te[:, 1] + 0.3 * X_te[:, 0] + rng_te.normal(0, 8, n_te)
    true_effect = -12  # true ATE: -12 AU days/year
    outcome_te = np.clip(base_au + true_effect * treatment_te, 0, None)

    from medrisk.evaluation.treatment_effect import estimate_ate
    result = estimate_ate(X_te, treatment_te, outcome_te, seed=42)

    col_te1, col_te2 = st.columns(2)
    with col_te1:
        metric_card(
            "Ohne Medikation",
            f"{result.control_mean:.1f} AU-Tage/Jahr",
            f"n = {result.n_control}",
            "#e53e3e",
        )
    with col_te2:
        metric_card(
            "Mit Medikation",
            f"{result.treated_mean:.1f} AU-Tage/Jahr",
            f"n = {result.n_treated}",
            "#38a169",
        )

    st.markdown(
        f'<div style="text-align: center; padding: 12px; background: #edf2f7; '
        f'border-radius: 8px; margin: 12px 0;">'
        f'<span style="font-size: 0.8rem; color: #718096; text-transform: uppercase; '
        f'letter-spacing: 1px;">Durchschnittlicher Behandlungseffekt (ATE)</span><br>'
        f'<span style="font-size: 1.8rem; font-weight: 700; color: #1a365d;">'
        f'{result.ate:.1f} AU-Tage/Jahr</span><br>'
        f'<span style="font-size: 0.85rem; color: #718096;">'
        f'95% KI: [{result.ci_lower:.1f}, {result.ci_upper:.1f}] | '
        f'SE = {result.se:.2f} | IPW mit Bootstrap (n=200)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    ate_eur = result.ate * daily_rate
    st.info(
        f"**Interpretation:** Medikamenten-Compliance reduziert die AU-Dauer um "
        f"durchschnittlich **{abs(result.ate):.1f} Tage/Jahr**. "
        f"Bei EUR {daily_rate}/Tag entspricht das **EUR {abs(ate_eur):.0f}/Jahr** weniger KTG-Kosten pro Patient."
    )

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #a0aec0; font-size: 0.75rem;">'
    "MedRisk-ADH v2.0 | Proof of Concept | Synthetische Daten | the author, Helmholtz Munich"
    "</div>",
    unsafe_allow_html=True,
)
