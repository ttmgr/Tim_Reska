"""
cli.py — Click-based CLI entry point for medrisk-fetch.

Commands:
  medrisk-fetch list-datasets <source> [--filter key=val ...]
  medrisk-fetch inspect <source> <dataset-id>
  medrisk-fetch fetch <source> [--dataset-id ID ...] [--study NAME] [--output-dir DIR] [--force-refresh]
  medrisk-fetch export <input-dir> --format {survival|multistate|cgm} --output <path>
  medrisk-fetch sources
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from medrisk.fetch._settings import AppSettings


@click.group()
@click.option(
    "--config-dir",
    default="configs",
    type=click.Path(),
    envvar="MEDRISK_FETCH_CONFIG_DIR",
    help="Path to configs/ directory",
    show_default=True,
)
@click.option(
    "--cache-dir",
    default=".cache/medrisk_fetch",
    type=click.Path(),
    envvar="MEDRISK_FETCH_CACHE_DIR",
    show_default=True,
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    envvar="MEDRISK_FETCH_LOG_LEVEL",
    show_default=True,
)
@click.option(
    "--log-file",
    default=None,
    type=click.Path(),
    help="Append logs to this file in addition to stderr",
)
@click.pass_context
def main(ctx: click.Context, config_dir: str, cache_dir: str, log_level: str, log_file) -> None:
    """medrisk-fetch: Programmatic discovery and download of public health cohort data."""
    settings = AppSettings(
        config_dir=Path(config_dir),
        cache_dir=Path(cache_dir),
        log_level=log_level.upper(),
        log_file=Path(log_file) if log_file else None,
    )
    settings.configure_logging()
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


@main.command("sources")
@click.pass_context
def list_sources_cmd(ctx: click.Context) -> None:
    """List all registered data source adapters."""
    from medrisk.fetch._pipeline import PipelineRunner

    runner = PipelineRunner(ctx.obj["settings"])
    sources = runner.available_sources()
    click.echo("Available sources:")
    for s in sources:
        click.echo(f"  {s}")


@main.command("list-datasets")
@click.argument("source")
@click.option(
    "--filter",
    "filters",
    multiple=True,
    metavar="KEY=VALUE",
    help="Filter key=value pairs (e.g. --filter cycle=2017-2018 --filter domain=labs)",
)
@click.option("--json-out", is_flag=True, help="Output as JSON")
@click.pass_context
def list_datasets_cmd(ctx: click.Context, source: str, filters: tuple, json_out: bool) -> None:
    """List available datasets for SOURCE adapter."""
    from medrisk.fetch._pipeline import PipelineRunner

    runner = PipelineRunner(ctx.obj["settings"])
    parsed_filters: dict = {}
    for f in filters:
        if "=" in f:
            k, v = f.split("=", 1)
            parsed_filters[k.strip()] = v.strip()
    try:
        datasets = runner.list_datasets(source, parsed_filters or None)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if json_out:
        import dataclasses

        click.echo(json.dumps([dataclasses.asdict(d) for d in datasets], indent=2, default=str))
    else:
        click.echo(f"Datasets for source '{source}' ({len(datasets)} found):")
        for ds in datasets:
            auth_flag = " [auth required]" if ds.requires_auth else ""
            click.echo(f"  {ds.dataset_id}{auth_flag}")
            click.echo(f"    {ds.title}")
            if ds.url:
                click.echo(f"    URL: {ds.url}")


@main.command("inspect")
@click.argument("source")
@click.argument("dataset_id")
@click.pass_context
def inspect_cmd(ctx: click.Context, source: str, dataset_id: str) -> None:
    """Show metadata for a specific dataset."""
    import dataclasses

    from medrisk.fetch._pipeline import PipelineRunner

    runner = PipelineRunner(ctx.obj["settings"])
    try:
        info = runner.inspect(source, dataset_id)
    except (KeyError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(json.dumps(dataclasses.asdict(info), indent=2, default=str))


@main.command("fetch")
@click.argument("source")
@click.option(
    "--dataset-id", "dataset_ids", multiple=True, help="One or more dataset IDs to fetch"
)
@click.option("--study", default=None, help="Named study from studies.yml")
@click.option(
    "--output-dir",
    default="output",
    show_default=True,
    type=click.Path(),
    help="Directory to write parquet output tables",
)
@click.option("--force-refresh", is_flag=True, help="Ignore cache and re-download")
@click.option("--no-export", is_flag=True, help="Parse only; do not write parquet output")
@click.pass_context
def fetch_cmd(
    ctx: click.Context,
    source: str,
    dataset_ids: tuple,
    study: str,
    output_dir: str,
    force_refresh: bool,
    no_export: bool,
) -> None:
    """Download and parse cohort data from SOURCE."""
    from medrisk.fetch._pipeline import PipelineRunner

    runner = PipelineRunner(ctx.obj["settings"])
    out = None if no_export else Path(output_dir)
    try:
        results = runner.run(
            source=source,
            dataset_ids=list(dataset_ids) or None,
            study=study or None,
            output_dir=out,
            force_refresh=force_refresh,
        )
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Processed {len(results)} dataset(s).")
    for ds in results:
        s = ds.summary()
        click.echo(
            f"  persons={s['persons']} measurements={s['measurements']} "
            f"events={s['events']} treatments={s['treatments']}"
        )


@main.command("export")
@click.argument("input_dir", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["survival", "multistate", "cgm"], case_sensitive=False),
    required=True,
    help="Output format",
)
@click.option("--output", required=True, type=click.Path(), help="Output file path (.parquet)")
@click.option(
    "--event-codes",
    multiple=True,
    help="Event codes to use as the endpoint for survival/multistate (e.g. --event-codes E11)",
)
@click.option("--censor-date", default=None, help="Administrative censoring date (YYYY-MM-DD)")
@click.option("--window-hours", default=24, show_default=True, help="CGM window size in hours")
@click.pass_context
def export_cmd(
    ctx: click.Context,
    input_dir: str,
    fmt: str,
    output: str,
    event_codes: tuple,
    censor_date: str,
    window_hours: int,
) -> None:
    """Re-shape stored cohort data into analysis-ready formats."""
    import pandas as pd

    from medrisk.fetch._export_helpers import (
        build_cgm_sequences,
        build_multistate_frame,
        build_survival_frame,
    )
    from medrisk.fetch._writers import read_cohort_dataset

    dataset = read_cohort_dataset(Path(input_dir))

    persons_df = (
        pd.DataFrame([p.model_dump() for p in dataset.persons])
        if dataset.persons
        else pd.DataFrame()
    )
    events_df = (
        pd.DataFrame([e.model_dump() for e in dataset.events])
        if dataset.events
        else pd.DataFrame()
    )
    measurements_df = (
        pd.DataFrame([m.model_dump() for m in dataset.measurements])
        if dataset.measurements
        else pd.DataFrame()
    )

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "survival":
        codes = list(event_codes) if event_codes else []
        if not codes:
            click.echo("Warning: no --event-codes specified; result may be empty.", err=True)
        result = build_survival_frame(
            persons_df, events_df, event_codes=codes, censor_date=censor_date or None
        )
        result.to_parquet(out_path, index=False)
        click.echo(f"Survival frame: {len(result)} rows → {out_path}")

    elif fmt == "multistate":
        click.echo(
            "multistate export requires custom transition_codes; using empty map.", err=True
        )
        result = build_multistate_frame(persons_df, events_df, states=[], transition_codes={})
        result.to_parquet(out_path, index=False)
        click.echo(f"Multistate frame: {len(result)} rows → {out_path}")

    elif fmt == "cgm":
        result = build_cgm_sequences(measurements_df, window_hours=window_hours)
        if result.empty:
            click.echo("No CGM data found.", err=True)
        else:
            result.to_parquet(out_path)
            click.echo(f"CGM sequences: {len(result)} windows → {out_path}")
