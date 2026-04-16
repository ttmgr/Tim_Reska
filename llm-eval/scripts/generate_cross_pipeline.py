#!/usr/bin/env python3
"""
Generate cross-pipeline comparison figures.

Compares model performance across the aerobiome and wetland pipelines:
1. Scatter plot: aerobiome vs wetland composite scores per model
2. Bar chart: performance gap (aerobiome - wetland) per model

Requires both pipelines to have scored data in the CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCORE_MAP = {
    "tool_selection": {"C": 1.0, "A": 0.5, "I": 0.0},
    "parameter_accuracy": {"C": 1.0, "P": 0.5, "I": 0.0},
    "output_compatibility": {"P": 1.0, "F": 0.0},
    "scientific_validity": {"S": 1.0, "Q": 0.5, "I": 0.0},
    "executability": {"R": 1.0, "M": 0.5, "N": 0.0},
}

DIMENSIONS = list(SCORE_MAP.keys())

FAMILY_COLORS = {
    "openai": "#10b981",
    "claude": "#8b5cf6",
    "gemini": "#f43f5e",
    "google": "#f59e0b",
    "deepseek": "#3b82f6",
    "zhipu": "#6b7280",
}
FAMILY_LABELS = {
    "openai": "OpenAI",
    "claude": "Claude",
    "gemini": "Gemini",
    "google": "Google",
    "deepseek": "DeepSeek",
    "zhipu": "Zhipu",
}
MODEL_LABELS = {
    ("openai", "gpt4o"): "GPT-4o",
    ("openai", "o1_preview"): "o1-prev",
    ("openai", "o1_mini"): "o1-mini",
    ("openai", "o1"): "o1",
    ("openai", "o1_pro"): "o1-pro",
    ("openai", "o3_mini"): "o3-mini",
    ("openai", "o3_high"): "o3",
    ("openai", "o4_mini"): "o4-mini",
    ("openai", "gpt5"): "GPT-5",
    ("openai", "chatgpt_deep_research"): "DR",
    ("claude", "sonnet_3.5"): "S3.5",
    ("claude", "sonnet_4"): "S4",
    ("claude", "sonnet_4.5"): "S4.5",
    ("claude", "haiku_4.5"): "H4.5",
    ("claude", "opus_4.5"): "Op4.5",
    ("claude", "opus_4.6"): "Op4.6",
    ("claude", "sonnet_4.6"): "S4.6",
    ("claude", "deep_research"): "DR",
    ("gemini", "2.0_flash"): "2.0F",
    ("gemini", "2.5_pro_preview"): "2.5PP",
    ("gemini", "2.5_flash"): "2.5F",
    ("gemini", "2.5_pro_stable"): "2.5P",
    ("gemini", "3_pro"): "3P",
    ("gemini", "3_flash"): "3F",
    ("gemini", "3.1_pro"): "3.1P",
    ("google", "gemini_deep_research"): "GDR",
    ("deepseek", "v3"): "V3",
    ("zhipu", "glm_5"): "GLM-5",
}


def load_and_score(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "pipeline" not in df.columns:
        return pd.DataFrame()
    for dim in DIMENSIONS:
        df[f"{dim}_num"] = df[dim].map(SCORE_MAP[dim])
    df["composite"] = df[[f"{d}_num" for d in DIMENSIONS]].mean(axis=1)
    return df


def model_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Average composite score per model per pipeline."""
    return (
        df.groupby(["pipeline", "model_family", "model_version"])["composite"]
        .mean()
        .reset_index()
    )


