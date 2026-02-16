#!/usr/bin/env python3
"""
Host-pathogen association analysis.

Cross-references detected pathogens (from metagenomics and virome tracks)
with vertebrate species identified through eDNA metabarcoding to infer
potential host-pathogen-environment relationships at each sampling site.

This is the integrative step that ties together all four analysis tracks
into a One Health perspective.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def parse_pathogen_screen(filepath: str) -> list[dict]:
    """Parse pathogen screening results."""
    pathogens = []
    with open(filepath) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            pathogens.append(row)
    return pathogens


def parse_vertebrate_species(filepath: str) -> list[str]:
    """Extract unique vertebrate species from eDNA BLAST results."""
    species = set()
    with open(filepath) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) >= 13:
                # Extract species from BLAST stitle (last field)
                title = fields[12]
                # Try to extract binomial name
                parts = title.split()
                if len(parts) >= 2:
                    species.add(f"{parts[0]} {parts[1]}")
    return sorted(species)


def parse_aiv_subtype(filepath: str) -> dict:
    """Parse AIV subtyping results."""
    with open(filepath) as fh:
        line = fh.readline().strip()
        if line:
            fields = line.split("\t")
            return {
                "sample": fields[0],
                "subtype": fields[1] if len(fields) > 1 else "unknown",
                "reads": int(fields[2]) if len(fields) > 2 else 0
            }
    return {"sample": "", "subtype": "not_detected", "reads": 0}


# Known host-pathogen associations for One Health context
KNOWN_ASSOCIATIONS = {
    "influenza a virus": ["Anas platyrhynchos", "Anser anser", "Cygnus olor",
                          "Fulica atra", "Aythya ferina"],
    "salmonella": ["Anas platyrhynchos", "Rattus norvegicus", "Sus scrofa"],
    "campylobacter": ["Anas platyrhynchos", "Anser anser", "Columba livia"],
    "leptospira": ["Rattus norvegicus", "Sus scrofa", "Myocastor coypus"],
    "cryptosporidium": ["Bos taurus", "Ovis aries", "Cervus elaphus"],
    "giardia": ["Castor fiber", "Myocastor coypus", "Ondatra zibethicus"],
}


def infer_associations(
    pathogens: list[dict],
    hosts: list[str],
    aiv_result: dict
) -> list[dict]:
    """Infer host-pathogen associations based on co-occurrence and known links."""
    associations = []

    for pathogen in pathogens:
        pathogen_name = pathogen.get("species", "").lower()
        associated_hosts = []

        # Check against known host-pathogen associations
        for known_pathogen, known_hosts in KNOWN_ASSOCIATIONS.items():
            if known_pathogen in pathogen_name:
                for host in known_hosts:
                    if host in hosts:
                        associated_hosts.append({
                            "host": host,
                            "evidence": "known_association + co-occurrence"
                        })

        # If no known associations, flag all co-occurring hosts
        if not associated_hosts:
            for host in hosts[:5]:  # Limit to top 5 hosts
                associated_hosts.append({
                    "host": host,
                    "evidence": "co-occurrence_only"
                })

        associations.append({
            "pathogen": pathogen.get("species", "unknown"),
            "category": pathogen.get("category", "unknown"),
            "reads": pathogen.get("reads", 0),
            "hosts": associated_hosts
        })

    # Add AIV-specific associations
    if aiv_result.get("subtype", "not_detected") != "not_detected":
        aiv_hosts = [h for h in hosts
                     if any(genus in h for genus in
                            ["Anas", "Anser", "Cygnus", "Fulica", "Aythya"])]
        associations.append({
            "pathogen": f"Avian Influenza ({aiv_result['subtype']})",
            "category": "avian / zoonotic",
            "reads": aiv_result["reads"],
            "hosts": [{"host": h, "evidence": "known_reservoir + co-occurrence"}
                      for h in aiv_hosts]
        })

    return associations


def main():
    samples_config = snakemake.params.samples
    all_associations = []

    for pathogen_file, virome_file, host_file, aiv_file in zip(
        snakemake.input.pathogens,
        snakemake.input.virome,
        snakemake.input.hosts,
        snakemake.input.aiv
    ):
        sample = Path(pathogen_file).stem.replace("_pathogen_screen", "")
        site = samples_config.get(sample, {}).get("site", "unknown")

        pathogens = parse_pathogen_screen(pathogen_file)
        hosts = parse_vertebrate_species(host_file)
        aiv = parse_aiv_subtype(aiv_file)

        associations = infer_associations(pathogens, hosts, aiv)

        for assoc in associations:
            for host_info in assoc.get("hosts", [{"host": "none", "evidence": "none"}]):
                all_associations.append({
                    "sample": sample,
                    "site": site,
                    "pathogen": assoc["pathogen"],
                    "category": assoc["category"],
                    "pathogen_reads": assoc["reads"],
                    "host": host_info["host"],
                    "evidence": host_info["evidence"]
                })

    # Write output
    with open(snakemake.output.associations, "w") as fh:
        if all_associations:
            writer = csv.DictWriter(fh, fieldnames=all_associations[0].keys(),
                                    delimiter="\t")
            writer.writeheader()
            writer.writerows(all_associations)
        else:
            fh.write("# No host-pathogen associations found\n")

    print(f"Host-pathogen analysis: {len(all_associations)} associations",
          file=sys.stderr)


if __name__ == "__main__":
    main()
