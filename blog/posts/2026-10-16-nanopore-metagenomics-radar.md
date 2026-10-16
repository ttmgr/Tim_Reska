---
title: Nanopore and Metagenomics Radar, 16 October 2026
date: 2026-10-16
series: Nanopore and Metagenomics Radar
summary: Rapid metagenomics changed treatment for 26% of samples in a paediatric intensive care unit, wastewater resistance signals turn out to depend on the host species, and a quiet three weeks for nanopore software. Covers 25 September to 16 October 2026.
---
What changed in nanopore sequencing and metagenomics between 25 September and 16 October 2026. Every item links to the page it comes from, and numbers are copied from the abstracts. Peer-reviewed articles and preprints are marked as such.

## The three things worth knowing

- **Rapid metagenomics moved beyond the hospital that built it, and changed treatment.** In a paediatric intensive care unit, results changed antimicrobial treatment for 26% of samples, and found organisms that routine tests missed in 24%.
- **Wastewater resistance signals depend on which bacterium carries the gene.** In one study, resistance genes in Enterobacteriaceae tracked antibiotic prescribing closely, while those in Pseudomonadaceae lagged by 1 to 3 months. A second study found wastewater a poor stand-in for clinical carbapenem resistance in *E. coli*.
- **A quiet three weeks for nanopore software.** There were no new kits, chemistry, Dorado, Medaka, MinKNOW or EPI2ME workflow releases in the window. Oxford Nanopore says it will show new adaptive sampling tools at ASHG, 20 to 24 October.

## Clinical metagenomics

