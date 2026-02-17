#!/usr/bin/env python3
"""
Select optimal AIV reference per influenza segment from samtools idxstats.

For each of the 8 influenza segments (PB2, PB1, PA, HA, NP, NA, M, NS),
selects the reference sequence with the highest number of mapped reads.

Used in: Perlas A*, Reska T*, et al. (2025)
"""

import sys
from collections import defaultdict
from pathlib import Path


# Standard influenza A segment identifiers
SEGMENTS = ["PB2", "PB1", "PA", "HA", "NP", "NA", "M", "NS"]


def parse_idxstats(filepath: str) -> list[dict]:
    """Parse samtools idxstats output."""
    entries = []
    with open(filepath) as fh:
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 4:
                entries.append({
                    "ref_name": fields[0],
                    "length": int(fields[1]),
                    "mapped": int(fields[2]),
                    "unmapped": int(fields[3])
                })
    return entries


def identify_segment(ref_name: str) -> str:
    """Identify which influenza segment a reference belongs to."""
    ref_upper = ref_name.upper()
    for seg in SEGMENTS:
        if seg in ref_upper:
            return seg
    return "unknown"


def select_best_per_segment(entries: list[dict]) -> dict:
    """Select reference with most mapped reads per segment."""
    segment_refs = defaultdict(list)

    for entry in entries:
        if entry["mapped"] > 0:
            segment = identify_segment(entry["ref_name"])
            if segment != "unknown":
                segment_refs[segment].append(entry)

    best = {}
    for segment, refs in segment_refs.items():
        best_ref = max(refs, key=lambda x: x["mapped"])
        best[segment] = best_ref

    return best


def main():
    idxstats_path = snakemake.input.idxstats
    output_path = snakemake.output.best_refs

    entries = parse_idxstats(idxstats_path)
    best = select_best_per_segment(entries)

    # Write best reference names (one per line) for re-mapping
    with open(output_path, "w") as fh:
        for segment in SEGMENTS:
            if segment in best:
                ref = best[segment]
                fh.write(f"{ref['ref_name']}\t{segment}\t{ref['mapped']}\n")

    total_mapped = sum(r["mapped"] for r in best.values())
    print(f"AIV reference selection: {len(best)} segments with "
          f"{total_mapped} total mapped reads", file=sys.stderr)


if __name__ == "__main__":
    main()
