---
title: Rapid metagenomics changed antimicrobial treatment for 26% of pediatric intensive care samples
date: 2026-10-16
series: Nanopore and Metagenomics Radar
summary: Rapid clinical metagenomics altered antimicrobial treatment for 26% of samples in a pediatric intensive care unit, wastewater resistance signals were shown to depend on the bacterial host, and no new nanopore software was released. Covers 25 September to 16 October 2026.
---
This edition summarizes developments in nanopore sequencing and metagenomics published between 25 September and 16 October 2026. Each item links to its primary source, numerical values are reproduced from the respective abstracts or release notes, and preprints are identified as such, as they have not yet undergone peer review.

## Summary

Three developments characterize this period. First, rapid pan-microbial metagenomics was evaluated outside the center in which it was developed. In a pediatric intensive care unit (PICU), sequencing results altered antimicrobial treatment for 26% of samples and identified organisms missed by routine diagnostics in 24% (Forrest-Hammond et al. 2026). Second, two studies indicate that antimicrobial resistance (AMR) signals in wastewater depend on the bacterial host carrying the gene. While resistance genes associated with Enterobacteriaceae tracked antibiotic prescribing closely, those associated with Pseudomonadaceae lagged by 1 to 3 months (Brown et al. 2026), and a second study found wastewater to be a poor proxy for clinical carbapenem resistance in *Escherichia coli* (Berglund et al. 2026, preprint). Third, the period was quiet for nanopore software, with no new kits or chemistry and no releases of Dorado, Medaka, MinKNOW or EPI2ME workflows. Oxford Nanopore Technologies (ONT) has announced new adaptive sampling tools for the ASHG meeting, 20 to 24 October.

## Clinical metagenomics

