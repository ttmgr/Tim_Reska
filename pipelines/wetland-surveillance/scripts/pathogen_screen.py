#!/usr/bin/env python3
"""
Pathogen screening script.

Cross-references Bracken species-level taxonomic assignments against
a curated database of known pathogens relevant to One Health surveillance.

The pathogen database includes WHO priority pathogens, zoonotic agents,
waterborne pathogens, and AMR-associated organisms commonly tracked
in environmental surveillance programs.
"""

import csv
import sys
from pathlib import Path


# Default pathogen categories for One Health surveillance
PATHOGEN_CATEGORIES = {
    "zoonotic": "Zoonotic pathogen — transmissible between animals and humans",
    "waterborne": "Waterborne pathogen — transmitted through contaminated water",
    "amr_associated": "Associated with antimicrobial resistance",
    "who_priority": "WHO priority pathogen for AMR surveillance",
    "avian": "Avian pathogen — relevant for poultry and wildlife health",
    "emerging": "Emerging or re-emerging infectious agent"
}


def load_pathogen_database(db_path: str) -> dict:
    """Load curated pathogen database.

    Expected format (TSV):
        species_name    taxon_id    category    risk_level    notes
    """
    pathogens = {}
    with open(db_path) as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            taxon_id = row.get("taxon_id", "").strip()
            species = row.get("species_name", "").strip()
            pathogens[species.lower()] = {
                "taxon_id": taxon_id,
                "species": species,
                "category": row.get("category", "unknown"),
                "risk_level": row.get("risk_level", "unknown"),
                "notes": row.get("notes", "")
            }
    return pathogens


def parse_bracken_results(bracken_path: str) -> list[dict]:
    """Parse Bracken species-level results."""
    species = []
    with open(bracken_path) as fh:
        header = fh.readline()
        for line in fh:
            fields = line.strip().split("\t")
            if len(fields) >= 7:
                species.append({
                    "name": fields[0],
                    "taxon_id": fields[1],
                    "reads": int(fields[5]),
                    "fraction": float(fields[6])
                })
    return species


def screen_pathogens(species_list, pathogen_db):
    """Screen detected species against pathogen database."""
    hits = []
    for sp in species_list:
        sp_lower = sp["name"].lower()
        if sp_lower in pathogen_db:
            hit = pathogen_db[sp_lower].copy()
            hit["detected_reads"] = sp["reads"]
            hit["relative_abundance"] = sp["fraction"]
            hits.append(hit)
        else:
            # Check genus-level match
            genus = sp_lower.split()[0] if " " in sp_lower else sp_lower
            for db_name, db_entry in pathogen_db.items():
                if db_name.startswith(genus + " "):
                    hit = db_entry.copy()
                    hit["detected_reads"] = sp["reads"]
                    hit["relative_abundance"] = sp["fraction"]
                    hit["match_level"] = "genus"
                    hits.append(hit)
                    break

    return sorted(hits, key=lambda x: x["detected_reads"], reverse=True)


def main():
    bracken_path = snakemake.input.taxonomy
    pathogen_db_path = snakemake.input.pathogen_db
    output_path = snakemake.output.screen

    pathogen_db = load_pathogen_database(pathogen_db_path)
    species = parse_bracken_results(bracken_path)
    hits = screen_pathogens(species, pathogen_db)

    with open(output_path, "w") as fh:
        fh.write("species\tcategory\trisk_level\treads\trelative_abundance\tnotes\n")
        for hit in hits:
            fh.write(
                f"{hit['species']}\t{hit['category']}\t{hit['risk_level']}\t"
                f"{hit['detected_reads']}\t{hit['relative_abundance']:.6f}\t"
                f"{hit.get('notes', '')}\n"
            )

    if hits:
        print(f"Pathogen screen: {len(hits)} pathogen(s) detected",
              file=sys.stderr)
    else:
        print("Pathogen screen: no known pathogens detected",
              file=sys.stderr)


if __name__ == "__main__":
    main()
