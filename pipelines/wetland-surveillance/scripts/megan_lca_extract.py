#!/usr/bin/env python3
"""
Extract LCA (Lowest Common Ancestor) pathogen assignments from MEGAN CE.

Processes SAM alignment files through MEGAN Community Edition v6.21.1
LCA criteria and cross-references results against the CZID pathogen list.

LCA parameters (as per Publication II):
  - >50% near-best alignments
  - <10% edit distance

Pathogen detection threshold: ≥5 reads or ≥1 contig per species.

Used in: Perlas A*, Reska T*, et al. (2025)
"""

import csv
import sys
from collections import Counter
from pathlib import Path


def parse_sam_for_lca(sam_path: str, max_edit_distance_pct: float = 0.10):
    """Parse SAM file and group alignments per query for LCA assignment.

    Filters:
      - Only primary and supplementary alignments (not unmapped)
      - Edit distance < 10% of alignment length
    """
    query_hits = {}

    with open(sam_path) as fh:
        for line in fh:
            if line.startswith("@"):
                continue
            fields = line.strip().split("\t")
            if len(fields) < 11:
                continue

            flag = int(fields[1])
            if flag & 4:  # unmapped
                continue

            query = fields[0]
            ref = fields[2]
            cigar = fields[5]

            # Extract edit distance from NM tag
            nm = 0
            for tag in fields[11:]:
                if tag.startswith("NM:i:"):
                    nm = int(tag.split(":")[2])
                    break

            # Calculate alignment length from CIGAR
            aln_len = sum(int(x) for x in
                          __import__("re").findall(r"(\d+)[MDI]", cigar))

            if aln_len > 0 and (nm / aln_len) < max_edit_distance_pct:
                if query not in query_hits:
                    query_hits[query] = []
                query_hits[query].append({
                    "reference": ref,
                    "edit_distance": nm,
                    "alignment_length": aln_len,
                    "score": aln_len - nm
                })

    return query_hits


def assign_lca(hits: list[dict], near_best_pct: float = 0.50) -> str:
    """Assign taxonomy using LCA with >50% near-best alignment criterion."""
    if not hits:
        return "unassigned"

    best_score = max(h["score"] for h in hits)
    threshold = best_score * near_best_pct

    near_best = [h for h in hits if h["score"] >= threshold]

    refs = set(h["reference"] for h in near_best)
    if len(refs) == 1:
        return refs.pop()
    else:
        # Return the most common reference among near-best hits
        ref_counts = Counter(h["reference"] for h in near_best)
        return ref_counts.most_common(1)[0][0]


def main():
    reads_sam = snakemake.input.reads_sam
    contigs_sam = snakemake.input.contigs_sam
    output_path = snakemake.output.lca

    min_reads = snakemake.params.min_reads
    min_contigs = snakemake.params.min_contigs

    # Process reads
    read_hits = parse_sam_for_lca(reads_sam)
    read_assignments = Counter()
    for query, hits in read_hits.items():
        taxon = assign_lca(hits)
        read_assignments[taxon] += 1

    # Process contigs
    contig_hits = parse_sam_for_lca(contigs_sam)
    contig_assignments = Counter()
    for query, hits in contig_hits.items():
        taxon = assign_lca(hits)
        contig_assignments[taxon] += 1

    # Filter: ≥5 reads OR ≥1 contig
    pathogens = set()
    for taxon, count in read_assignments.items():
        if count >= min_reads:
            pathogens.add(taxon)
    for taxon, count in contig_assignments.items():
        if count >= min_contigs:
            pathogens.add(taxon)

    # Write results
    with open(output_path, "w") as fh:
        fh.write("taxon\tread_count\tcontig_count\tdetection_level\n")
        for taxon in sorted(pathogens):
            rc = read_assignments.get(taxon, 0)
            cc = contig_assignments.get(taxon, 0)
            level = "high" if rc >= min_reads and cc >= min_contigs else "moderate"
            fh.write(f"{taxon}\t{rc}\t{cc}\t{level}\n")

    print(f"MEGAN LCA: {len(pathogens)} taxa passed thresholds "
          f"(≥{min_reads} reads or ≥{min_contigs} contig)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
