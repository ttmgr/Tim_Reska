# Tim Reska

**PhD Candidate in Genomics & Bioinformatics | AI-Augmented Scientific Infrastructure | Research Project Lead**

Helmholtz Munich & Technical University of Munich · Munich, Germany

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://linkedin.com/in/timreska)
[![Email](https://img.shields.io/badge/Email-D14836?logo=gmail&logoColor=white)](mailto:timreska@gmail.com)
[![Google Scholar](https://img.shields.io/badge/Google_Scholar-4285F4?logo=google-scholar&logoColor=white)](https://scholar.google.com)

---

## About

I build and deploy AI-augmented scientific infrastructure — from scoping through production — across genomics, biosurveillance, and clinical collaboration contexts.

As the **founding member** of the Helmholtz AI research group, I built the team's operations from scratch: set up the entire laboratory, established SOPs and experimental workflows, and took on full operational leadership — while simultaneously driving my own PhD research. I've since contributed to **7 research projects** (independently initiating and leading 2), trained **6 researchers** in laboratory and computational methods, and created comprehensive troubleshooting guides and documentation adopted group-wide.

On the technical side, I've integrated OpenAI Codex and Model Context Protocol (MCP) into real-time nanopore sequencing pipelines, accelerating development cycles by **40%**, and systematically evaluated **5+ LLMs** (GPT3/4/5, Claude2/3/4, Gemini2/3, Perplexity, Grok) for code generation, data interpretation, and analysis tasks.

I care about three things: **shipping production systems**, **validating them scientifically**, and **communicating their impact** to diverse stakeholders — from lab technicians to institutional decision-makers.

---

## What I Bring

| For Tech Companies | For Strategy Consulting | For Advisory & Restructuring |
|:---|:---|:---|
| Production ML/AI pipelines | Structured problem decomposition | Data-driven turnaround analysis |
| LLM evaluation & integration | Cross-functional stakeholder alignment | Operational process optimization |
| End-to-end system architecture | International project coordination (DE/FR/ES) | Cost-efficiency through automation |
| Open source & developer tooling | Publication-grade deliverables | Risk assessment under uncertainty |

---

## PhD Thesis — One Health Biosurveillance Framework

**"Genome-Resolved Surveillance of Air and Water Microbiomes using Nanopore Sequencing"**

My dissertation implements an integrated One Health surveillance strategy by developing a common approach to two environmentally and methodologically distinct matrices — **air** and **water** — using a shared, culture-independent workflow built around field-deployable nanopore sequencing.

### Comparative Study Design

| Parameter | Air Study (Publication I) | Aquatic Study (Publication II) |
|:---|:---|:---|
| **Matrix** | Air | Water |
| **Sampling** | Active liquid impingement | Passive membrane adsorption |
| **Nucleic acids** | DNA only | DNA and RNA (dual extraction) |
| **Sequencing** | Shotgun metagenomics | Shotgun metagenomics, RNA virome, vertebrate eDNA metabarcoding, AIV WGS |
| **Study sites** | Greenhouse & natural environment (Munich), urban campaign (Barcelona) | 12 lentic wetlands across Germany, France, and Spain |
| **Sample size** | n = 48 (12 + 6 + 30) | n = 24 (2 replicates × 12 sites) |
| **Key challenge** | Maximizing DNA recovery from sparse biomass | Inhibitor removal; dual nucleic acid isolation |

The primary challenge was adapting a central analytical pipeline to two distinct sample types: the **aerobiome**, characterized by ultra-low biomass demanding high-volume concentration and stringent contamination control (Reska et al. 2024), and **aquatic ecosystems**, characterized by logistical complexity and multiomics targets requiring integrative sampling and parallel isolation of both DNA and RNA (Perlas, Reska, Sánchez-Cano, et al. 2025).

---

## Featured Projects

### PCR-Free Nanopore Biosurveillance System
**Python · Snakemake · HPC · Illumina · Nanopore · PacBio**

Initiated and delivered end-to-end deployment of a PCR-free nanopore surveillance system for low-biomass air samples across **7 international sites** (Munich, Barcelona, and more). Reduced diagnostic turnaround from **48h to 6h**.

**Impact:**
- Methodology validated through peer review — published in *ISME Communications* (2024)
- Adopted as institutional surveillance strategy at University of Zurich
- Detected Avian Influenza (H4 subtype) and critical AMR reservoirs in field deployments

→ **[View pipeline code](pipelines/aerobiome/)** — Snakemake workflow with ULB contamination control

---

### One Health Multinational Biosurveillance Campaign
**Multi-omics · DNA/RNA/eDNA · Shotgun Metagenomics · RNA Virome · AIV WGS**

Directed a multinational biosurveillance campaign across **12 wetland ecosystems** in Germany, France, and Spain. Managed multi-omics workflows (DNA/RNA/eDNA) including shotgun metagenomics, RNA virome analysis, vertebrate eDNA metabarcoding, and Avian Influenza whole-genome sequencing across distributed teams despite logistical disruptions, equipment failures, and real-time protocol pivots.

**Impact:**
- Identified **13-fold higher pathogenic loads** at anthropogenic vs. natural sites
- Findings integrated into University of Zurich's institutional surveillance strategy
- Published in peer-reviewed journal (Perlas, Reska, Sánchez-Cano, et al. 2025)

→ **[View pipeline code](pipelines/wetland-surveillance/)** — Multi-omics Snakemake workflow (4 analysis tracks)

---

### LLM Integration for Scientific Workflows
**OpenAI Codex · Claude · Gemini · MCP · PyTorch**

Systematic evaluation and integration of AI tools into research workflows:

- Integrated **OpenAI Codex and MCP** into bioinformatics pipelines for automated output parsing, sorting, and real-time summarization during active nanopore sequencing runs
- Evaluated **5+ LLMs** across code generation, scientific literature interpretation, and data analysis — developed internal model selection and routing guidelines adopted by collaborators across institutions
- Applied **RNN models (PyTorch)** for sequence classification in genomic analysis workflows with published evaluation metrics (AUROC, precision, sensitivity, specificity)

---

### Bioinformatics Pipeline Infrastructure
**Python · Snakemake · Nextflow · Illumina · Nanopore · PacBio**

Built end-to-end bioinformatics pipelines for three major sequencing platforms, including beta-testing novel technology in collaboration with industry partners. Managed full lifecycle from architecture design through production deployment on HPC infrastructure. Established computational frameworks adopted by the entire research group.

**Scope:**
- Automated quality control, assembly, taxonomic classification, and variant calling
- Designed for reproducibility with containerized environments and version-controlled workflows
- Production deployment serving multiple research groups

---

## Leadership & Operations

**Founding member** of the Helmholtz AI research group (est. 2022). Volunteered to take on full laboratory management and operational leadership alongside doctoral research — an unusual scope for a PhD candidate.

| Area | Scope |
|:---|:---|
| **Laboratory setup** | Built the lab from zero — equipment, workflows, inventory, purchasing |
| **SOPs & documentation** | Created all Standard Operating Procedures and troubleshooting guides |
| **Team development** | Trained 6 researchers in wet-lab and computational methods |
| **Safety & compliance** | Occupational Safety Officer — workshops, regulatory compliance, operational safety |
| **Project portfolio** | Contributed to 7 research projects, independently led 2 |

### International Collaboration Network

Active research collaborations across **5+ institutions** in 4 countries:

- Klinikum rechts der Isar (TU Munich Hospital)
- Barcelona Institute for Global Health (ISGlobal)
- University of Zurich & agricultural industry partners
- School of Agriculture, University of Turin
- Spanish Institute for Game and Wildlife Research (IREC)

---

## Publications

**8 publications** · Invited speaker at **TUM** (70 attendees), **ETH Zurich** (40), **University of Cambridge** (12)

---

#### Air Monitoring by Nanopore Sequencing
**Reska T**, Pozdniakova S, Urban L · *ISME Communications* (2024)

Developed nanopore-based metagenomics for air microbiome profiling. Achieved species-level taxonomic resolution across controlled greenhouse environments, natural outdoor settings, and urban locations in Barcelona.

---

#### Real-Time Genomic Pathogen, Resistance, and Host Range Characterization from Passive Water Sampling of Wetland Ecosystems
Perlas A\*, **Reska T**\*, Sánchez-Cano A, Mejías-Molina C, Gygax D, Martínez-Puchol S, Rusiñol M, Eger E, Schaufler K, Höfle U, Croville G, Le Loc'h G, Guérin J-L, Urban L · *Preprint* (2025) · [DOI](https://doi.org/10.1101/2025.09.05.674394)

Holistic framework combining passive water sampling with nanopore sequencing to characterize pathogen load, AMR, and host range across wetland ecosystems along the East Atlantic Flyway. Showed anthropogenically impacted ecosystems consistently exhibit higher pathogen and AMR gene abundances. Detected and characterized avian influenza at a third of monitored sites, using eDNA to explore potential animal hosts.

*\*Shared first authorship*

---

#### Improvements in RNA and DNA Nanopore Sequencing for Rapid Genetic Characterization of Avian Influenza
Perlas A, **Reska T**, Croville G, Tarrés-Freixas F, Guérin J-L, Majó N, Urban L

Systematically compared latest DNA and RNA nanopore sequencing approaches for characterizing avian influenza virus strains. Demonstrated that R10 DNA nanopore chemistry after reverse transcription outperformed direct RNA sequencing for accuracy and throughput.

---

#### Environmental Screening through Nanopore Native Sequencing Leads to the Detection of *Batrachochytrium dendrobatidis* in La Mandria Regional Park, Italy
Varzandi AR, **Reska T**, Urban L, Zanet S, Ferroglio E · *Global Ecology and Conservation* (2025) · [DOI](https://doi.org/10.1016/j.gecco.2025.e03517)

Used PCR-free nanopore native sequencing on water samples from 8 irrigation channels to detect wildlife pathogens. First detection of the fungal pathogen *B. dendrobatidis* in this area — confirmed by ddPCR, and identified months before the first case was reported in wild animals of the park.

---

#### Detection of Hidden Antibiotic Resistance through Real-Time Genomics
Sauerborn E, Corredor NC, **Reska T**, Perlas A, Vargas da Fonseca Atum S, Goldman N, Wantia N, Prazeres da Costa C, Foster-Nyarko E & Urban L · ***Nature Communications*** 15, 5494 (2024)

Demonstrated how nanopore sequencing detects low-abundance plasmid-mediated resistance missed by conventional diagnostics — with direct implications for clinical treatment decisions in multi-drug resistant infections.

`22,000+ Accesses` · `43 Citations` · `74 Altmetric`

---

#### Nanopore- and AI-Empowered Microbial Viability Inference
Multiple authors incl. **Reska T**

Created a computational framework using nanopore sequencing and deep neural networks to distinguish DNA from viable vs. dead microorganisms directly from raw signal data. Applied to estimate viability of obligate intracellular *Chlamydia* where traditional culture methods fail.

---

#### Partitioning RNAs by Length Improves Transcriptome Reconstruction (Ladder-seq)
Chakraborty S, [...] **Reska T** [...] Canzar S

Introduced Ladder-seq, which separates transcripts by length using denaturing gel electrophoresis before sequencing. Extended kallisto and StringTie algorithms to use length information — revealing 40% more genes harboring isoform switches compared to conventional RNA-seq.

---

#### Real-Time Genomics for One Health
Urban L, Perlas A, [...] **Reska T** [...] et al. · *Review*

Review describing how real-time nanopore genomic analyses benefit One Health — covering zoonotic disease surveillance, food security, environmental microbiome monitoring, antimicrobial resistance tracking, wildlife conservation, biodiversity monitoring, and invasive species detection.

## Technical Skills

```
Languages        Python · TypeScript · R · SQL · Bash
AI/ML            LLM Integration (GPT-4, Claude, Gemini) · MCP · PyTorch · RNNs · Prompt Engineering
Cloud & Infra    AWS (Lambda, DynamoDB, Bedrock, Step Functions, S3) · Terraform · Docker
Data & Pipelines Snakemake · Nextflow · Pandas · NumPy · Bioinformatics (Illumina, Nanopore, PacBio)
Sequencing       Shotgun Metagenomics · RNA Virome · eDNA Metabarcoding · Whole-Genome Sequencing
DevOps           GitHub Actions · CI/CD · HPC Deployment · Infrastructure as Code
Scientific       Experimental Design · Statistical Analysis · Peer Review · Grant Writing
```

---

## Education

| Degree | Institution | Period | Highlights |
|--------|------------|--------|------------|
| **PhD** Genomics & Bioinformatics | Helmholtz Munich & TU Munich | 2022 – 2026 | Thesis: Genome-Resolved Surveillance of Air and Water Microbiomes using Nanopore Sequencing |
| **M.Sc.** Biochemistry | LMU Munich | 2019 – 2022 | GPA: 1.6/1.0 · Master Thesis Grade: 1.3 · Thesis: Combining 2nd and 3rd Generation Sequencing |

---

## What Ties It Together

I work across technical depth and operational breadth — building production AI pipelines one day, coordinating a multinational field campaign the next. What stays constant is a preference for structured problem-solving, measurable outcomes, and clear communication across audiences.

- **Technical:** 5+ LLMs evaluated and deployed in production, MCP integrations for real-time sequencing, full-stack pipeline architecture across three sequencing platforms
- **Operational:** Diagnostic turnaround reduced by 87.5% (48h → 6h), development cycles accelerated by 40%, multinational campaigns managed across 3 countries with real-time pivots
- **Scientific:** 5 peer-reviewed publications, invited talks at TUM, ETH Zurich, and Cambridge, methodology adopted into institutional surveillance strategies

---

## Currently

- Finishing PhD thesis (expected mid-2026)
- Exploring opportunities at the intersection of technology, strategy, and impact

---

<p align="center">
  <i>Available for conversations about technology, strategy, and building things that matter.</i>
  <br><br>
  <a href="mailto:timreska@gmail.com">timreska@gmail.com</a> · +49 151 29 13 07 11
</p>
