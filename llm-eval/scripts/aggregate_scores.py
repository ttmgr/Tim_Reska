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

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from scoring import (
    DIMENSIONS,
    FAMILY_ORDER,
    FULLY_CORRECT,
    PIPELINE_LABELS,
    PIPELINE_STEP_COUNTS,
    SCORE_MAP,
    family_label,
    is_step_fully_correct,
    model_label,
    ordered_models,
    slugify,
)


def load_scores(csv_path: Path, pipeline: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Handle pipeline column — if absent, treat all rows as aerobiome
    if "pipeline" not in df.columns:
        df.insert(0, "pipeline", "aerobiome")
    if pipeline is not None:
        df = df[df["pipeline"] == pipeline].copy()
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


def first_fully_correct(df: pd.DataFrame, expected_steps: int | None = None) -> dict[str, str | None]:
    if expected_steps is None:
        # Infer from pipeline column if present
        pipelines = df["pipeline"].unique() if "pipeline" in df.columns else ["aerobiome"]
        expected_steps = PIPELINE_STEP_COUNTS.get(pipelines[0], df["step_number"].nunique())
    results = {}
    for family in preferred_family_sequence(df):
        results[family] = None
        family_models = [m for m in ordered_models(df) if m[0] == family]
        for fam, version in family_models:
            version_df = df[(df["model_family"] == fam) & (df["model_version"] == version)]
            if len(version_df) != expected_steps:
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


def write_by_step(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered_index = {key: i for i, key in enumerate(ordered_models(df))}
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
    model_order = ordered_models(df)
    for family, version in model_order:
        subset = df[(df["model_family"] == family) & (df["model_version"] == version)].copy()
        subset = subset.sort_values("step_number")
        # Determine expected step count from pipeline column
        pipelines = subset["pipeline"].unique() if "pipeline" in subset.columns else ["aerobiome"]
        expected_steps = PIPELINE_STEP_COUNTS.get(pipelines[0], subset["step_number"].nunique())
        full_correct = len(subset) == expected_steps and all(subset.apply(is_step_fully_correct, axis=1))
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
    model_order = ordered_models(df)
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
        f"- Evaluated entries: {len(model_order)}",
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
        versions = [model_label(fam, version) for fam, version in model_order if fam == family]
        lines.append(f"- **{family_label(family)} ({len(versions)}):** " + " | ".join(versions))

    return "\n".join(lines).rstrip() + "\n"


def run_pipeline(repo_root: Path, csv_path: Path, pipeline: str) -> str:
    """Generate all outputs for a single pipeline."""
    if pipeline == "aerobiome":
        eval_dir = repo_root / "evaluations"
    else:
        eval_dir = repo_root / "evaluations" / pipeline

    summary_path = eval_dir / "summary_generated.md"
    by_step_dir = eval_dir / "by_step"
    by_model_dir = eval_dir / "by_model"

    df = load_scores(csv_path, pipeline=pipeline)
    if df.empty:
        return ""

    expected_steps = PIPELINE_STEP_COUNTS.get(pipeline, df["step_number"].nunique())
    write_by_step(df, by_step_dir)
    write_by_model(df, by_model_dir)
    summary = build_summary(df)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary)
    return summary


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "results" / "tables" / "scoring_matrix.csv"

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.", file=sys.stderr)
        return 1

    # Detect which pipelines are present in the CSV
    df_all = pd.read_csv(csv_path)
    if "pipeline" not in df_all.columns:
        pipelines = ["aerobiome"]
    else:
        pipelines = sorted(df_all["pipeline"].unique())

    for pipeline in pipelines:
        summary = run_pipeline(repo_root, csv_path, pipeline)
        if summary:
            label = PIPELINE_LABELS.get(pipeline, pipeline.title())
            print(f"\n{'=' * 60}")
            print(f"  {label} Pipeline")
            print(f"{'=' * 60}\n")
            sys.stdout.write(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
