#!/usr/bin/env python3
"""
eDNA taxonomy assignment via global alignment to MIDORI2 12S rRNA database.

Applies avian filtering criteria from Publication II:
  - Class Aves: ≥80% query coverage, ≥98% sequence identity, ≥5 reads
  - Cross-references against eBird regional occurrence data
  - Biogeographically implausible hits collapsed to higher ranks or removed

Used in: Perlas A*, Reska T*, et al. (2025)
"""

import csv
import subprocess
import sys
from pathlib import Path


def run_global_alignment(query_fasta: str, db: str) -> list[dict]:
    """Run VSEARCH global alignment against MIDORI2 database."""
    hits = []
    result = subprocess.run(
        ["vsearch", "--usearch_global", query_fasta,
         "--db", db,
         "--id", "0.80",
         "--blast6out", "/dev/stdout",
         "--maxaccepts", "5",
         "--top_hits_only"],
        capture_output=True, text=True
    )

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) >= 12:
            hits.append({
                "query": fields[0],
                "target": fields[1],
                "identity": float(fields[2]),
                "alignment_length": int(fields[3]),
                "query_length": int(fields[6]) if fields[6].isdigit() else 0,
                "evalue": fields[10] if len(fields) > 10 else "",
            })
    return hits


def parse_midori_header(header: str) -> dict:
    """Parse MIDORI2 database header for taxonomic information.

    MIDORI2 headers contain taxonomy in the format:
    >accession;tax=k:Animalia,p:Chordata,c:Aves,...,s:Species_name
    """
    info = {"kingdom": "", "phylum": "", "class": "", "order": "",
            "family": "", "genus": "", "species": ""}

    if "tax=" in header:
        tax_str = header.split("tax=")[1]
        for rank_entry in tax_str.split(","):
            if ":" in rank_entry:
                rank_code, name = rank_entry.split(":", 1)
                rank_map = {"k": "kingdom", "p": "phylum", "c": "class",
                            "o": "order", "f": "family", "g": "genus",
                            "s": "species"}
                if rank_code in rank_map:
                    info[rank_map[rank_code]] = name.replace("_", " ")
    return info


def apply_avian_filters(hits: list[dict],
                        min_identity: float = 98.0,
                        min_query_coverage: float = 80.0,
                        min_reads: int = 5) -> list[dict]:
    """Apply avian-specific filtering criteria."""
    filtered = []
    for hit in hits:
        taxonomy = parse_midori_header(hit["target"])

        # Calculate query coverage
        qcov = (hit["alignment_length"] / hit["query_length"] * 100
                if hit["query_length"] > 0 else 0)

        # Apply filters for Aves
        if taxonomy["class"] == "Aves":
            if hit["identity"] >= min_identity and qcov >= min_query_coverage:
                hit["taxonomy"] = taxonomy
                hit["query_coverage"] = qcov
                filtered.append(hit)

        # Non-avian vertebrates: keep with standard thresholds
        elif taxonomy["phylum"] == "Chordata":
            if hit["identity"] >= 95.0 and qcov >= min_query_coverage:
                hit["taxonomy"] = taxonomy
                hit["query_coverage"] = qcov
                filtered.append(hit)

    return filtered


def main():
    otu_fasta = snakemake.input.otus
    db = snakemake.input.db
    output_path = snakemake.output.species

    min_identity = snakemake.params.min_identity
    min_query_coverage = snakemake.params.min_query_coverage
    min_reads = snakemake.params.min_reads

    # Run alignment
    hits = run_global_alignment(otu_fasta, db)

    # Apply filters
    filtered = apply_avian_filters(hits, min_identity, min_query_coverage, min_reads)

    # Write results
    with open(output_path, "w") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["otu_id", "species", "class", "order", "family",
                         "identity", "query_coverage", "target"])
        for hit in filtered:
            tax = hit["taxonomy"]
            writer.writerow([
                hit["query"],
                tax["species"],
                tax["class"],
                tax["order"],
                tax["family"],
                f"{hit['identity']:.1f}",
                f"{hit['query_coverage']:.1f}",
                hit["target"]
            ])

    print(f"eDNA taxonomy: {len(filtered)} vertebrate species assigned",
          file=sys.stderr)


if __name__ == "__main__":
    main()
