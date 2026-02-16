#!/usr/bin/env python3
"""
Aerobiome analysis report generator.

Aggregates QC metrics, contamination statistics, taxonomic profiles,
and AMR findings across all samples into a single HTML report. Designed
for rapid interpretation of ultra-low biomass air monitoring results.
"""

import json
import sys
from pathlib import Path


def parse_nanostats(stats_file: str) -> dict:
    """Extract key metrics from NanoPlot NanoStats.txt."""
    metrics = {}
    with open(stats_file) as fh:
        for line in fh:
            if ":" in line:
                key, val = line.split(":", 1)
                metrics[key.strip()] = val.strip()
    return metrics


def parse_bracken(bracken_file: str, top_n: int = 15) -> list[dict]:
    """Parse Bracken species report and return top N taxa."""
    taxa = []
    with open(bracken_file) as fh:
        header = fh.readline().strip().split("\t")
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 7:
                taxa.append({
                    "name": fields[0],
                    "taxonomy_id": fields[1],
                    "reads": int(fields[5]),
                    "fraction": float(fields[6])
                })
    taxa.sort(key=lambda x: x["reads"], reverse=True)
    return taxa[:top_n]


def generate_html(samples, qc_data, decontam_data, taxonomy_data, amr_data, sites):
    """Generate HTML report."""
    html = ["""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Aerobiome Analysis Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #38bdf8; margin-bottom: 0.5rem; font-size: 1.8rem; }
        h2 { color: #7dd3fc; margin: 2rem 0 1rem; font-size: 1.3rem; border-bottom: 1px solid #1e3a5f; padding-bottom: 0.5rem; }
        h3 { color: #bae6fd; margin: 1.5rem 0 0.5rem; font-size: 1.1rem; }
        .subtitle { color: #94a3b8; margin-bottom: 2rem; }
        table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        th { background: #1e293b; color: #7dd3fc; text-align: left; padding: 0.6rem 0.8rem; font-size: 0.85rem; }
        td { padding: 0.5rem 0.8rem; border-bottom: 1px solid #1e293b; font-size: 0.85rem; }
        tr:hover { background: #1e293b; }
        .metric { display: inline-block; background: #1e293b; border-radius: 8px; padding: 1rem 1.5rem; margin: 0.5rem; min-width: 160px; }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #38bdf8; }
        .metric-label { font-size: 0.75rem; color: #94a3b8; margin-top: 0.3rem; }
        .warning { color: #fbbf24; }
        .good { color: #4ade80; }
        .bar { height: 8px; background: #1e3a5f; border-radius: 4px; overflow: hidden; }
        .bar-fill { height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); border-radius: 4px; }
        .site-tag { display: inline-block; background: #312e81; color: #a5b4fc; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
    </style>
</head>
<body>
<div class="container">
    <h1>🌬️ Aerobiome Analysis Report</h1>
    <p class="subtitle">Ultra-low biomass air metagenomics — nanopore sequencing</p>
"""]

    # --- Overview metrics ---
    total_reads = sum(d.get("reads_input", 0) for d in decontam_data.values())
    total_kept = sum(d.get("reads_kept", 0) for d in decontam_data.values())
    total_removed = sum(d.get("reads_removed", 0) for d in decontam_data.values())
    pct_kept = round(100 * total_kept / total_reads, 1) if total_reads > 0 else 0

    html.append(f"""
    <h2>Overview</h2>
    <div>
        <div class="metric"><div class="metric-value">{len(samples)}</div><div class="metric-label">Samples analyzed</div></div>
        <div class="metric"><div class="metric-value">{total_reads:,}</div><div class="metric-label">Total reads</div></div>
        <div class="metric"><div class="metric-value">{total_kept:,}</div><div class="metric-label">Reads after decontamination</div></div>
        <div class="metric"><div class="metric-value">{pct_kept}%</div><div class="metric-label">Retention rate</div></div>
    </div>
    """)

    # --- Per-sample QC ---
    html.append("<h2>Contamination Control</h2>")
    html.append("<table><tr><th>Sample</th><th>Reads In</th><th>Removed</th><th>% Removed</th><th>Contaminant Taxa</th><th>Retention</th></tr>")
    for sample in samples:
        d = decontam_data.get(sample, {})
        pct = d.get("pct_removed", 0)
        color = "good" if pct < 30 else "warning"
        html.append(f"""<tr>
            <td>{sample}</td>
            <td>{d.get('reads_input', 0):,}</td>
            <td>{d.get('reads_removed', 0):,}</td>
            <td class="{color}">{pct}%</td>
            <td>{d.get('contaminant_taxa_count', 0)}</td>
            <td><div class="bar" style="width:120px"><div class="bar-fill" style="width:{100-pct}%"></div></div></td>
        </tr>""")
    html.append("</table>")

    # --- Top species per sample ---
    html.append("<h2>Species-Level Taxonomic Profiles</h2>")
    for sample in samples:
        taxa = taxonomy_data.get(sample, [])
        if taxa:
            html.append(f"<h3>{sample}</h3>")
            html.append("<table><tr><th>Species</th><th>Reads</th><th>Relative Abundance</th></tr>")
            for t in taxa[:10]:
                pct = round(t["fraction"] * 100, 2)
                html.append(f"""<tr>
                    <td><em>{t['name']}</em></td>
                    <td>{t['reads']:,}</td>
                    <td>{pct}% <div class="bar" style="width:200px;display:inline-block;vertical-align:middle"><div class="bar-fill" style="width:{min(pct, 100)}%"></div></div></td>
                </tr>""")
            html.append("</table>")

    # --- Footer ---
    html.append("""
    <hr style="border-color: #1e3a5f; margin-top: 3rem;">
    <p style="color: #64748b; font-size: 0.75rem; margin-top: 1rem;">
        Generated by aerobiome-pipeline · Reska T, Pozdniakova S, Urban L (2024)
    </p>
</div>
</body>
</html>""")

    return "\n".join(html)


def main():
    samples = snakemake.params.samples
    sites = snakemake.params.study_sites

    # Load data
    qc_data = {}
    for f in snakemake.input.qc_stats:
        sample = Path(f).parent.name.replace("_nanoplot", "")
        qc_data[sample] = parse_nanostats(f)

    decontam_data = {}
    for f in snakemake.input.decontam_stats:
        sample = Path(f).stem.replace("_decontam_stats", "")
        with open(f) as fh:
            decontam_data[sample] = json.load(fh)

    taxonomy_data = {}
    for f in snakemake.input.taxonomy:
        sample = Path(f).stem.replace("_bracken_species", "")
        taxonomy_data[sample] = parse_bracken(f)

    # Generate report
    html = generate_html(samples, qc_data, decontam_data, taxonomy_data, {}, sites)

    with open(snakemake.output.html, "w") as fh:
        fh.write(html)


if __name__ == "__main__":
    main()
