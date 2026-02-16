#!/usr/bin/env python3
"""
Integrated multi-omics surveillance report generator.

Combines results from all four analysis tracks (metagenomics, virome,
eDNA metabarcoding, AIV WGS) into a single HTML report for rapid
interpretation. Includes host-pathogen association matrix.
"""

import csv
import json
import sys
from pathlib import Path


def parse_bracken(filepath):
    taxa = []
    with open(filepath) as fh:
        header = fh.readline()
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 7:
                taxa.append({
                    "name": fields[0],
                    "reads": int(fields[5]),
                    "fraction": float(fields[6])
                })
    return sorted(taxa, key=lambda x: x["reads"], reverse=True)


def parse_amr(filepath):
    hits = []
    with open(filepath) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) >= 6:
                hits.append({"gene": fields[5] if len(fields) > 5 else "unknown",
                             "identity": fields[9] if len(fields) > 9 else "",
                             "database": fields[11] if len(fields) > 11 else ""})
    return hits


def parse_aiv(filepath):
    with open(filepath) as fh:
        line = fh.readline().strip()
        if line and not line.startswith("#"):
            fields = line.split("\t")
            return fields[1] if len(fields) > 1 else "not_detected"
    return "not_detected"


def generate_html(samples, sites, taxonomy, amr, aiv_results, associations):
    html = ["""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Wetland Surveillance Report</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Inter', system-ui, sans-serif; background: #0c1222; color: #e2e8f0; padding: 2rem; }
    .container { max-width: 1400px; margin: 0 auto; }
    h1 { color: #34d399; margin-bottom: 0.5rem; font-size: 2rem; }
    h2 { color: #6ee7b7; margin: 2.5rem 0 1rem; font-size: 1.4rem; border-bottom: 1px solid #1a3a2f; padding-bottom: 0.5rem; }
    h3 { color: #a7f3d0; margin: 1.5rem 0 0.5rem; font-size: 1.1rem; }
    .subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 1rem; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    th { background: #1a2332; color: #6ee7b7; text-align: left; padding: 0.6rem 0.8rem; font-size: 0.85rem; }
    td { padding: 0.5rem 0.8rem; border-bottom: 1px solid #1a2332; font-size: 0.85rem; }
    tr:hover { background: #1a2332; }
    .tracks { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }
    .track { background: #1a2332; border-radius: 10px; padding: 1.2rem; border-left: 3px solid; }
    .track-1 { border-color: #38bdf8; }
    .track-2 { border-color: #c084fc; }
    .track-3 { border-color: #fb923c; }
    .track-4 { border-color: #f87171; }
    .track-title { font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem; }
    .track-1 .track-title { color: #38bdf8; }
    .track-2 .track-title { color: #c084fc; }
    .track-3 .track-title { color: #fb923c; }
    .track-4 .track-title { color: #f87171; }
    .metric { display: inline-block; background: #1a2332; border-radius: 8px; padding: 1rem 1.5rem; margin: 0.5rem; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #34d399; }
    .metric-label { font-size: 0.75rem; color: #94a3b8; margin-top: 0.3rem; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin: 2px; }
    .tag-pathogen { background: #7f1d1d; color: #fca5a5; }
    .tag-amr { background: #713f12; color: #fde68a; }
    .tag-aiv { background: #4c1d95; color: #c4b5fd; }
    .tag-host { background: #064e3b; color: #6ee7b7; }
    .alert { background: #7f1d1d; border: 1px solid #991b1b; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
    .alert-title { color: #fca5a5; font-weight: 700; }
    .bar { height: 8px; background: #1a3a2f; border-radius: 4px; overflow: hidden; display: inline-block; width: 150px; vertical-align: middle; }
    .bar-fill { height: 100%; background: linear-gradient(90deg, #34d399, #6ee7b7); border-radius: 4px; }
</style>
</head>
<body>
<div class="container">
    <h1>🌊 Wetland Surveillance Report</h1>
    <p class="subtitle">Multi-omics pathogen, AMR, and host characterization — East Atlantic Flyway</p>
"""]

    # Track overview
    html.append("""
    <h2>Analysis Tracks</h2>
    <div class="tracks">
        <div class="track track-1">
            <div class="track-title">Track 1: Metagenomics</div>
            <div style="font-size:0.8rem; color:#94a3b8">Shotgun DNA → taxonomy, pathogens, AMR</div>
        </div>
        <div class="track track-2">
            <div class="track-title">Track 2: RNA Virome</div>
            <div style="font-size:0.8rem; color:#94a3b8">RNA → viral community profiling</div>
        </div>
        <div class="track track-3">
            <div class="track-title">Track 3: eDNA Barcoding</div>
            <div style="font-size:0.8rem; color:#94a3b8">12S/cytb → vertebrate host ID</div>
        </div>
        <div class="track track-4">
            <div class="track-title">Track 4: AIV WGS</div>
            <div style="font-size:0.8rem; color:#94a3b8">Targeted influenza genome assembly</div>
        </div>
    </div>
    """)

    # AIV detection summary
    aiv_positives = {s: st for s, st in aiv_results.items() if st != "not_detected"}
    if aiv_positives:
        html.append('<div class="alert"><div class="alert-title">⚠️ Avian Influenza Detected</div>')
        for sample, subtype in aiv_positives.items():
            site = samples.get(sample, {}).get("site", "unknown")
            html.append(f'<div style="margin-top:0.5rem">{sample} ({site}): <span class="tag tag-aiv">{subtype}</span></div>')
        html.append('</div>')

    # Per-site summary
    html.append("<h2>Site-Level Summary</h2>")
    site_samples = {}
    for s, info in samples.items():
        site = info.get("site", "unknown")
        site_samples.setdefault(site, []).append(s)

    html.append("<table><tr><th>Site</th><th>Samples</th><th>Top Pathogens</th><th>AMR Genes</th><th>AIV</th></tr>")
    for site, site_info in sites.items():
        s_list = site_samples.get(site, [])
        n_amr = sum(len(amr.get(s, [])) for s in s_list)
        aiv_status = ", ".join(aiv_results.get(s, "—") for s in s_list)
        html.append(f"""<tr>
            <td>{site_info.get('label', site)}<br><span style="color:#64748b;font-size:0.75rem">{site_info.get('country', '')}</span></td>
            <td>{len(s_list)}</td>
            <td><span class="tag tag-pathogen">{n_amr} genes</span></td>
            <td>{n_amr}</td>
            <td>{aiv_status}</td>
        </tr>""")
    html.append("</table>")

    # Footer
    html.append("""
    <hr style="border-color:#1a3a2f; margin-top:3rem;">
    <p style="color:#64748b; font-size:0.75rem; margin-top:1rem;">
        Generated by wetland-surveillance-pipeline · Perlas A*, Reska T* et al. (2025)
    </p>
</div></body></html>""")

    return "\n".join(html)


def main():
    samples = snakemake.params.samples
    sites = snakemake.params.sites

    taxonomy = {}
    for f in snakemake.input.taxonomy:
        sample = Path(f).stem.replace("_bracken_species", "")
        taxonomy[sample] = parse_bracken(f)

    amr_data = {}
    for f in snakemake.input.amr:
        sample = Path(f).stem.replace("_amr_hits", "")
        amr_data[sample] = parse_amr(f)

    aiv_results = {}
    for f in snakemake.input.aiv:
        sample = Path(f).stem.replace("_aiv_subtype", "")
        aiv_results[sample] = parse_aiv(f)

    associations = []
    with open(snakemake.input.associations) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            associations.append(row)

    html = generate_html(samples, sites, taxonomy, amr_data, aiv_results, associations)

    with open(snakemake.output.html, "w") as fh:
        fh.write(html)


if __name__ == "__main__":
    main()
