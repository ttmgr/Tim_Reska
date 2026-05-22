#!/usr/bin/env python3
"""
Statistical comparisons of LLM model performance.

Three comparisons × three pipeline scopes (pooled, aerobiome, wetland):
  1. Company:    OpenAI vs Anthropic vs Google
  2. Flash tier: ChatGPT-all vs Sonnet family vs Gemini Flash family
  3. Pro tier:   ChatGPT-all vs Claude-all vs Gemini Pro family
  4. Flagship:   GPT-5 vs Opus 4.6 vs Gemini 3.1 Pro  (step-level)

Two complementary test families are run for comparisons 1–3:

  A) Non-parametric (model-level means as unit of analysis)
     – Kruskal-Wallis omnibus
     – Dunn post-hoc with Holm correction (when KW p < 0.05)
     – Pairwise Mann-Whitney U + Cliff's delta + bootstrap 95% CI

  B) Linear Mixed Effects Model  (step-level observations, better powered)
     – composite ~ group + (1 | model)
     – Omnibus: likelihood-ratio test (full vs null model, REML=False)
     – Pairwise: binary LMM per pair + Holm correction

Comparison 4 uses step-level scores directly (n=1 model per group, so
model-level aggregation and LMM random intercept are not applicable).
KW + MWU + Cliff's delta are reported with an explicit correlation caveat.

Outputs:
  results/tables/statistical_tests_kw.csv
  results/tables/statistical_tests_lmm.csv
  results/tables/statistical_tests_flagship.csv
  evaluations/statistical_tests.md
  results/figures/statistical_comparison.{png,pdf,svg}
  results/figures/flagship_comparison.{png,pdf,svg}
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib
import matplotlib.colors
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scikit_posthocs as sp
import statsmodels.formula.api as smf
from scipy.stats import chi2, kruskal, mannwhitneyu
from statsmodels.stats.multitest import multipletests

from scoring import DIMENSIONS, add_numeric_scores

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "results" / "tables" / "scoring_matrix.csv"
OUT_KW_CSV = ROOT / "results" / "tables" / "statistical_tests_kw.csv"
OUT_LMM_CSV = ROOT / "results" / "tables" / "statistical_tests_lmm.csv"
OUT_FLAGSHIP_CSV = ROOT / "results" / "tables" / "statistical_tests_flagship.csv"
OUT_MD = ROOT / "evaluations" / "statistical_tests.md"
OUT_FIG_DIR = ROOT / "results" / "figures"

# ── scoring taxonomy — imported from scoring.py ─────────────────────────────────
# SCORE_MAP and DIMENSIONS are imported from scoring (single source of truth).

# ── comparison definitions ────────────────────────────────────────────────────
COMPARISONS = [
    (
        "1_company",
        "Company (OpenAI vs Anthropic vs Google)",
        {
            "OpenAI":    {"families": ["openai"]},
            "Anthropic": {"families": ["claude"]},
            "Google":    {"families": ["gemini", "google"]},
        },
    ),
    (
        "2_flash",
        "Flash / Small Tier (ChatGPT-all vs Sonnet vs Gemini Flash)",
        {
            "ChatGPT (all)": {"families": ["openai"]},
            "Sonnet": {
                "families": ["claude"],
                "versions": {"sonnet_3.5", "sonnet_4", "sonnet_4.5", "sonnet_4.6"},
            },
            "Gemini Flash": {
                "families": ["gemini"],
                "versions": {"2.0_flash", "2.5_flash", "3_flash"},
            },
        },
    ),
    (
        "3_pro",
        "Pro / Large Tier (ChatGPT-all vs Claude-all vs Gemini Pro)",
        {
            "ChatGPT (all)": {"families": ["openai"]},
            "Claude (all)":  {"families": ["claude"]},
            "Gemini Pro": {
                "families": ["gemini"],
                "versions": {"2.5_pro_preview", "2.5_pro_stable", "3_pro", "3.1_pro"},
            },
        },
    ),
]

SCOPES = [
    ("pooled",    "Pooled",    None),
    ("aerobiome", "Aerobiome", "aerobiome"),
    ("wetland",   "Wetland",   "wetland"),
]

GROUP_COLORS = {
    "OpenAI":        "#2E75B6",
    "ChatGPT (all)": "#2E75B6",
    "Anthropic":     "#C55A11",
    "Sonnet":        "#C55A11",
    "Claude (all)":  "#C55A11",
    "Google":        "#7030A0",
    "Gemini Flash":  "#7030A0",
    "Gemini Pro":    "#7030A0",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10, "axes.labelsize": 11,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9,
    "axes.linewidth": 0.9,
    "xtick.major.width": 0.9, "ytick.major.width": 0.9,
    "xtick.major.size": 4, "ytick.major.size": 4,
    "axes.spines.right": False, "axes.spines.top": False,
    "figure.dpi": 300, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.facecolor": "white",
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})


# ── plot helpers (from 21-plot-design rulebook) ───────────────────────────────

def jstrip(ax, x, vals, color, size=4.8, alpha=0.75, seed=0):
    rng = np.random.default_rng(seed)
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return
    jitter = rng.uniform(-0.10, 0.10, size=vals.size)
    ax.scatter(
        np.full(vals.size, x) + jitter, vals,
        c=[color], s=size ** 2, alpha=alpha,
        edgecolors="white", linewidths=0.5, zorder=5,
    )


def boxplot_manual(ax, x, vals, color, width=0.40, seed=0,
                   lw_box=1.0, lw_med=2.0, lw_whisk=0.9):
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return
    q1, median, q3 = np.percentile(vals, [25, 50, 75])
    iqr = q3 - q1
    lo_fence, hi_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    in_fence = vals[(vals >= lo_fence) & (vals <= hi_fence)]
    lo = float(in_fence.min()) if in_fence.size else float(q1)
    hi = float(in_fence.max()) if in_fence.size else float(q3)
    half = width / 2.0

    ax.add_patch(matplotlib.patches.Rectangle(
        (x - half, q1), width, q3 - q1,
        facecolor=matplotlib.colors.to_rgba(color, 0.25),
        edgecolor="black", linewidth=lw_box, zorder=2,
    ))
    ax.plot([x - half, x + half], [median, median], color="black", lw=lw_med, zorder=4)
    ax.plot([x, x], [q1, lo], color="black", lw=lw_whisk, zorder=3)
    ax.plot([x, x], [q3, hi], color="black", lw=lw_whisk, zorder=3)
    ax.plot([x - half, x + half], [lo, lo], color="black", lw=lw_whisk, zorder=3)
    ax.plot([x - half, x + half], [hi, hi], color="black", lw=lw_whisk, zorder=3)

    outliers = vals[(vals < lo) | (vals > hi)]
    if outliers.size:
        ax.scatter(np.full(outliers.size, x), outliers,
                   marker="+", s=28, c=[color], alpha=0.7, zorder=4)
    jstrip(ax, x, vals, color, size=4.8, alpha=0.72, seed=seed)


def mwu_pr(a, b):
    a = np.asarray(a, dtype=float); a = a[np.isfinite(a)]
    b = np.asarray(b, dtype=float); b = b[np.isfinite(b)]
    if len(a) < 3 or len(b) < 3:
        return None, None
    U, p = mannwhitneyu(a, b, alternative="two-sided")
    r = (2.0 * float(U)) / (len(a) * len(b)) - 1.0
    return float(p), float(r)


def stars(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n/a"
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


def annotate_pr(ax, x1, x2, y, p, r, dy_frac=0.08, fontsize=8.0):
    """Bracket + stars. Silent when p >= 0.05."""
    if p is None or p >= 0.05:
        return
    h = y * dy_frac
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=0.9, color="k", clip_on=False)
    ax.text(
        (x1 + x2) / 2.0, y + h * 1.15,
        f"{stars(p)}\np={p:.2g}\nr={r:+.2f}",
        ha="center", va="bottom", fontsize=fontsize,
        color="k", fontweight="bold", clip_on=False,
    )


# ── statistical helpers ───────────────────────────────────────────────────────

def cliff_delta(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    concordant = int(np.sum(x[:, None] > y[None, :]))
    discordant = int(np.sum(x[:, None] < y[None, :]))
    return float((concordant - discordant) / (len(x) * len(y)))


def cliff_magnitude(d):
    d = abs(d)
    if d < 0.147: return "negligible"
    if d < 0.330: return "small"
    if d < 0.474: return "medium"
    return "large"


def bootstrap_ci(x, n_boot=1000, seed=42):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float); x = x[np.isfinite(x)]
    if len(x) < 2:
        return np.nan, np.nan
    boot = [np.mean(rng.choice(x, size=len(x), replace=True)) for _ in range(n_boot)]
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def _holm(raw_pvals):
    """Holm-Bonferroni correction. Returns list of corrected p-values (nan preserved)."""
    valid_mask = [p is not None and not np.isnan(p) for p in raw_pvals]
    out = [np.nan] * len(raw_pvals)
    valid_p = [p for p, v in zip(raw_pvals, valid_mask) if v]
    if valid_p:
        _, corrected, _, _ = multipletests(valid_p, method="holm")
        vi = 0
        for i, valid in enumerate(valid_mask):
            if valid:
                out[i] = float(corrected[vi]); vi += 1
    return out


# ── data loading ──────────────────────────────────────────────────────────────

def load_data():
    df = pd.read_csv(CSV_PATH)
    add_numeric_scores(df)
    df["composite"] = df[[f"{d}_num" for d in DIMENSIONS]].mean(axis=1)
    df["model_key"] = df["model_family"] + "_" + df["model_version"]
    return df


def compute_model_means(df, pipeline=None):
    if pipeline is not None:
        df = df[df["pipeline"] == pipeline]
    return (
        df.groupby(["model_family", "model_version"])["composite"]
        .mean().reset_index()
        .rename(columns={"composite": "composite_mean"})
    )


def filter_to_group(model_means_df, group_def):
    families = group_def["families"]
    versions = group_def.get("versions", None)
    mask = model_means_df["model_family"].isin(families)
    if versions is not None:
        mask &= model_means_df["model_version"].isin(versions)
    return model_means_df.loc[mask, "composite_mean"].values


def build_step_df(df, groups_def, pipeline=None):
    """Step-level df annotated with group labels; rows outside all groups dropped."""
    if pipeline is not None:
        df = df[df["pipeline"] == pipeline]
    df = df.copy()
    df["group"] = None
    for group_name, defn in groups_def.items():
        mask = df["model_family"].isin(defn["families"])
        if "versions" in defn:
            mask &= df["model_version"].isin(defn["versions"])
        df.loc[mask, "group"] = group_name
    return df[df["group"].notna()].copy()


# ── A: non-parametric tests (model-level means) ───────────────────────────────

def run_kw_comparison(cmp_id, cmp_label, groups_def, scope_id, scope_label, model_means_df):
    group_names = list(groups_def.keys())
    group_scores = {n: filter_to_group(model_means_df, d) for n, d in groups_def.items()}
    arrays = [group_scores[n] for n in group_names]

    if any(len(a) < 2 for a in arrays):
        kw_h, kw_p = np.nan, np.nan
    else:
        kw_h, kw_p = kruskal(*arrays)
        kw_h, kw_p = float(kw_h), float(kw_p)

    dunn_p = {}
    if not np.isnan(kw_p) and kw_p < 0.05:
        combined_vals = np.concatenate(arrays)
        combined_labels = np.concatenate([np.full(len(a), n) for n, a in zip(group_names, arrays)])
        dunn_df = sp.posthoc_dunn(
            pd.DataFrame({"score": combined_vals, "group": combined_labels}),
            val_col="score", group_col="group", p_adjust="holm",
        )
        for i, n1 in enumerate(group_names):
            for n2 in group_names[i + 1:]:
                dunn_p[(n1, n2)] = float(dunn_df.loc[n1, n2])

    pair_results = []
    for i, n1 in enumerate(group_names):
        for n2 in group_names[i + 1:]:
            a, b = group_scores[n1], group_scores[n2]
            cd = cliff_delta(a, b) if len(a) >= 2 and len(b) >= 2 else np.nan
            mwu_p_val, mwu_r_val = mwu_pr(a, b)
            pair_results.append({
                "group_a": n1, "group_b": n2,
                "n_a": len(a), "n_b": len(b),
                "mean_a": float(np.mean(a)) if len(a) else np.nan,
                "mean_b": float(np.mean(b)) if len(b) else np.nan,
                "cliff_delta": cd,
                "cliff_magnitude": cliff_magnitude(cd) if not np.isnan(cd) else "n/a",
                "mwu_p": mwu_p_val,
                "mwu_r": mwu_r_val,
                "dunn_p_holm": dunn_p.get((n1, n2), np.nan),
            })

    group_summaries = {}
    for name in group_names:
        sc = group_scores[name]
        ci_lo, ci_hi = bootstrap_ci(sc)
        group_summaries[name] = {
            "n": len(sc),
            "mean": float(np.mean(sc)) if len(sc) else np.nan,
            "sd": float(np.std(sc, ddof=1)) if len(sc) >= 2 else np.nan,
            "ci_lo": ci_lo, "ci_hi": ci_hi,
        }

    return {
        "cmp_id": cmp_id, "cmp_label": cmp_label,
        "scope_id": scope_id, "scope_label": scope_label,
        "group_names": group_names,
        "group_scores": group_scores,
        "group_summaries": group_summaries,
        "kw_h": kw_h, "kw_p": kw_p,
        "pair_results": pair_results,
    }


# ── B: linear mixed effects model (step-level, model as random intercept) ─────

def _fit_lmm(formula, data, groups_col, method="lbfgs"):
    """Fit a single LMM; try fallback optimisers on convergence failure."""
    for m in (method, "bfgs", "nm"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return smf.mixedlm(formula, data=data, groups=data[groups_col]).fit(
                    reml=False, method=m, disp=False
                )
        except Exception:
            continue
    return None


def run_lmm_comparison(cmp_id, cmp_label, groups_def, scope_id, scope_label, df, pipeline=None):
    step_df = build_step_df(df, groups_def, pipeline)
    group_names = list(groups_def.keys())

    if step_df.empty or step_df["model_key"].nunique() < 3:
        return None

    # Encode groups as g0/g1/g2 so patsy never sees special characters
    gid = {name: f"g{i}" for i, name in enumerate(group_names)}
    step_df = step_df.copy()
    step_df["gid"] = step_df["group"].map(gid)

    # ── omnibus LRT ──────────────────────────────────────────────────────────
    null_fit = _fit_lmm("composite ~ 1",          step_df, "model_key")
    full_fit = _fit_lmm("composite ~ C(gid)",     step_df, "model_key")

    if null_fit is not None and full_fit is not None:
        lr_stat = float(max(0.0, -2.0 * (null_fit.llf - full_fit.llf)))
        lr_df   = len(group_names) - 1
        lr_p    = float(chi2.sf(lr_stat, df=lr_df))
    else:
        lr_stat, lr_df, lr_p = np.nan, np.nan, np.nan

    # ── pairwise binary LMMs ─────────────────────────────────────────────────
    pairs = [(group_names[i], group_names[j])
             for i in range(len(group_names))
             for j in range(i + 1, len(group_names))]

    raw_p, pair_info = [], []
    for g1, g2 in pairs:
        sub = step_df[step_df["group"].isin([g1, g2])].copy()
        sub["is_g2"] = (sub["group"] == g2).astype(float)
        fit = _fit_lmm("composite ~ is_g2", sub, "model_key")
        if fit is not None and "is_g2" in fit.params.index:
            coef = float(fit.params["is_g2"])
            se   = float(fit.bse["is_g2"])
            z    = float(fit.tvalues["is_g2"])
            p    = float(fit.pvalues["is_g2"])
        else:
            coef, se, z, p = np.nan, np.nan, np.nan, np.nan
        raw_p.append(p)
        pair_info.append((g1, g2, coef, se, z, p))

    holm_p = _holm(raw_p)

    pairwise = [
        {
            "group_a": g1, "group_b": g2,
            "n_models_a": int(step_df.loc[step_df["group"] == g1, "model_key"].nunique()),
            "n_models_b": int(step_df.loc[step_df["group"] == g2, "model_key"].nunique()),
            "n_obs_a": int((step_df["group"] == g1).sum()),
            "n_obs_b": int((step_df["group"] == g2).sum()),
            "coef": coef, "se": se, "z_stat": z,
            "lmm_p": p, "lmm_p_holm": hp,
        }
        for (g1, g2, coef, se, z, p), hp in zip(pair_info, holm_p)
    ]

    return {
        "cmp_id": cmp_id, "cmp_label": cmp_label,
        "scope_id": scope_id, "scope_label": scope_label,
        "group_names": group_names,
        "lrt_stat": lr_stat, "lrt_df": lr_df, "lrt_p": lr_p,
        "pairwise": pairwise,
        "n_obs_total": len(step_df),
        "n_models_total": step_df["model_key"].nunique(),
    }


# ── figure ────────────────────────────────────────────────────────────────────

def _find(results, cmp_id, scope_id):
    return next((r for r in results if r["cmp_id"] == cmp_id and r["scope_id"] == scope_id), None)


def plot_all(kw_results, lmm_results):
    n_rows, n_cols = len(COMPARISONS), len(SCOPES)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 13), sharey=True)
    row_short = ["Company", "Flash Tier", "Pro Tier"]

    for row_i, (cmp_id, _, _) in enumerate(COMPARISONS):
        for col_j, (scope_id, scope_label, _) in enumerate(SCOPES):
            ax = axes[row_i, col_j]
            kw = _find(kw_results, cmp_id, scope_id)
            lmm = _find(lmm_results, cmp_id, scope_id)
            group_names = kw["group_names"]

            for xi, name in enumerate(group_names):
                color = GROUP_COLORS.get(name, "#555555")
                boxplot_manual(ax, xi, kw["group_scores"][name], color, width=0.40, seed=xi)

            bracket_config = [(0, 1, 1.04), (1, 2, 1.04), (0, 2, 1.22)]
            for xi1, xi2, bry in bracket_config:
                n1, n2 = group_names[xi1], group_names[xi2]
                pr = next((p for p in kw["pair_results"]
                           if p["group_a"] == n1 and p["group_b"] == n2), None)
                if pr and pr["mwu_p"] is not None:
                    annotate_pr(ax, xi1, xi2, bry, pr["mwu_p"], pr["mwu_r"],
                                dy_frac=0.08, fontsize=7.5)

            # Corner annotation: KW + LMM omnibus p
            kw_line = (f"KW H={kw['kw_h']:.2f}, p={kw['kw_p']:.3f}"
                       if not np.isnan(kw["kw_h"]) else "KW: n/a")
            if lmm is not None and not np.isnan(lmm["lrt_p"]):
                lmm_line = f"LMM LRT p={lmm['lrt_p']:.3f}"
                sig = " †" if lmm["lrt_p"] < 0.05 else ""
                lmm_line += sig
            else:
                lmm_line = "LMM: n/a"
            ax.text(0.02, 0.97, f"{kw_line}\n{lmm_line}",
                    transform=ax.transAxes, fontsize=6.8, va="top", color="0.38",
                    linespacing=1.5)

            ax.set_xlim(-0.55, len(group_names) - 0.45)
            ax.set_ylim(0, 1.58)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
            ax.set_xticks(range(len(group_names)))
            ax.set_xticklabels(
                [f"{n}\n(n={kw['group_summaries'][n]['n']})" for n in group_names],
                fontsize=8.5,
            )
            if col_j == 0:
                ax.set_ylabel("Composite score", fontsize=10)
            if row_i == 0:
                ax.set_title(scope_label, fontsize=11, fontweight="bold", pad=6)
            if col_j == 0:
                ax.text(-0.22, 0.5, row_short[row_i], transform=ax.transAxes,
                        fontsize=9, fontweight="bold", rotation=90,
                        va="center", ha="center")

    fig.suptitle(
        "LLM Performance Comparisons\n"
        "Box plots show model-level distributions  ·  "
        "Brackets: MWU (significant pairs only)  ·  "
        "Corner text: KW + LMM omnibus p",
        fontsize=11, y=1.02, fontweight="bold",
    )
    plt.tight_layout(rect=[0.06, 0, 1, 1])
    OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(OUT_FIG_DIR / f"statistical_comparison.{ext}")
    print(f"[figure]   → {OUT_FIG_DIR}/statistical_comparison.{{png,pdf,svg}}")
    plt.close(fig)


# ── table outputs ─────────────────────────────────────────────────────────────

def _fmt(val, d=4):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return round(val, d)


def save_kw_csv(kw_results):
    rows = []
    for res in kw_results:
        base = {"comparison": res["cmp_label"], "scope": res["scope_label"],
                "kw_H": _fmt(res["kw_h"]), "kw_p": _fmt(res["kw_p"])}
        for pr in res["pair_results"]:
            rows.append({**base,
                "group_a": pr["group_a"], "group_b": pr["group_b"],
                "n_a": pr["n_a"], "n_b": pr["n_b"],
                "mean_a": _fmt(pr["mean_a"]), "mean_b": _fmt(pr["mean_b"]),
                "cliff_delta": _fmt(pr["cliff_delta"], 3),
                "cliff_magnitude": pr["cliff_magnitude"],
                "mwu_p": _fmt(pr["mwu_p"]), "mwu_r": _fmt(pr["mwu_r"], 3),
                "dunn_p_holm": _fmt(pr["dunn_p_holm"]),
            })
    OUT_KW_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_KW_CSV, index=False)
    print(f"[KW csv]   → {OUT_KW_CSV}")


def save_lmm_csv(lmm_results):
    rows = []
    for res in lmm_results:
        if res is None:
            continue
        base = {"comparison": res["cmp_label"], "scope": res["scope_label"],
                "lrt_stat": _fmt(res["lrt_stat"]), "lrt_df": res["lrt_df"],
                "lrt_p": _fmt(res["lrt_p"]),
                "n_obs_total": res["n_obs_total"],
                "n_models_total": res["n_models_total"]}
        for pr in res["pairwise"]:
            rows.append({**base,
                "group_a": pr["group_a"], "group_b": pr["group_b"],
                "n_models_a": pr["n_models_a"], "n_models_b": pr["n_models_b"],
                "n_obs_a": pr["n_obs_a"], "n_obs_b": pr["n_obs_b"],
                "coef": _fmt(pr["coef"]), "se": _fmt(pr["se"]),
                "z_stat": _fmt(pr["z_stat"], 3),
                "lmm_p": _fmt(pr["lmm_p"]), "lmm_p_holm": _fmt(pr["lmm_p_holm"]),
            })
    OUT_LMM_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_LMM_CSV, index=False)
    print(f"[LMM csv]  → {OUT_LMM_CSV}")


def save_markdown(kw_results, lmm_results):
    lines = [
        "# Statistical Comparisons of LLM Performance\n",
        "Two complementary test families are reported for each comparison × pipeline scope.\n",
        "---\n",
        "## A — Non-Parametric Tests (model-level means)\n",
        "**Unit:** each model is reduced to one composite mean score per scope.  ",
        "**Omnibus:** Kruskal-Wallis H.  ",
        "**Post-hoc:** Dunn's test (Holm correction, only when KW p < 0.05).  ",
        "**Effect size:** Cliff's δ (negligible < 0.147 ≤ small < 0.33 ≤ medium < 0.474 ≤ large).  ",
        "**CI:** bootstrap 95%, 1 000 iterations.\n",
        "> **Small-n caveat:** sub-tier groups have n = 3–4 models. "
        "Tests are indicative only for those comparisons.\n",
    ]

    for cmp_id, cmp_label, _ in COMPARISONS:
        lines += ["", f"### {cmp_label}", ""]
        for scope_id, scope_label, _ in SCOPES:
            res = _find(kw_results, cmp_id, scope_id)
            lines += [f"#### {scope_label}", ""]
            lines += ["| Group | n | Mean ± SD | 95% CI |", "|-------|---|-----------|--------|"]
            for name in res["group_names"]:
                gs = res["group_summaries"][name]
                lines.append(f"| {name} | {gs['n']} "
                              f"| {gs['mean']:.3f} ± {gs['sd']:.3f} "
                              f"| [{gs['ci_lo']:.3f}, {gs['ci_hi']:.3f}] |")
            kw_sig = "**significant**" if res["kw_p"] < 0.05 else "not significant"
            lines += ["",
                      f"**Kruskal-Wallis:** H = {res['kw_h']:.3f}, p = {res['kw_p']:.4f} ({kw_sig})",
                      "",
                      "| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |",
                      "|------|-----------|-----------|-------|---------------|-----|"]
            for pr in res["pair_results"]:
                cd = f"{pr['cliff_delta']:+.3f}" if not np.isnan(pr["cliff_delta"]) else "n/a"
                mp = f"{pr['mwu_p']:.4f}" if pr["mwu_p"] is not None else "n/a"
                dv = pr["dunn_p_holm"]
                dp = f"{dv:.4f}" if not np.isnan(dv) else "—"
                lines.append(f"| {pr['group_a']} vs {pr['group_b']} "
                              f"| {cd} | {pr['cliff_magnitude']} | {mp} | {dp} | {stars(pr['mwu_p'])} |")
            lines.append("")

    lines += [
        "---\n",
        "## B — Linear Mixed Effects Model (step-level, better powered)\n",
        "**Model:** `composite ~ group + (1 | model)` — step-level scores as observations; "
        "model identity as random intercept to absorb within-model correlation.  ",
        "**Omnibus:** likelihood-ratio test (LRT) comparing full vs intercept-only model "
        "(both fitted with ML, not REML).  ",
        "**Pairwise:** binary LMM per pair (one group coded as indicator), Holm correction.  ",
        "**Coefficient (coef):** estimated mean difference (group B − group A) in composite score.\n",
        "> The LMM uses all step-level observations (~17 per model) and is more powerful "
        "than KW for the company comparison (n ≈ 10/8/8 models). For Flash-tier (n = 10/4/3) "
        "and Pro-tier (n = 10/8/4), power gains are smaller because between-group "
        "inference still scales with the number of models, not steps.\n",
    ]

    for cmp_id, cmp_label, _ in COMPARISONS:
        lines += ["", f"### {cmp_label}", ""]
        for scope_id, scope_label, _ in SCOPES:
            res = _find(lmm_results, cmp_id, scope_id)
            lines += [f"#### {scope_label}", ""]
            if res is None:
                lines.append("_LMM could not be fitted (insufficient data)._\n")
                continue
            lrt_sig = "**significant**" if res["lrt_p"] < 0.05 else "not significant"
            lines += [
                f"**LRT:** χ²({res['lrt_df']}) = {res['lrt_stat']:.3f}, "
                f"p = {res['lrt_p']:.4f} ({lrt_sig})  "
                f"_(N = {res['n_obs_total']} step-scores, "
                f"{res['n_models_total']} models)_",
                "",
                "| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |",
                "|------|---------------|------|----|---|-------|--------|-----|",
            ]
            for pr in res["pairwise"]:
                coef_s = f"{pr['coef']:+.3f}" if not np.isnan(pr["coef"]) else "n/a"
                se_s   = f"{pr['se']:.3f}"    if not np.isnan(pr["se"])   else "n/a"
                z_s    = f"{pr['z_stat']:+.2f}" if not np.isnan(pr["z_stat"]) else "n/a"
                lp_s   = f"{pr['lmm_p']:.4f}" if not np.isnan(pr["lmm_p"]) else "n/a"
                hp_s   = f"{pr['lmm_p_holm']:.4f}" if not np.isnan(pr["lmm_p_holm"]) else "n/a"
                lines.append(
                    f"| {pr['group_a']} vs {pr['group_b']} "
                    f"| {pr['n_models_a']} / {pr['n_models_b']} "
                    f"| {coef_s} | {se_s} | {z_s} | {lp_s} | {hp_s} | {stars(pr['lmm_p_holm'])} |"
                )
            lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"[markdown] → {OUT_MD}")


# ── C: flagship comparison (step-level, n=1 model per group) ──────────────────

FLAGSHIPS = {
    "GPT-5":         {"family": "openai", "version": "gpt5"},
    "Opus 4.6":      {"family": "claude", "version": "opus_4.6"},
    "Gemini 3.1 Pro":{"family": "gemini", "version": "3.1_pro"},
}
FLAGSHIP_COLORS = {
    "GPT-5":          "#2E75B6",
    "Opus 4.6":       "#C55A11",
    "Gemini 3.1 Pro": "#7030A0",
}


def run_flagship_comparison(df, pipeline=None):
    """KW + pairwise MWU on step-level scores for the three flagship models."""
    scope_id = pipeline if pipeline else "pooled"
    if pipeline:
        df = df[df["pipeline"] == pipeline]

    group_scores = {}
    for label, spec in FLAGSHIPS.items():
        mask = (df["model_family"] == spec["family"]) & (df["model_version"] == spec["version"])
        group_scores[label] = df.loc[mask, "composite"].values

    group_names = list(FLAGSHIPS.keys())
    arrays = [group_scores[n] for n in group_names]

    if any(len(a) == 0 for a in arrays):
        return None

    kw_h, kw_p = kruskal(*arrays)
    kw_h, kw_p = float(kw_h), float(kw_p)

    # Dunn post-hoc when significant
    dunn_p = {}
    if kw_p < 0.05:
        combined_vals = np.concatenate(arrays)
        combined_labels = np.concatenate([np.full(len(a), n) for n, a in zip(group_names, arrays)])
        dunn_df = sp.posthoc_dunn(
            pd.DataFrame({"score": combined_vals, "group": combined_labels}),
            val_col="score", group_col="group", p_adjust="holm",
        )
        for i, n1 in enumerate(group_names):
            for n2 in group_names[i + 1:]:
                dunn_p[(n1, n2)] = float(dunn_df.loc[n1, n2])

    pair_results = []
    for i, n1 in enumerate(group_names):
        for n2 in group_names[i + 1:]:
            a, b = group_scores[n1], group_scores[n2]
            cd = cliff_delta(a, b)
            U, mwu_p_val = mannwhitneyu(a, b, alternative="two-sided")
            mwu_r_val = (2.0 * float(U)) / (len(a) * len(b)) - 1.0
            pair_results.append({
                "group_a": n1, "group_b": n2,
                "n_a": len(a), "n_b": len(b),
                "mean_a": float(np.mean(a)), "mean_b": float(np.mean(b)),
                "cliff_delta": cd,
                "cliff_magnitude": cliff_magnitude(cd),
                "mwu_p": float(mwu_p_val),
                "mwu_r": float(mwu_r_val),
                "dunn_p_holm": dunn_p.get((n1, n2), np.nan),
            })

    group_summaries = {
        name: {
            "n": len(sc),
            "mean": float(np.mean(sc)),
            "sd": float(np.std(sc, ddof=1)),
        }
        for name, sc in group_scores.items()
    }

    return {
        "scope_id": scope_id,
        "group_names": group_names,
        "group_scores": group_scores,
        "group_summaries": group_summaries,
        "kw_h": kw_h, "kw_p": kw_p,
        "pair_results": pair_results,
    }


def plot_flagship(flagship_results):
    scope_labels = {"pooled": "Pooled", "aerobiome": "Aerobiome", "wetland": "Wetland"}
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)

    for col_j, res in enumerate(flagship_results):
        ax = axes[col_j]
        group_names = res["group_names"]

        for xi, name in enumerate(group_names):
            color = FLAGSHIP_COLORS[name]
            boxplot_manual(ax, xi, res["group_scores"][name], color, width=0.40, seed=xi)

        # Pairwise MWU brackets (silent if ns)
        bracket_config = [(0, 1, 1.04), (1, 2, 1.04), (0, 2, 1.22)]
        for xi1, xi2, bry in bracket_config:
            n1, n2 = group_names[xi1], group_names[xi2]
            pr = next((p for p in res["pair_results"]
                       if p["group_a"] == n1 and p["group_b"] == n2), None)
            if pr:
                annotate_pr(ax, xi1, xi2, bry, pr["mwu_p"], pr["mwu_r"],
                            dy_frac=0.08, fontsize=8.0)

        if not np.isnan(res["kw_h"]):
            sig_marker = " †" if res["kw_p"] < 0.05 else ""
            kw_ann = f"KW H={res['kw_h']:.2f}, p={res['kw_p']:.3f}{sig_marker}"
        else:
            kw_ann = "KW: all scores tied (p = 1)"
        ax.text(0.02, 0.97, kw_ann,
                transform=ax.transAxes, fontsize=7.5, va="top", color="0.38")

        ax.set_xlim(-0.55, len(group_names) - 0.45)
        ax.set_ylim(0, 1.58)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticks(range(len(group_names)))
        ax.set_xticklabels(
            [f"{n}\n(n={res['group_summaries'][n]['n']} steps)" for n in group_names],
            fontsize=9,
        )
        if col_j == 0:
            ax.set_ylabel("Composite score", fontsize=10)
        ax.set_title(scope_labels.get(res["scope_id"], res["scope_id"]),
                     fontsize=11, fontweight="bold", pad=6)

    fig.suptitle(
        "Flagship Model Comparison: GPT-5 vs Opus 4.6 vs Gemini 3.1 Pro\n"
        "Step-level composite scores  ·  Brackets: MWU (significant pairs only)\n"
        "[Note] Steps within a model are correlated — treat p-values as indicative",
        fontsize=10, y=1.04, fontweight="bold",
    )
    plt.tight_layout()
    OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(OUT_FIG_DIR / f"flagship_comparison.{ext}")
    print(f"[figure]   → {OUT_FIG_DIR}/flagship_comparison.{{png,pdf,svg}}")
    plt.close(fig)


def save_flagship_csv(flagship_results):
    rows = []
    scope_labels = {"pooled": "Pooled", "aerobiome": "Aerobiome", "wetland": "Wetland"}
    for res in flagship_results:
        base = {
            "scope": scope_labels.get(res["scope_id"], res["scope_id"]),
            "kw_H": _fmt(res["kw_h"]), "kw_p": _fmt(res["kw_p"]),
        }
        for pr in res["pair_results"]:
            rows.append({**base,
                "group_a": pr["group_a"], "group_b": pr["group_b"],
                "n_steps_a": pr["n_a"], "n_steps_b": pr["n_b"],
                "mean_a": _fmt(pr["mean_a"]), "mean_b": _fmt(pr["mean_b"]),
                "cliff_delta": _fmt(pr["cliff_delta"], 3),
                "cliff_magnitude": pr["cliff_magnitude"],
                "mwu_p": _fmt(pr["mwu_p"]), "mwu_r": _fmt(pr["mwu_r"], 3),
                "dunn_p_holm": _fmt(pr["dunn_p_holm"]),
            })
    OUT_FLAGSHIP_CSV.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_FLAGSHIP_CSV, index=False)
    print(f"[flagship] → {OUT_FLAGSHIP_CSV}")


def append_flagship_markdown(flagship_results):
    scope_labels = {"pooled": "Pooled", "aerobiome": "Aerobiome", "wetland": "Wetland"}
    lines = [
        "",
        "---\n",
        "## C — Flagship Model Comparison\n",
        "**Models:** GPT-5 (OpenAI) · Opus 4.6 (Anthropic) · Gemini 3.1 Pro (Google)  ",
        "**Unit:** step-level composite scores (n = 17 pooled / 7 aerobiome / 10 wetland per model).  ",
        "**Tests:** Kruskal-Wallis + Dunn post-hoc (Holm, when significant) + pairwise MWU + Cliff's δ.\n",
        "> **Correlation caveat:** with only one model per group, steps within a model are not",
        "> independent (same model applied to consecutive pipeline stages). p-values are",
        "> therefore indicative of the direction and size of differences, not formal hypothesis",
        "> tests. Interpret Cliff's δ as the primary measure of practical significance.\n",
    ]

    for res in flagship_results:
        scope = scope_labels.get(res["scope_id"], res["scope_id"])
        lines += [f"### {scope}", ""]
        lines += ["| Model | n steps | Mean ± SD |", "|-------|---------|-----------|"]
        for name in res["group_names"]:
            gs = res["group_summaries"][name]
            lines.append(f"| {name} | {gs['n']} | {gs['mean']:.3f} ± {gs['sd']:.3f} |")
        if np.isnan(res["kw_h"]):
            kw_line = "**Kruskal-Wallis:** all three models scored identically across every step (all scores tied — p = 1)"
        else:
            kw_sig = "**significant**" if res["kw_p"] < 0.05 else "not significant"
            kw_line = f"**Kruskal-Wallis:** H = {res['kw_h']:.3f}, p = {res['kw_p']:.4f} ({kw_sig})"
        lines += [
            "",
            kw_line,
            "",
            "| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |",
            "|------|-----------|-----------|-------|---------------|-----|",
        ]
        for pr in res["pair_results"]:
            cd = f"{pr['cliff_delta']:+.3f}"
            dv = pr["dunn_p_holm"]
            dp = f"{dv:.4f}" if not np.isnan(dv) else "—"
            lines.append(
                f"| {pr['group_a']} vs {pr['group_b']} "
                f"| {cd} | {pr['cliff_magnitude']} "
                f"| {pr['mwu_p']:.4f} | {dp} | {stars(pr['mwu_p'])} |"
            )
        lines.append("")

    with open(OUT_MD, "a") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[markdown] → appended flagship section to {OUT_MD}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    df = load_data()
    kw_results, lmm_results = [], []

    for scope_id, scope_label, pipeline_filter in SCOPES:
        model_means_df = compute_model_means(df, pipeline=pipeline_filter)

        for cmp_id, cmp_label, groups_def in COMPARISONS:
            # A: KW
            kw = run_kw_comparison(
                cmp_id, cmp_label, groups_def,
                scope_id, scope_label, model_means_df,
            )
            kw_results.append(kw)

            # B: LMM
            print(f"  [LMM] fitting {cmp_id} / {scope_id} …", end=" ", flush=True)
            lmm = run_lmm_comparison(
                cmp_id, cmp_label, groups_def,
                scope_id, scope_label, df, pipeline=pipeline_filter,
            )
            lmm_results.append(lmm)
            lrt_str = f"LRT p={lmm['lrt_p']:.4f}" if lmm and not np.isnan(lmm["lrt_p"]) else "n/a"
            print(lrt_str)

            # Console summary
            print(f"\n{'='*64}")
            print(f"  {cmp_label}  |  {scope_label}")
            print(f"  KW  H={kw['kw_h']:.3f},  p={kw['kw_p']:.4f}"
                  + ("  ← significant" if kw["kw_p"] < 0.05 else ""))
            if lmm:
                print(f"  LMM LRT χ²({lmm['lrt_df']})={lmm['lrt_stat']:.3f},  p={lmm['lrt_p']:.4f}"
                      + ("  ← significant" if lmm["lrt_p"] < 0.05 else ""))
            for pr in kw["pair_results"]:
                mwu_s = f"{pr['mwu_p']:.4f}" if pr["mwu_p"] is not None else "n/a"
                cd_s  = f"{pr['cliff_delta']:+.3f}" if not np.isnan(pr["cliff_delta"]) else "n/a"
                lmm_pr = None
                if lmm:
                    lmm_pr = next(
                        (p for p in lmm["pairwise"]
                         if p["group_a"] == pr["group_a"] and p["group_b"] == pr["group_b"]),
                        None,
                    )
                lmm_s = f"LMM p={lmm_pr['lmm_p_holm']:.4f} ({stars(lmm_pr['lmm_p_holm'])})" \
                        if lmm_pr and not np.isnan(lmm_pr["lmm_p_holm"]) else ""
                print(
                    f"    {pr['group_a']:16s} vs {pr['group_b']:16s} | "
                    f"δ={cd_s} ({pr['cliff_magnitude']:10s}) | "
                    f"MWU p={mwu_s} {stars(pr['mwu_p'])}  {lmm_s}"
                )

    save_kw_csv(kw_results)
    save_lmm_csv(lmm_results)
    save_markdown(kw_results, lmm_results)
    plot_all(kw_results, lmm_results)

    # C: flagship
    print("\n── Flagship comparison ──────────────────────────────────────────")
    flagship_results = []
    for scope_id, _, pipeline_filter in SCOPES:
        res = run_flagship_comparison(df, pipeline=pipeline_filter)
        if res is None:
            print(f"  [{scope_id}] no data — skipping")
            continue
        flagship_results.append(res)
        print(f"\n  {scope_id.upper()}")
        print(f"  KW H={res['kw_h']:.3f},  p={res['kw_p']:.4f}"
              + ("  ← significant" if res["kw_p"] < 0.05 else ""))
        for pr in res["pair_results"]:
            print(
                f"    {pr['group_a']:16s} vs {pr['group_b']:16s} | "
                f"δ={pr['cliff_delta']:+.3f} ({pr['cliff_magnitude']:10s}) | "
                f"MWU p={pr['mwu_p']:.4f}  {stars(pr['mwu_p'])}"
            )

    save_flagship_csv(flagship_results)
    append_flagship_markdown(flagship_results)
    plot_flagship(flagship_results)
    print("\nDone.")


if __name__ == "__main__":
    main()
