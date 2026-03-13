#!/usr/bin/env python3
"""
Aggregate scoring results and generate markdown summaries.

Outputs:
- evaluations/summary_generated.md
- evaluations/by_step/*.md
- evaluations/by_model/*.md

Stdout prints the exact contents of summary_generated.md.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

SCORE_MAP = {
    "tool_selection": {"C": 1.0, "A": 0.5, "I": 0.0},
    "parameter_accuracy": {"C": 1.0, "P": 0.5, "I": 0.0},
    "output_compatibility": {"P": 1.0, "F": 0.0},
    "scientific_validity": {"S": 1.0, "Q": 0.5, "I": 0.0},
    "executability": {"R": 1.0, "M": 0.5, "N": 0.0},
}

FULLY_CORRECT = {
    "tool_selection": "C",
    "parameter_accuracy": "C",
    "output_compatibility": "P",
    "scientific_validity": "S",
    "executability": "R",
}

DIMENSIONS = list(SCORE_MAP.keys())
CORE_VERSION_ORDER = {
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

FAMILY_ORDER = ["openai", "claude", "gemini", "google", "deepseek", "zhipu"]
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
    ("openai", "o1_preview"): "o1-preview",
    ("openai", "o1_mini"): "o1-mini",
    ("openai", "o1"): "o1",
    ("openai", "o1_pro"): "o1-pro",
    ("openai", "o3_mini"): "o3-mini",
    ("openai", "o3_high"): "o3 (high reasoning)",
    ("openai", "o4_mini"): "o4-mini",
    ("openai", "gpt5"): "GPT-5",
    ("openai", "chatgpt_deep_research"): "ChatGPT Deep Research",
    ("claude", "sonnet_3.5"): "Sonnet 3.5",
    ("claude", "sonnet_4"): "Sonnet 4",
    ("claude", "sonnet_4.5"): "Sonnet 4.5",
    ("claude", "haiku_4.5"): "Haiku 4.5",
    ("claude", "opus_4.5"): "Opus 4.5",
    ("claude", "opus_4.6"): "Opus 4.6",
    ("claude", "sonnet_4.6"): "Sonnet 4.6",
    ("claude", "deep_research"): "Claude Deep Research",
    ("gemini", "2.0_flash"): "Gemini 2.0 Flash",
    ("gemini", "2.5_pro_preview"): "Gemini 2.5 Pro Preview",
    ("gemini", "2.5_flash"): "Gemini 2.5 Flash",
    ("gemini", "2.5_pro_stable"): "Gemini 2.5 Pro",
    ("gemini", "3_pro"): "Gemini 3 Pro",
    ("gemini", "3_flash"): "Gemini 3 Flash",
    ("gemini", "3.1_pro"): "Gemini 3.1 Pro",
    ("google", "gemini_deep_research"): "Gemini Deep Research",
    ("deepseek", "v3"): "DeepSeek V3",
    ("zhipu", "glm_5"): "GLM-5",
}


def load_scores(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    for dim in DIMENSIONS:
        df[dim] = df[dim].astype(str).str.strip().replace("nan", "")
        df[f"{dim}_num"] = df[dim].map(SCORE_MAP[dim])
    df["step_number"] = df["step_number"].astype(int)
    df["composite_score"] = df[[f"{dim}_num" for dim in DIMENSIONS]].mean(axis=1)
    return df


def model_key(row_or_pair) -> tuple[str, str]:
    if isinstance(row_or_pair, tuple):
        return row_or_pair
    return row_or_pair["model_family"], row_or_pair["model_version"]


def preferred_models(df: pd.DataFrame) -> list[tuple[str, str]]:
    seen = set(zip(df["model_family"], df["model_version"]))
    ordered = []

    for family in FAMILY_ORDER:
        for version in CORE_VERSION_ORDER.get(family, []):
            key = (family, version)
            if key in seen:
                ordered.append(key)

    extras = sorted(seen - set(ordered))
    ordered.extend(extras)
    return ordered


def model_label(family: str, version: str) -> str:
    return MODEL_LABELS.get((family, version), f"{family}/{version}")


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(family, family.title())


def is_step_fully_correct(row: pd.Series) -> bool:
    return all(row[dim] == expected for dim, expected in FULLY_CORRECT.items())


def first_fully_correct(df: pd.DataFrame) -> dict[str, str | None]:
    results = {}
    for family in preferred_family_sequence(df):
        results[family] = None
        family_models = [m for m in preferred_models(df) if m[0] == family]
        for fam, version in family_models:
            version_df = df[(df["model_family"] == fam) & (df["model_version"] == version)]
            if len(version_df) != 7:
                continue
            if all(is_step_fully_correct(row) for _, row in version_df.iterrows()):
                results[family] = version
                break
    return results


def preferred_family_sequence(df: pd.DataFrame) -> list[str]:
    families = list(dict.fromkeys(df["model_family"]))
    ordered = [f for f in FAMILY_ORDER if f in families]
    ordered.extend(sorted(set(families) - set(ordered)))
    return ordered


def hardest_steps(df: pd.DataFrame) -> list[tuple[int, str, float]]:
    out = []
    for step_num in sorted(df["step_number"].unique()):
        subset = df[df["step_number"] == step_num]
        out.append((step_num, subset["step_name"].iloc[0], subset["composite_score"].mean()))
    return sorted(out, key=lambda item: item[2])


def most_common_failures(df: pd.DataFrame) -> dict[int, dict[str, str]]:
    out = {}
    for step_num in sorted(df["step_number"].unique()):
        subset = df[df["step_number"] == step_num]
        step_failures = {}
        for dim in DIMENSIONS:
            failures = [
                value for value in subset[dim].tolist()
                if value and value != FULLY_CORRECT[dim]
            ]
            if failures:
                value, count = Counter(failures).most_common(1)[0]
                step_failures[dim] = f"{value} ({count}x)"
        out[step_num] = step_failures
    return out


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def write_by_step(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered_index = {key: i for i, key in enumerate(preferred_models(df))}
    for step_num in sorted(df["step_number"].unique()):
        subset = df[df["step_number"] == step_num].copy()
        step_name = subset["step_name"].iloc[0]
        full_correct = int(subset.apply(is_step_fully_correct, axis=1).sum())
        failures = most_common_failures(subset)[step_num]

        lines = [
            f"# Step {step_num}: {step_name.replace('_', ' ').title()}",
            "",
            f"- Models evaluated: {len(subset)}",
            f"- Fully correct responses: {full_correct}/{len(subset)}",
            f"- Average composite score: {subset['composite_score'].mean():.2f}",
            "",
            "## Dominant Non-Correct Labels",
            "",
        ]
        for dim in DIMENSIONS:
            if dim in failures:
                lines.append(f"- `{dim}`: {failures[dim]}")
        lines.extend([
            "",
            "## Model-Level Results",
            "",
            "| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |",
            "|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|",
        ])
        subset = subset.sort_values(
            by=["model_family", "model_version"],
            key=lambda col: col,
        )
        rows = sorted(
            subset.to_dict("records"),
            key=lambda row: ordered_index[(row["model_family"], row["model_version"])],
        )
        for row in rows:
            lines.append(
                "| {family} | {model} | {score:.2f} | {tool} | {params} | {output} | {science} | {exec_} | {notes} |".format(
                    family=family_label(row["model_family"]),
                    model=model_label(row["model_family"], row["model_version"]),
                    score=row["composite_score"],
                    tool=row["tool_selection"],
                    params=row["parameter_accuracy"],
                    output=row["output_compatibility"],
                    science=row["scientific_validity"],
                    exec_=row["executability"],
                    notes=row["notes"].replace("|", "\\|"),
                )
            )

        filename = output_dir / f"step_{step_num:02d}_{slugify(step_name)}.md"
        filename.write_text("\n".join(lines) + "\n")


def write_by_model(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered_models = preferred_models(df)
    for family, version in ordered_models:
        subset = df[(df["model_family"] == family) & (df["model_version"] == version)].copy()
        subset = subset.sort_values("step_number")
        full_correct = len(subset) == 7 and all(subset.apply(is_step_fully_correct, axis=1))
        lines = [
            f"# {model_label(family, version)}",
            "",
            f"- Family: {family_label(family)}",
            f"- Steps scored: {len(subset)}",
            f"- Average composite score: {subset['composite_score'].mean():.2f}",
            f"- Fully correct end-to-end pipeline: {'Yes' if full_correct else 'No'}",
            "",
            "## Step-Level Results",
            "",
            "| Step | Composite | Tool | Params | Output | Science | Exec | Notes |",
            "|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|",
        ]
        for row in subset.to_dict("records"):
            lines.append(
                "| {step}. {name} | {score:.2f} | {tool} | {params} | {output} | {science} | {exec_} | {notes} |".format(
                    step=row["step_number"],
                    name=row["step_name"].replace("_", " "),
                    score=row["composite_score"],
                    tool=row["tool_selection"],
                    params=row["parameter_accuracy"],
                    output=row["output_compatibility"],
                    science=row["scientific_validity"],
                    exec_=row["executability"],
                    notes=row["notes"].replace("|", "\\|"),
                )
            )

        filename = output_dir / f"{family}_{slugify(version)}.md"
        filename.write_text("\n".join(lines) + "\n")


def build_summary(df: pd.DataFrame) -> str:
    ordered_models = preferred_models(df)
    first_correct = first_fully_correct(df)
    steps_ranked = hardest_steps(df)
    failures = most_common_failures(df)

    lines = [
        "# Aggregated Scoring Results",
        "",
        "*Auto-generated from `results/tables/scoring_matrix.csv`.*",
        "",
        "## Dataset Scope",
        "",
        f"- Evaluated entries: {len(ordered_models)}",
        f"- Scored step-results: {len(df)}",
        f"- Pipeline steps: {df['step_number'].nunique()}",
        "",
        "## First Fully Correct Pipeline per Family",
        "",
    ]
    for family in preferred_family_sequence(df):
        winner = first_correct.get(family)
        status = model_label(family, winner) if winner else "None"
        lines.append(f"- **{family_label(family)}:** {status}")

    lines.extend([
        "",
        "## Steps Ranked by Difficulty",
        "",
        "| Rank | Step | Average Composite Score |",
        "|:-----|:-----|------------------------:|",
    ])
    for rank, (step_num, step_name, avg_score) in enumerate(steps_ranked, start=1):
        lines.append(f"| {rank} | {step_num}. {step_name.replace('_', ' ')} | {avg_score:.2f} |")

    lines.extend([
        "",
        "## Dominant Non-Correct Labels by Step",
        "",
    ])
    for step_num in sorted(failures):
        step_name = df[df["step_number"] == step_num]["step_name"].iloc[0].replace("_", " ")
        lines.append(f"### Step {step_num}: {step_name.title()}")
        lines.append("")
        for dim in DIMENSIONS:
            if dim in failures[step_num]:
                lines.append(f"- `{dim}`: {failures[step_num][dim]}")
        lines.append("")

    lines.extend([
        "## Family Coverage",
        "",
    ])
    for family in preferred_family_sequence(df):
        versions = [model_label(fam, version) for fam, version in ordered_models if fam == family]
        lines.append(f"- **{family_label(family)} ({len(versions)}):** " + " | ".join(versions))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "results" / "tables" / "scoring_matrix.csv"
    summary_path = repo_root / "evaluations" / "summary_generated.md"
    by_step_dir = repo_root / "evaluations" / "by_step"
    by_model_dir = repo_root / "evaluations" / "by_model"

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.", file=sys.stderr)
        return 1

    df = load_scores(csv_path)
    write_by_step(df, by_step_dir)
    write_by_model(df, by_model_dir)
    summary = build_summary(df)
    summary_path.write_text(summary)
    sys.stdout.write(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