- **Rapid pan-microbial metagenomics in paediatric intensive care.** Forrest-Hammond et al., *Lancet Microbe*, peer-reviewed, online 15 October. 177 samples from 122 children, and 98% passed quality control. At 16 hours of sequencing, sensitivity was 89% for bacteria, 100% for fungi and 87% for viruses, with specificity of 99% or more. Results changed care for 29% of samples. The authors say higher sensitivity and resistance prediction are needed before wider use. One author declares part-time employment at Oxford Nanopore Technologies. [PubMed 42880330](https://pubmed.ncbi.nlm.nih.gov/42880330/)

## Wastewater and environmental surveillance

- **Sewage resistance signals follow prescribing, with a lag that depends on the host.** Brown et al., *Nature Communications*, peer-reviewed, 9 October. Five years of outpatient prescriptions compared with a year of twice-weekly metagenomic sampling at one treatment plant. Resistance genes linked to Enterobacteriaceae tracked use closely, and those linked to Pseudomonadaceae followed with a 1 to 3 month lag. Surveillance readouts should be read per host, not as total gene counts. [Nature Communications](https://www.nature.com/articles/s41467-026-78142-3)
- **Wastewater is not a reliable proxy for clinical carbapenem resistance in *E. coli*.** Berglund et al., medRxiv preprint, 6 October. Isolates from Uppsala wastewater only partly overlapped with clinical isolates from the same region and period. Metagenomics rarely detected the resistance genes, which the authors put down to low abundance. [medRxiv](https://www.medrxiv.org/content/10.64898/2026.10.02.26364587v1)
- **Four years of weekly wastewater sequencing against qPCR.** Prakash et al., medRxiv preprint, 15 October. Five respiratory viruses in wastewater from 16 Texas cities, May 2022 to July 2026. Both methods tracked emergency-department visits, and the authors find sequencing more promising than qPCR for early outbreak detection. [medRxiv](https://www.medrxiv.org/content/10.64898/2026.10.13.26364774v1)
- **Capture-enriched wastewater metagenomics across the United States.** Wolfe et al., *Applied and Environmental Microbiology*, peer-reviewed, 28 September. Nearly 450 weekly samples from 15 treatment plants, with a median viral read fraction over 19%, and abundance estimates that agreed with digital PCR. This is a short-read hybrid-capture method, not nanopore. [DOI 10.1128/aem.01020-26](https://doi.org/10.1128/aem.01020-26)
- **Measles detected in hospital air during an outbreak.** Barbian et al., medRxiv preprint, 27 September. Measles virus was found in emergency-department air over five weeks, and two of three air-derived sequences matched outbreak patients. [medRxiv](https://www.medrxiv.org/content/10.64898/2026.09.25.26363929v1)

## Methods and references

- **8,744 complete environmental plasmids from long reads.** Sørensen et al., bioRxiv preprint, 8 October. Built from 9,972 short-read and 154 nanopore-sequenced metagenomes from Denmark. Plasmid diversity rose by 99% against known environmental plasmids. The authors also release a tool that checks whether a plasmid assembly is complete. Useful for linking resistance genes to plasmids. [bioRxiv](https://www.biorxiv.org/content/10.64898/2026.10.06.756670v1)
- **EsViritu, a viral profiler built against false positives.** Tisza et al., bioRxiv preprint, 30 September. Compared with Kraken2, Centrifuger, Metabuli and sylph on the same viral database, it led or tied on abundance accuracy at every taxonomic rank, and reported essentially no false positives in pathogen-free samples. The preprint does not mention long reads, so nanopore users should test it on their own data. [bioRxiv](https://www.biorxiv.org/content/10.64898/2026.09.29.755457v1)
- **Absolute, strain-level abundance from long reads.** Din et al., bioRxiv preprint, 29 September. The method adds plasmid internal standards to get absolute abundances from long-read metagenomes. [bioRxiv](https://www.biorxiv.org/content/10.64898/2026.09.28.754546v1)

## Tools and databases

- **GTDB-Tk 2.8.0 changes species assignment** (13 October). `classify` and `classify_wf` now use the same species-assignment rule, so species calls can differ from 2.7.x, mainly in closely related genera. It uses the same R232 reference package, so no new download is needed, but older versions cannot resume from a 2.8.0 output folder. [GitHub release](https://github.com/Ecogenomics/GTDBTk/releases/tag/2.8.0)
- **A new MetaPhlAn database build appeared** (13 October). Files named `mpa_vJan26_CHOCOPhlAnSGB_202605_EGBv1` are on the bioBakery server, but there is no release note yet explaining what changed. Wait for documentation before switching. [bioBakery database folder](http://cmprod1.cibio.unitn.it/biobakery4/metaphlan_databases/)
- **NCBI's legacy Taxonomy Browser is being replaced in October.** Scripts that scrape or link the old `wwwtax.cgi` pages may break. The taxonomy itself and the taxdump files are not affected. [NCBI](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi)
- **POD5 0.3.49** (8 October). Faster migration of raw signal files. Version 0.3.48 (21 September) fixed older libraries failing to read newer files, which matters if you mix POD5 versions across instruments. [GitHub release](https://github.com/nanoporetech/pod5-file-format/releases/tag/0.3.49)

## Just before this window

These landed in September, before 25 September, and are worth knowing about if you missed them.

- **Kraken2 2.17.2** (23 September): multi-database classification now supports k-mer reporting, plus speed improvements. [GitHub releases](https://github.com/DerrickWood/kraken2/releases)
- **sylph 1.0.0** (14 September): the first 1.0 release. [GitHub releases](https://github.com/bluenote-1577/sylph/releases)
- **RefSeq Release 237** (4 September). [NCBI RefSeq](https://www.ncbi.nlm.nih.gov/refseq/)
- **Dorado 1.3.4** (3 September): a bug-fix release for a crash with HAC models. [GitHub releases](https://github.com/nanoporetech/dorado/releases)

## Coming up

- **New adaptive sampling tools at ASHG 2026**, 20 to 24 October. Oxford Nanopore says it will show tools to build custom "digital panels". Adaptive sampling is how many labs deplete host DNA or enrich for pathogens. [Oxford Nanopore](https://nanoporetech.com/about/events/conferences/ashg-2026)
