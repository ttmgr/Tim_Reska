#!/usr/bin/env python3
"""
Community analysis script for aerobiome pipeline.

Computes beta-diversity (Bray-Curtis dissimilarity), performs PCoA
ordination, and generates rarefaction curves from Kraken2 genus-level
profiles.

Libraries: Pandas, NumPy, scikit-learn, scikit-bio, SciPy, Matplotlib
(as used in Reska et al. 2024)
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import braycurtis
from skbio import DistanceMatrix
from skbio.stats.ordination import pcoa


def parse_kraken2_report(filepath: str) -> dict:
    """Parse Kraken2 report and extract genus-level read counts.

    Kraken2 report format (tab-delimited):
      col 0: % of reads at or below this node
      col 1: reads at or below this node
      col 2: reads directly assigned to this node
      col 3: rank code (G = genus)
      col 4: NCBI taxon ID
      col 5: scientific name
    """
    genera = {}
    with open(filepath) as fh:
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 6:
                rank = fields[3].strip()
                if rank == "G":
                    name = fields[5].strip()
                    reads = int(fields[2].strip())
                    if reads > 0:
                        genera[name] = reads
    return genera


def build_abundance_matrix(reports: list, sample_names: list) -> pd.DataFrame:
    """Build genus × sample abundance matrix from Kraken2 reports."""
    all_genera = set()
    profiles = {}

    for filepath, sample in zip(reports, sample_names):
        genera = parse_kraken2_report(filepath)
        profiles[sample] = genera
        all_genera.update(genera.keys())

    # Assemble matrix
    matrix = pd.DataFrame(0, index=sorted(all_genera), columns=sample_names)
    for sample, genera in profiles.items():
        for genus, count in genera.items():
            matrix.loc[genus, sample] = count

    return matrix


def compute_bray_curtis(matrix: pd.DataFrame) -> pd.DataFrame:
    """Compute pairwise Bray-Curtis dissimilarity."""
    samples = matrix.columns.tolist()
    n = len(samples)
    dm = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            dist = braycurtis(matrix.iloc[:, i].values,
                              matrix.iloc[:, j].values)
            dm[i, j] = dist
            dm[j, i] = dist

    return pd.DataFrame(dm, index=samples, columns=samples)


def run_pcoa(dm_df: pd.DataFrame) -> pd.DataFrame:
    """Run Principal Coordinate Analysis on Bray-Curtis matrix."""
    dm = DistanceMatrix(dm_df.values, ids=dm_df.index.tolist())
    results = pcoa(dm)
    coords = results.samples[["PC1", "PC2", "PC3"]].copy()
    coords.index = dm_df.index
    return coords


def plot_rarefaction(matrix: pd.DataFrame, output_path: str,
                     depths: list = None):
    """Generate rarefaction curves at specified depths."""
    if depths is None:
        depths = [5000, 10000, 15000, 30000, 50000, 70000]

    fig, ax = plt.subplots(figsize=(8, 5))

    for sample in matrix.columns:
        counts = matrix[sample].values
        total = counts.sum()
        richness_at_depth = []

        for depth in depths:
            if depth > total:
                richness_at_depth.append(np.nan)
                continue
            # Subsample and count observed genera
            p = counts / total
            n_observed = []
            for _ in range(10):
                subsample = np.random.multinomial(depth, p)
                n_observed.append((subsample > 0).sum())
            richness_at_depth.append(np.mean(n_observed))

        ax.plot(depths, richness_at_depth, marker="o", markersize=3,
                label=sample, alpha=0.7)

    ax.set_xlabel("Sequencing depth (reads)")
    ax.set_ylabel("Observed genera")
    ax.set_title("Rarefaction curves")
    ax.legend(fontsize=6, ncol=2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def main():
    reports = snakemake.input.reports
    samples = snakemake.params.samples

    # Build abundance matrix
    matrix = build_abundance_matrix(reports, samples)

    # Bray-Curtis dissimilarity
    bc = compute_bray_curtis(matrix)
    bc.to_csv(snakemake.output.bray_curtis, sep="\t")

    # PCoA
    coords = run_pcoa(bc)
    coords.to_csv(snakemake.output.pcoa, sep="\t")

    # Rarefaction
    plot_rarefaction(matrix, snakemake.output.rarefaction)

    print(f"Community analysis complete: {len(samples)} samples, "
          f"{len(matrix.index)} genera", file=sys.stderr)


if __name__ == "__main__":
    main()