def plot_scatter(avgs: pd.DataFrame, output_path: Path) -> None:
    """Scatter plot: aerobiome score (x) vs wetland score (y) per model."""
    aero = avgs[avgs["pipeline"] == "aerobiome"].set_index(["model_family", "model_version"])
    wet = avgs[avgs["pipeline"] == "wetland"].set_index(["model_family", "model_version"])
    common = aero.index.intersection(wet.index)

    if len(common) == 0:
        print("No models with both pipeline scores — skipping scatter plot.")
        return

    fig, ax = plt.subplots(figsize=(8, 8))

    for family, version in common:
        x = aero.loc[(family, version), "composite"]
        y = wet.loc[(family, version), "composite"]
        color = FAMILY_COLORS.get(family, "#6b7280")
        label = MODEL_LABELS.get((family, version), f"{family}/{version}")
        ax.scatter(x, y, c=color, s=60, zorder=3, edgecolors="white", linewidths=0.5)
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(5, 5),
                    fontsize=6, color=color, fontweight="bold")

    # Diagonal line (equal performance)
    ax.plot([0, 1], [0, 1], "--", color="#94a3b8", linewidth=1, alpha=0.5)
    ax.text(0.85, 0.78, "Equal\nperformance", fontsize=7, color="#94a3b8", ha="center")

    # Family legend
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=8, label=FAMILY_LABELS.get(f, f))
        for f, c in FAMILY_COLORS.items()
        if any(m[0] == f for m in common)
    ]
    ax.legend(handles=handles, fontsize=8, frameon=False, loc="upper left")

    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Aerobiome Pipeline — Average Composite Score", fontsize=10)
    ax.set_ylabel("Wetland Pipeline — Average Composite Score", fontsize=10)
    ax.set_title("Cross-Pipeline Performance Comparison", fontsize=12, fontweight="bold", pad=12)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Cross-pipeline scatter saved to {output_path}")
    plt.close()


def plot_gap(avgs: pd.DataFrame, output_path: Path) -> None:
    """Bar chart: performance gap (aerobiome - wetland) per model, sorted."""
    aero = avgs[avgs["pipeline"] == "aerobiome"].set_index(["model_family", "model_version"])
    wet = avgs[avgs["pipeline"] == "wetland"].set_index(["model_family", "model_version"])
    common = aero.index.intersection(wet.index)

    if len(common) == 0:
        print("No models with both pipeline scores — skipping gap chart.")
        return

    gaps = []
    for family, version in common:
        gap = aero.loc[(family, version), "composite"] - wet.loc[(family, version), "composite"]
        label = MODEL_LABELS.get((family, version), f"{family}/{version}")
        color = FAMILY_COLORS.get(family, "#6b7280")
        gaps.append((label, gap, color, family))

    gaps.sort(key=lambda x: x[1], reverse=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(gaps) * 0.35)))
    y_pos = np.arange(len(gaps))
    bars = ax.barh(y_pos, [g[1] for g in gaps], color=[g[2] for g in gaps],
                   height=0.6, edgecolor="white", linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([g[0] for g in gaps], fontsize=8)
    ax.axvline(0, color="#334155", linewidth=0.8)
    ax.set_xlabel("Performance Gap (Aerobiome - Wetland)", fontsize=9)
    ax.set_title("Pipeline Difficulty Gap per Model\n(Positive = wetland is harder)",
                 fontsize=11, fontweight="bold", color="#1e293b", pad=12)
    ax.invert_yaxis()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="x", alpha=0.15)

    for bar, (_, gap, _, _) in zip(bars, gaps):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{gap:+.2f}", va="center", fontsize=7, fontweight="bold", color="#334155")

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Cross-pipeline gap chart saved to {output_path}")
    plt.close()


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "results" / "tables" / "scoring_matrix.csv"
    figs = repo_root / "results" / "figures"

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.", file=sys.stderr)
        return 1

    df = load_and_score(csv_path)
    if df.empty:
        print("No pipeline column found in CSV — nothing to compare.")
        return 0

    pipelines = set(df["pipeline"].unique())
    if not {"aerobiome", "wetland"}.issubset(pipelines):
        print("Need both aerobiome and wetland data for cross-pipeline comparison.")
        print(f"Found: {pipelines}")
        return 0

    avgs = model_averages(df)
    plot_scatter(avgs, figs / "cross_pipeline_comparison.png")
    plot_gap(avgs, figs / "cross_pipeline_gap.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
