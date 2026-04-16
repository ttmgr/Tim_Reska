#!/usr/bin/env python3
"""
Generate a scoring heatmap from the evaluation matrix.

Reads results/tables/scoring_matrix.csv and produces a heatmap with:
- X-axis: pipeline steps
- Y-axis: evaluated entries
- Color: composite score (green = correct, yellow = partial, red = incorrect)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

SCORE_MAP = {
    "tool_selection": {"C": 1.0, "A": 0.5, "I": 0.0},
    "parameter_accuracy": {"C": 1.0, "P": 0.5, "I": 0.0},
    "output_compatibility": {"P": 1.0, "F": 0.0},
    "scientific_validity": {"S": 1.0, "Q": 0.5, "I": 0.0},
    "executability": {"R": 1.0, "M": 0.5, "N": 0.0},
}

DIMENSIONS = list(SCORE_MAP.keys())
STEP_LABELS_AEROBIOME = {
    1: "Basecalling",
    2: "QC",
    3: "Host\nDepletion",
    4: "Taxonomy",
    5: "Assembly",
    6: "Binning",
    7: "Annotation",
}
STEP_LABELS_WETLAND = {
    1: "Basecalling\n& QC",
    2: "Taxonomy\n& Norm.",
    3: "Assembly\n(Dual)",
    4: "Polish &\nAnnotate",
    5: "Pathogen\nID",
    6: "AMR/Vir/\nPlasmid",
    7: "RNA\nVirome",
    8: "eDNA\nMetabarc.",
    9: "AIV\nConsensus",
    10: "AIV\nPhylo.",
}
PIPELINE_STEP_LABELS = {
    "aerobiome": STEP_LABELS_AEROBIOME,
    "wetland": STEP_LABELS_WETLAND,
}
PIPELINE_TITLES = {
    "aerobiome": "Aerobiome Pipeline",
    "wetland": "Wetland Surveillance Pipeline",
}
# Keep backward compat alias
STEP_LABELS = STEP_LABELS_AEROBIOME
FAMILY_ORDER = ["openai", "claude", "gemini", "google", "deepseek", "zhipu"]
VERSION_ORDER = {
    "openai": [
        "gpt4o",
        "o1_preview",
        "o1_mini",
        "o1",
        "o1_pro",
        "o3_mini",
        "o3_high",
        "o4_mini",
        "gpt5",
        "chatgpt_deep_research",
    ],
    "claude": [
        "sonnet_3.5",
        "sonnet_4",
        "sonnet_4.5",
        "haiku_4.5",
        "opus_4.5",
        "opus_4.6",
        "sonnet_4.6",
        "deep_research",
    ],
    "gemini": [
        "2.0_flash",
        "2.5_pro_preview",
        "2.5_flash",
        "2.5_pro_stable",
        "3_pro",
        "3_flash",
        "3.1_pro",
    ],
    "google": ["gemini_deep_research"],
    "deepseek": ["v3"],
    "zhipu": ["glm_5"],
}
MODEL_LABELS = {
    ("openai", "gpt4o"): "GPT-4o",
    ("openai", "o1_preview"): "o1-preview",
    ("openai", "o1_mini"): "o1-mini",
    ("openai", "o1"): "o1",
    ("openai", "o1_pro"): "o1-pro",
    ("openai", "o3_mini"): "o3-mini",
    ("openai", "o3_high"): "o3 (high)",
    ("openai", "o4_mini"): "o4-mini",
    ("openai", "gpt5"): "GPT-5",
    ("openai", "chatgpt_deep_research"): "Deep Research",
    ("claude", "sonnet_3.5"): "Sonnet 3.5",
    ("claude", "sonnet_4"): "Sonnet 4",
    ("claude", "sonnet_4.5"): "Sonnet 4.5",
    ("claude", "haiku_4.5"): "Haiku 4.5",
    ("claude", "opus_4.5"): "Opus 4.5",
    ("claude", "opus_4.6"): "Opus 4.6",
    ("claude", "sonnet_4.6"): "Sonnet 4.6",
    ("claude", "deep_research"): "Deep Research",
    ("gemini", "2.0_flash"): "2.0 Flash",
    ("gemini", "2.5_pro_preview"): "2.5 Pro Prev",
    ("gemini", "2.5_flash"): "2.5 Flash",
    ("gemini", "2.5_pro_stable"): "2.5 Pro",
    ("gemini", "3_pro"): "3 Pro",
    ("gemini", "3_flash"): "3 Flash",
    ("gemini", "3.1_pro"): "3.1 Pro",
    ("google", "gemini_deep_research"): "Gemini Deep Research",
    ("deepseek", "v3"): "DeepSeek V3",
    ("zhipu", "glm_5"): "GLM-5",
}
FAMILY_LABELS = {
    "openai": "OpenAI",
    "claude": "Claude",
    "gemini": "Gemini",
    "google": "Google",
    "deepseek": "DeepSeek",
    "zhipu": "Zhipu",
}


def load_scores(csv_path: Path, pipeline: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "pipeline" not in df.columns:
        df.insert(0, "pipeline", "aerobiome")
    if pipeline is not None:
        df = df[df["pipeline"] == pipeline].copy()
    for dim in DIMENSIONS:
        df[dim] = df[dim].astype(str).str.strip()
    df["step_number"] = df["step_number"].astype(int)
    return df


def composite_score(row: pd.Series) -> float | None:
    values = []
    for dim in DIMENSIONS:
        raw = str(row.get(dim, "")).strip().upper()
        score = SCORE_MAP[dim].get(raw)
        if score is None:
            return None
        values.append(score)
    return float(np.mean(values))


def ordered_models(df: pd.DataFrame) -> list[tuple[str, str]]:
    present = set(zip(df["model_family"], df["model_version"]))
    ordered = []
    for family in FAMILY_ORDER:
        for version in VERSION_ORDER.get(family, []):
            key = (family, version)
            if key in present:
                ordered.append(key)
    ordered.extend(sorted(present - set(ordered)))
    return ordered


def build_matrix(df: pd.DataFrame, pipeline: str = "aerobiome") -> tuple[np.ndarray, list[str], list[str], list[tuple[str, int, int]]]:
    models = ordered_models(df)
    steps = sorted(df["step_number"].unique())
    matrix = np.full((len(models), len(steps)), np.nan)

    for row_idx, key in enumerate(models):
        family, version = key
        subset = df[(df["model_family"] == family) & (df["model_version"] == version)]
        for _, row in subset.iterrows():
            step_idx = steps.index(int(row["step_number"]))
            score = composite_score(row)
            if score is not None:
                matrix[row_idx, step_idx] = score

    family_spans = []
    start = 0
    while start < len(models):
        family = models[start][0]
        end = start
        while end + 1 < len(models) and models[end + 1][0] == family:
            end += 1
        family_spans.append((family, start, end))
        start = end + 1

    y_labels = [MODEL_LABELS.get(model, f"{model[0]}/{model[1]}") for model in models]
    step_labels = PIPELINE_STEP_LABELS.get(pipeline, STEP_LABELS_AEROBIOME)
    x_labels = [step_labels.get(step, f"Step {step}") for step in steps]
    return matrix, y_labels, x_labels, family_spans


def plot_heatmap(matrix: np.ndarray, y_labels: list[str], x_labels: list[str],
                 family_spans: list[tuple[str, int, int]], output_path: Path,
                 title: str = "LLM Nanopore Metagenomics Pipeline Evaluation") -> None:
    fig_height = max(14, len(y_labels) * 0.45)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    cmap = LinearSegmentedColormap.from_list(
        "score",
        ["#e74c3c", "#f39c12", "#2ecc71"],
        N=256,
    )
    cmap.set_bad(color="#f5f5f5")
    masked = np.ma.masked_invalid(matrix)
    ax.imshow(masked, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, fontsize=9)
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels, fontsize=9)

    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks([(start + end) / 2 for _, start, end in family_spans])
    ax2.set_yticklabels(
        [FAMILY_LABELS.get(family, family.title()) for family, _, _ in family_spans],
        fontsize=10,
        fontweight="bold",
    )

    for i in range(len(y_labels) + 1):
        ax.axhline(i - 0.5, color="white", linewidth=1.2)
    for j in range(len(x_labels) + 1):
        ax.axvline(j - 0.5, color="white", linewidth=1.2)

    for _, start, end in family_spans:
        ax.axhline(start - 0.5, color="#cbd5e1", linewidth=2)
        ax.axhline(end + 0.5, color="#cbd5e1", linewidth=2)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            if np.isnan(value):
                ax.text(j, i, "—", ha="center", va="center", fontsize=8, color="#94a3b8")
            else:
                color = "white" if value < 0.35 else "black"
                ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=8,
                        fontweight="bold", color=color)

    legend = [
        mpatches.Patch(color="#2ecc71", label="Correct (1.0)"),
        mpatches.Patch(color="#f39c12", label="Partial (0.5)"),
        mpatches.Patch(color="#e74c3c", label="Incorrect (0.0)"),
        mpatches.Patch(color="#f5f5f5", label="Not evaluated"),
    ]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0, -0.07),
              ncol=4, fontsize=8, frameon=False)

    ax.set_title(
        title,
        fontsize=13,
        fontweight="bold",
        pad=16,
    )
    ax.set_xlabel("Pipeline Step", fontsize=10, labelpad=8)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "results" / "tables" / "scoring_matrix.csv"
    figs = repo_root / "results" / "figures"

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.", file=sys.stderr)
        return 1

    # Detect pipelines
    df_all = pd.read_csv(csv_path)
    if "pipeline" not in df_all.columns:
        pipelines = ["aerobiome"]
    else:
        pipelines = sorted(df_all["pipeline"].unique())

    for pipeline in pipelines:
        df = load_scores(csv_path, pipeline=pipeline)
        if df.empty:
            continue
        matrix, y_labels, x_labels, family_spans = build_matrix(df, pipeline=pipeline)
        title_label = PIPELINE_TITLES.get(pipeline, pipeline.title())
        title = f"{title_label} — LLM Evaluation ({len(y_labels)} entries)"
        if pipeline == "aerobiome":
            output_path = figs / "scoring_heatmap.png"
        else:
            output_path = figs / f"{pipeline}_scoring_heatmap.png"
        plot_heatmap(matrix, y_labels, x_labels, family_spans, output_path, title=title)
        print(f"Heatmap saved to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
