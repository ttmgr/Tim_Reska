#!/usr/bin/env python3
"""
Contamination filter for ultra-low biomass (ULB) metagenomics.

Compares taxonomic profiles between real samples and negative controls
to identify and remove likely contaminant reads. This is the most critical
quality control step for ULB air samples, where reagent- and environment-
derived contaminants can dominate the signal.

Algorithm:
    1. Parse Kraken2 reports for all negative controls
    2. Build a contaminant profile: mean read count per taxon across controls
    3. For each taxon in the sample, compute fold-change over mean control
    4. Flag taxa below the fold-change threshold as contaminants
    5. Extract non-contaminant read IDs from Kraken2 output
    6. Filter the FASTQ to retain only non-contaminant reads
"""

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path


def parse_kraken_report(report_path: str) -> dict[int, int]:
    """Parse a Kraken2 report and return {taxon_id: read_count}."""
    taxa = {}
    with open(report_path) as fh:
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 5:
                read_count = int(fields[1])
                taxon_id = int(fields[4])
                if read_count > 0:
                    taxa[taxon_id] = read_count
    return taxa


def parse_kraken_output(output_path: str) -> dict[str, int]:
    """Parse Kraken2 output and return {read_id: taxon_id}."""
    read_taxa = {}
    with open(output_path) as fh:
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 3 and fields[0] == "C":
                read_id = fields[1]
                taxon_id = int(fields[2])
                read_taxa[read_id] = taxon_id
    return read_taxa


def build_contaminant_profile(
    neg_reports: list[str],
    min_reads: int = 2
) -> dict[int, float]:
    """Build mean abundance profile across negative controls.

    Args:
        neg_reports: Paths to Kraken2 reports from negative controls.
        min_reads: Minimum total reads across controls to consider a taxon.

    Returns:
        {taxon_id: mean_read_count} for taxa above threshold.
    """
    taxon_counts = defaultdict(list)

    for report in neg_reports:
        taxa = parse_kraken_report(report)
        all_taxa = set()
        for tid, count in taxa.items():
            taxon_counts[tid].append(count)
            all_taxa.add(tid)

    # For taxa not seen in a control, add 0
    for tid in list(taxon_counts.keys()):
        while len(taxon_counts[tid]) < len(neg_reports):
            taxon_counts[tid].append(0)

    # Compute means and filter
    contaminant_profile = {}
    for tid, counts in taxon_counts.items():
        total = sum(counts)
        if total >= min_reads:
            contaminant_profile[tid] = sum(counts) / len(counts)

    return contaminant_profile


def identify_contaminants(
    sample_taxa: dict[int, int],
    contaminant_profile: dict[int, float],
    fold_threshold: float = 5.0
) -> set[int]:
    """Identify contaminant taxa by fold-change comparison.

    A taxon is flagged as a contaminant if:
        sample_abundance / mean_control_abundance < fold_threshold

    Args:
        sample_taxa: {taxon_id: read_count} from the sample.
        contaminant_profile: {taxon_id: mean_read_count} from controls.
        fold_threshold: Minimum fold-change to retain a taxon.

    Returns:
        Set of contaminant taxon IDs.
    """
    contaminants = set()
    for tid, mean_control in contaminant_profile.items():
        sample_count = sample_taxa.get(tid, 0)
        if mean_control > 0:
            fold_change = sample_count / mean_control
            if fold_change < fold_threshold:
                contaminants.add(tid)
    return contaminants


def filter_fastq(
    input_fastq: str,
    output_fastq: str,
    read_taxa: dict[str, int],
    contaminant_taxa: set[int]
) -> tuple[int, int]:
    """Filter FASTQ file, removing reads classified as contaminants.

    Returns:
        (reads_kept, reads_removed)
    """
    kept = 0
    removed = 0

    opener_in = gzip.open if input_fastq.endswith(".gz") else open
    opener_out = gzip.open if output_fastq.endswith(".gz") else open

    with opener_in(input_fastq, "rt") as fin, \
         opener_out(output_fastq, "wt") as fout:
        while True:
            header = fin.readline()
            if not header:
                break
            seq = fin.readline()
            plus = fin.readline()
            qual = fin.readline()

            read_id = header.strip().split()[0].lstrip("@")
            taxon = read_taxa.get(read_id)

            if taxon is not None and taxon in contaminant_taxa:
                removed += 1
            else:
                fout.write(header)
                fout.write(seq)
                fout.write(plus)
                fout.write(qual)
                kept += 1

    return kept, removed


def main():
    # Snakemake provides these variables
    sample_report = snakemake.input.sample_report
    sample_output = snakemake.input.sample_output
    sample_fastq = snakemake.input.sample_fastq
    neg_reports = snakemake.input.neg_reports
    out_fastq = snakemake.output.fastq
    out_contaminants = snakemake.output.contaminant_list
    out_stats = snakemake.output.stats

    fold_threshold = snakemake.params.fold_threshold
    min_reads = snakemake.params.min_reads_in_control

    # 1. Build contaminant profile from negative controls
    contaminant_profile = build_contaminant_profile(
        neg_reports if isinstance(neg_reports, list) else [neg_reports],
        min_reads=min_reads
    )

    # 2. Parse sample taxonomy
    sample_taxa = parse_kraken_report(sample_report)

    # 3. Identify contaminants
    contaminant_taxa = identify_contaminants(
        sample_taxa, contaminant_profile, fold_threshold
    )

    # 4. Get read-level classifications
    read_taxa = parse_kraken_output(sample_output)

    # 5. Filter FASTQ
    kept, removed = filter_fastq(
        sample_fastq, out_fastq, read_taxa, contaminant_taxa
    )

    # 6. Write contaminant list
    with open(out_contaminants, "w") as fh:
        fh.write("taxon_id\tmean_control_abundance\tsample_abundance\tfold_change\n")
        for tid in sorted(contaminant_taxa):
            ctrl = contaminant_profile.get(tid, 0)
            samp = sample_taxa.get(tid, 0)
            fc = samp / ctrl if ctrl > 0 else float("inf")
            fh.write(f"{tid}\t{ctrl:.1f}\t{samp}\t{fc:.2f}\n")

    # 7. Write stats
    stats = {
        "reads_input": kept + removed,
        "reads_kept": kept,
        "reads_removed": removed,
        "pct_removed": round(100 * removed / (kept + removed), 2) if (kept + removed) > 0 else 0,
        "contaminant_taxa_count": len(contaminant_taxa),
        "total_taxa_in_controls": len(contaminant_profile),
        "fold_threshold": fold_threshold
    }
    with open(out_stats, "w") as fh:
        json.dump(stats, fh, indent=2)

    print(f"Contamination filter: kept {kept}, removed {removed} "
          f"({stats['pct_removed']}%), {len(contaminant_taxa)} contaminant taxa",
          file=sys.stderr)


if __name__ == "__main__":
    main()