Forrest-Hammond et al. (2026) evaluated rapid pan-microbial metagenomics on 177 samples from 122 children in a PICU, of which 98% passed quality control (*Lancet Microbe*, peer-reviewed, published online 15 October; [PubMed 42880330](https://pubmed.ncbi.nlm.nih.gov/42880330/)). After 16 hours of sequencing, sensitivity reached 89% for bacteria, 100% for fungi and 87% for viruses, with a specificity of 99% or higher. Results altered clinical management for 29% of samples. The authors nevertheless note that higher sensitivity and resistance prediction are required before broader implementation. One author declares part-time employment at ONT.

![**Figure 1:** *Performance and clinical impact of rapid pan-microbial metagenomics in a pediatric intensive care unit. (A) Sensitivity after 16 hours of sequencing by organism group; specificity was 99% or higher. (B) Share of samples for which results changed clinical management or antimicrobial treatment, or identified organisms missed by routine tests. Redrawn from the values reported by Forrest-Hammond et al. (2026).*](figures/2026-10-16-nanopore-fig1.svg)

## Wastewater and environmental surveillance

Brown et al. (2026) compared five years of outpatient prescription data with one year of twice-weekly metagenomic sampling at a single wastewater treatment plant (*Nature Communications*, peer-reviewed, 9 October; [article](https://www.nature.com/articles/s41467-026-78142-3)). Resistance genes linked to Enterobacteriaceae tracked antibiotic use closely, whereas those linked to Pseudomonadaceae followed with a lag of 1 to 3 months. These findings indicate that surveillance readouts should be interpreted per host taxon rather than as total gene counts. In a related preprint, Berglund et al. (2026) found that isolates from Uppsala wastewater overlapped only partially with clinical isolates from the same region and period (medRxiv, 6 October; [preprint](https://www.medrxiv.org/content/10.64898/2026.10.02.26364587v1)). Metagenomic sequencing rarely detected the corresponding resistance genes, which the authors attribute to their low abundance.

Two longitudinal studies compared sequencing with targeted assays. Prakash et al. (2026) monitored five respiratory viruses in wastewater from 16 Texas cities between May 2022 and July 2026, using weekly sequencing alongside quantitative PCR (qPCR) (medRxiv preprint, 15 October; [preprint](https://www.medrxiv.org/content/10.64898/2026.10.13.26364774v1)). Both methods tracked emergency department visits, although the authors consider sequencing more promising than qPCR for early outbreak detection. Wolfe et al. (2026) applied capture-enriched metagenomics to nearly 450 weekly samples from 15 treatment plants across the United States, obtaining a median viral read fraction above 19% and abundance estimates concordant with digital PCR (*Applied and Environmental Microbiology*, peer-reviewed, 28 September; [DOI 10.1128/aem.01020-26](https://doi.org/10.1128/aem.01020-26)). This approach relies on short-read hybrid capture rather than nanopore sequencing.

Beyond wastewater, Barbian et al. (2026) detected measles virus in emergency department air over five weeks during an outbreak, and two of three air-derived sequences matched those of outbreak patients (medRxiv preprint, 27 September; [preprint](https://www.medrxiv.org/content/10.64898/2026.09.25.26363929v1)).

## Methods and reference resources

Sørensen et al. (2026) assembled 8,744 complete environmental plasmids from 9,972 short-read and 154 nanopore-sequenced metagenomes from Denmark, increasing plasmid diversity by 99% relative to known environmental plasmids (bioRxiv preprint, 8 October; [preprint](https://www.biorxiv.org/content/10.64898/2026.10.06.756670v1)). The authors also release a tool that assesses whether a plasmid assembly is complete. The resource may support the linkage of resistance genes to plasmids.

Tisza et al. (2026) introduced EsViritu, a viral profiler designed to minimize false positives (bioRxiv preprint, 30 September; [preprint](https://www.biorxiv.org/content/10.64898/2026.09.29.755457v1)). Benchmarked against Kraken2, Centrifuger, Metabuli and sylph on the same viral database, EsViritu led or tied in abundance accuracy at every taxonomic rank and reported essentially no false positives in pathogen-free samples. As the preprint does not address long reads, its performance on nanopore data remains to be tested. Din et al. (2026) described a method that adds plasmid internal standards to long-read metagenomes to derive absolute, strain-level abundances (bioRxiv preprint, 29 September; [preprint](https://www.biorxiv.org/content/10.64898/2026.09.28.754546v1)).

## Tools and databases

GTDB-Tk 2.8.0 (13 October) applies the same species-assignment rule in `classify` and `classify_wf`, so species calls may differ from version 2.7.x, mainly in closely related genera ([release notes](https://github.com/Ecogenomics/GTDBTk/releases/tag/2.8.0)). The release uses the same R232 reference package and therefore requires no new download, although older versions cannot resume from a 2.8.0 output directory. A new MetaPhlAn database build, `mpa_vJan26_CHOCOPhlAnSGB_202605_EGBv1`, appeared on the bioBakery server on 13 October ([database folder](http://cmprod1.cibio.unitn.it/biobakery4/metaphlan_databases/)). As no release note yet documents the changes, a switch to this build should await documentation.

The legacy NCBI Taxonomy Browser is being replaced in October, which may break scripts that scrape or link the former `wwwtax.cgi` pages, while the taxonomy itself and the taxdump files remain unaffected ([NCBI](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi)). POD5 0.3.49 (8 October) accelerates the migration of raw signal files ([release notes](https://github.com/nanoporetech/pod5-file-format/releases/tag/0.3.49)). The preceding version 0.3.48 (21 September) resolved a failure of older libraries to read newer files, which is relevant where POD5 versions differ across instruments.

## Releases shortly before this period

The following releases appeared in September, before 25 September:

- Kraken2 2.17.2 (23 September), adding k-mer reporting for multi-database classification and speed improvements ([releases](https://github.com/DerrickWood/kraken2/releases))
- sylph 1.0.0 (14 September), the first 1.0 release ([releases](https://github.com/bluenote-1577/sylph/releases))
- RefSeq Release 237 (4 September) ([NCBI RefSeq](https://www.ncbi.nlm.nih.gov/refseq/))
- Dorado 1.3.4 (3 September), a bug-fix release for a crash with high-accuracy (HAC) models ([releases](https://github.com/nanoporetech/dorado/releases))

## Upcoming

ONT has announced that it will present tools for building custom "digital panels" at ASHG 2026, 20 to 24 October ([ONT](https://nanoporetech.com/about/events/conferences/ashg-2026)). Adaptive sampling is used by many laboratories to deplete host DNA or to enrich for pathogens.

## References

- Barbian, Hannah J., Michelle Funk, Stephanie R. Black, Mary K. Hayden, Shane Zelencik, Brian F. Borah, David Zhang, et al. 2026. 'Detecting measles virus in hospital air during a local outbreak'. *medRxiv* (preprint). https://doi.org/10.64898/2026.09.25.26363929.
- Berglund, Björn, Vaishnavi Divya Shridar, Marie Wrande, Jon Jerlström-Hultqvist, Stefan Engblom, Linus Sandegren, and Sanna Koskiniemi. 2026. 'Wastewater is Not a Reliable Proxy for Clinical Carbapenem Resistance Prevalence in *E. coli*'. *medRxiv* (preprint). https://doi.org/10.64898/2026.10.02.26364587.
- Brown, C. L., M. A. Rumi, L. McDaniel, A. Maile-Moskowitz, J. Sein, L. Nguyen, M. Choi, et al. 2026. 'Resistance indicators in sewage microbiota mirror clinical antibiotic use with temporal lag linked to host'. *Nature Communications*. https://doi.org/10.1038/s41467-026-78142-3.
- Din, M. Omar, Caitriona Brennan, Jianshu Zhao, Renee Oles, Lucas Patel, Amanda Birmingham, Dilara M. Sevilir, et al. 2026. 'Genome-resolved ecology and evolution of the microbiome enabled by quantitative long-read metagenomics'. *bioRxiv* (preprint). https://doi.org/10.64898/2026.09.28.754546.
- Forrest-Hammond, Robbie, Angelika Kopec, Adela Alcolea-Medina, Rahul Batra, Katherine Brown, Virve Enne, Jonathan Edgeworth, et al. 2026. 'Implementation of rapid pan-microbial metagenomics in paediatric intensive care: a single-centre, prospective, observational study'. *The Lancet Microbe*: 101461. https://doi.org/10.1016/j.lanmic.2026.101461.
- Prakash, Harihara, Vasanthi Avadhanula, Michael J. Tisza, Juwan Cormier, Matthew C. Ross, Ryan K. Perez, James D. Chang, et al. 2026. 'Four Years of Continuous Weekly Wastewater Analysis Reveals Sequencing as a Robust Alternative to PCR for Respiratory Virome Surveillance'. *medRxiv* (preprint). https://doi.org/10.64898/2026.10.13.26364774.
- Sørensen, Bertil, Connor L. Brown, Mantas Sereika, Søren Heidenbach, Philip Hugenholtz, Mads Albertsen, and Francesco Delogu. 2026. 'Nation-scale recovery of complete environmental plasmids pushes the boundaries of plasmid diversity through long-read sequencing'. *bioRxiv* (preprint). https://doi.org/10.64898/2026.10.06.756670.
- Tisza, Michael J., Shelby R. Simar, Jackie K. Zorz, Sara J. Javornik Cregeen, and Anthony W. Maresso. 2026. '*EsViritu* is a sensitive and specific profiler for viral pathogen detection and genome recovery in metagenomes'. *bioRxiv* (preprint). https://doi.org/10.64898/2026.09.29.755457.
- Wolfe, Marlene K., Devin North, Alexander L. Jaffe, Alessandro Zulli, Dorothea Duong, Bridgette Shelden, Miriam Goldman, et al. 2026. 'Prospective metagenomic sequencing of wastewater across the United States yields robust viral enrichment and concordance with digital PCR measurements'. *Applied and Environmental Microbiology*: e01020-26. https://doi.org/10.1128/aem.01020-26.

### Software, databases and announcements

- bioBakery. 2026. MetaPhlAn database folder. http://cmprod1.cibio.unitn.it/biobakery4/metaphlan_databases/. Accessed 16 October 2026.
- Ecogenomics. 2026. GTDB-Tk release 2.8.0. https://github.com/Ecogenomics/GTDBTk/releases/tag/2.8.0. Accessed 16 October 2026.
- Kraken2. 2026. Release notes. https://github.com/DerrickWood/kraken2/releases. Accessed 16 October 2026.
- National Center for Biotechnology Information (NCBI). 2026. RefSeq. https://www.ncbi.nlm.nih.gov/refseq/. Accessed 16 October 2026.
- National Center for Biotechnology Information (NCBI). 2026. Taxonomy Browser. https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi. Accessed 16 October 2026.
- Oxford Nanopore Technologies. 2026. ASHG 2026 conference page. https://nanoporetech.com/about/events/conferences/ashg-2026. Accessed 16 October 2026.
- Oxford Nanopore Technologies. 2026. Dorado release notes. https://github.com/nanoporetech/dorado/releases. Accessed 16 October 2026.
- Oxford Nanopore Technologies. 2026. POD5 file format release 0.3.49. https://github.com/nanoporetech/pod5-file-format/releases/tag/0.3.49. Accessed 16 October 2026.
- sylph. 2026. Release notes. https://github.com/bluenote-1577/sylph/releases. Accessed 16 October 2026.
