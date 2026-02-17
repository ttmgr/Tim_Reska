# Tim Reska

**PhD Candidate in Genomics & Bioinformatics | AI-Augmented Scientific Infrastructure | Research Project Lead**

Helmholtz Munich & Technical University of Munich · Munich, Germany

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://linkedin.com/in/timreska)
[![Email](https://img.shields.io/badge/Email-D14836?logo=gmail&logoColor=white)](mailto:timreska@gmail.com)
[![Google Scholar](https://img.shields.io/badge/Google_Scholar-4285F4?logo=google-scholar&logoColor=white)](https://scholar.google.com)

---

## About

I build and deploy AI-augmented scientific infrastructure — from scoping through production — across genomics, biosurveillance, and clinical collaboration contexts.

As the **founding member** of the Helmholtz AI research group, I built the team's operations from scratch: established the entire laboratory infrastructure, developed SOPs and experimental workflows, and assumed full operational leadership — while simultaneously driving my own PhD research. I've since contributed to **7 research projects** (independently initiating and leading 2), trained **6 researchers** in laboratory and computational methods, and created comprehensive troubleshooting guides and documentation adopted group-wide.

On the technical side, I've integrated OpenAI Codex and Model Context Protocol (MCP) into real-time nanopore sequencing pipelines, accelerating development cycles by **~40%**, and systematically evaluated **22 LLM versions** (GPT-4o through GPT-5, Claude Sonnet 3.5 through Opus 4.6, Gemini 2.0 through 3 Pro) for scientific code generation — developing a structured evaluation framework with **publication-grade methodology** that quantifies where AI can reliably augment expert work and where it introduces hidden risk.

I care about three things: **shipping production systems**, **validating them scientifically**, and **communicating their impact** to diverse stakeholders — from lab technicians to institutional decision-makers and industry partners.

---

## What I Bring

| For Tech / AI Companies | For Strategy & Advisory | For Life Sciences & Pharma |
|:---|:---|:---|
| Production AI/ML pipelines with domain validation | Structured problem decomposition under ambiguity | Regulatory-aware scientific infrastructure |
| LLM evaluation frameworks (22 models, 5 dimensions, 7 tasks) | Cross-functional stakeholder alignment (lab ↔ clinic ↔ compute) | GxP-aware workflow design & documentation |
| End-to-end system architecture across 3 sequencing platforms | International project coordination across 5 institutions in 4 countries | Translational genomics from research to surveillance deployment |
| AI safety & reliability assessment in high-stakes domains | Publication-grade deliverables & evidence-based recommendations | One Health framework: air, water, wildlife, clinical |

---

## PhD Thesis — One Health Biosurveillance Framework

**"Genome-Resolved Surveillance of Air and Water Microbiomes using Nanopore Sequencing"**

My dissertation implements an integrated One Health surveillance strategy by developing a common approach to two environmentally and methodologically distinct matrices — **air** and **water** — using a shared, culture-independent workflow built around field-deployable nanopore sequencing. The immediate translational relevance is a portable, culture-independent surveillance system applicable to public health, environmental monitoring, and potentially pharmaceutical quality control settings.

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
| **Potential applications** | Environmental air monitoring, cleanroom bioburden assessment | Waterborne pathogen surveillance, environmental compliance monitoring |

The primary challenge was adapting a central analytical pipeline to two distinct sample types: the **aerobiome**, characterized by ultra-low biomass demanding high-volume concentration and stringent contamination control (Reska et al. 2024), and **aquatic ecosystems**, characterized by logistical complexity and multiomics targets requiring integrative sampling and parallel isolation of both DNA and RNA (Perlas, Reska, Sánchez-Cano, et al. 2025).

---

## Featured Projects

### PCR-Free Nanopore Biosurveillance System
**Python · Snakemake · HPC · Illumina · Nanopore · PacBio**

Initiated and delivered end-to-end deployment of a PCR-free nanopore surveillance system for low-biomass air samples across **7 international sites** (Munich, Barcelona, and more). Reduced diagnostic turnaround from **48h to 6h** — an **87.5% reduction** in time-to-actionable-insight.

**Impact:**
- Methodology validated through peer review — published in *ISME Communications* (2024)
- Adopted as institutional surveillance strategy at University of Zurich
- Detected Avian Influenza (H4 subtype) and critical AMR reservoirs in field deployments
- Pipeline serves as ground truth for the [LLM evaluation study](llm-eval/), demonstrating practical application of validated workflows as AI benchmarks

→ **[View pipeline code](pipelines/aerobiome/)** — Snakemake workflow with ULB contamination control

---

### One Health Multinational Biosurveillance Campaign
**Multi-omics · DNA/RNA/eDNA · Shotgun Metagenomics · RNA Virome · AIV WGS**

Directed a multinational biosurveillance campaign across **12 wetland ecosystems** in Germany, France, and Spain. Managed multi-omics workflows (DNA/RNA/eDNA) including shotgun metagenomics, RNA virome analysis, vertebrate eDNA metabarcoding, and Avian Influenza whole-genome sequencing across distributed teams despite logistical disruptions, equipment failures, and real-time protocol pivots.

**Impact:**
- Identified **13-fold higher pathogenic loads** at anthropogenic vs. natural sites — direct evidence for environmental drivers of antimicrobial resistance proliferation
- Findings integrated into University of Zurich's institutional surveillance strategy
- Published in peer-reviewed journal (Perlas, Reska, Sánchez-Cano, et al. 2025)

→ **[View pipeline code](pipelines/wetland-surveillance/)** — Multi-omics Snakemake workflow (4 analysis tracks)

---

### Systematic LLM Evaluation for Scientific Pipeline Generation
**22 Models · 5 Scoring Dimensions · 7 Pipeline Steps · 154 Evaluations**

Designed and executed a structured evaluation framework testing whether large language models can generate scientifically valid bioinformatics pipelines. The key finding: **"plausible but wrong"** — LLMs produce code that runs, looks reasonable, and would pass surface-level review, but makes domain-specific choices that experts would immediately reject. No model produced a fully correct end-to-end pipeline until the latest generation (GPT-5, Opus 4.5, Gemini 3 Pro).

**Relevance across sectors:**
- **AI industry:** Demonstrates the gap between code-correctness benchmarks and domain-validity benchmarks — critical for responsible AI deployment in regulated domains
- **Consulting / advisory:** Provides a structured framework for evaluating AI readiness in any domain where "runs correctly" ≠ "produces valid results"
- **Pharma / life sciences:** Quantifies the reliability gap that must be closed before AI-generated analysis pipelines can be used in GxP-regulated or clinical settings

→ **[View full study](llm-eval/)** — Evaluation framework, scoring matrices, and analysis scripts

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

**Founding member** of the Helmholtz AI research group (est. 2022). Volunteered to take on full laboratory management and operational leadership alongside doctoral research — an unusual scope for a PhD candidate that demonstrates comfort with ambiguity and end-to-end ownership.

| Area | Scope |
|:---|:---|
| **Laboratory setup** | Built the lab from zero — equipment, workflows, inventory, purchasing |
| **SOPs & documentation** | Created all Standard Operating Procedures and troubleshooting guides |
| **Team development** | Trained 6 researchers in wet-lab and computational methods |
| **Safety & compliance** | Occupational Safety Officer — workshops, regulatory compliance, operational safety |
| **Project portfolio** | Contributed to 7 research projects, independently led 2 |
| **Budget & procurement** | Managed equipment specifications and purchasing decisions across laboratory buildout |

### International Collaboration Network

Active research collaborations across **5+ institutions** in 4 countries:

- Klinikum rechts der Isar (TU Munich Hospital) — clinical AMR surveillance
- Barcelona Institute for Global Health (ISGlobal) — urban metagenomics
- University of Zurich & agricultural industry partners — institutional surveillance adoption
- School of Agriculture, University of Turin — environmental pathogen detection
- Spanish Institute for Game and Wildlife Research (IREC) — wildlife disease ecology

---

## Publications

**8 publications** · **22,000+ accesses** · **43+ citations** · **74 Altmetric** on lead publication
Invited speaker at **TUM** (70 attendees), **ETH Zurich** (40), **University of Cambridge** (12)

---

#### Air Monitoring by Nanopore Sequencing
**Reska T**, Pozdniakova S, Urban L · *ISME Communications* (2024) · [DOI](https://doi.org/10.1093/ismeco/ycae058)

Developed nanopore-based metagenomics for air microbiome profiling. Achieved species-level taxonomic resolution across controlled greenhouse environments, natural outdoor settings, and urban locations in Barcelona. This pipeline serves as the validated ground truth for the [LLM evaluation study](llm-eval/).

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
AI/ML            LLM Evaluation & Integration (22 models) · MCP · PyTorch · RNNs · Prompt Engineering
Cloud & Infra    AWS (Lambda, DynamoDB, Bedrock, Step Functions, S3) · Terraform · Docker
Data & Pipelines Snakemake · Nextflow · Pandas · NumPy · Bioinformatics (Illumina, Nanopore, PacBio)
Sequencing       Shotgun Metagenomics · RNA Virome · eDNA Metabarcoding · Whole-Genome Sequencing
DevOps           GitHub Actions · CI/CD · HPC Deployment · Infrastructure as Code
Scientific       Experimental Design · Statistical Analysis · Peer Review · Grant Writing
Regulatory       GxP Awareness · SOP Development · Occupational Safety · Data Integrity
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

- **Technical:** 22 LLM versions evaluated with publication-grade methodology, MCP integrations for real-time sequencing, full-stack pipeline architecture across three sequencing platforms
- **Operational:** Diagnostic turnaround reduced by 87.5% (48h → 6h), development cycles accelerated by ~40%, multinational campaigns managed across 4 countries with real-time pivots
- **Scientific:** 8 peer-reviewed publications (Nature Communications, ISME Communications), invited talks at TUM, ETH Zurich, and Cambridge, methodology adopted into institutional surveillance strategies

---

## Currently

- Finishing PhD thesis (expected mid-2026)
- Exploring opportunities at the intersection of technology, strategy, and impact — particularly in AI safety/evaluation, life sciences consulting, or translational genomics

---

<p align="center">
  <i>Available for conversations about technology, strategy, and building things that matter.</i>
  <br><br>
  <a href="mailto:timreska@gmail.com">timreska@gmail.com</a> · +49 151 29 13 07 11
</p>
