# PKV ML Framework Explorer

A self-contained, browser-based catalogue of machine-learning and actuarial methods relevant to German private health insurance (PKV) workflows. Each method is documented with the problem it solves, a worked example, the underlying assumptions, and the trade-offs you accept when choosing it.

## What this is

An onboarding and reference instrument — for actuaries new to ML, ML practitioners new to insurance, and reviewers who want a quick refresher on a specific method's strengths and limits. The interface language is German (the target audience is the DACH PKV market). Designed as a companion to the applied-ML work in [`../disease-progression/`](../disease-progression/) and [`../medrisk/`](../medrisk/).

## Run it

```bash
open index.html          # macOS
xdg-open index.html      # Linux
```

No build step, no dependencies. Single HTML entry point.

## Methods covered

```mermaid
flowchart TB
    subgraph Stat["Statistical baselines"]
        LR[Logistische<br/>Regression]
        SA[Survival<br/>analysis]
        LT[Aktuarielle<br/>Sterbetafeln]
    end

    subgraph ML["Klassisches ML"]
        RF[Random<br/>Forest]
        OD["Outlier detection<br/>(Z-Score · Mahalanobis)"]
    end

    subgraph DL["Deep Learning"]
        LSTM[LSTM für<br/>Zeitreihen]
        AE[Autoencoder<br/>Anomalie-Detektion]
    end

    subgraph TS["Zeitreihen-Glättung"]
        MA[Moving<br/>Average]
        ES[Exponential<br/>Smoothing]
    end

    subgraph AI["Agentic AI"]
        ORCH[Agentische KI<br/>Orchestrierungsschicht]
    end

    Stat -.- UseCase[(PKV-Workflows:<br/>Tarifierung · Risikoselektion ·<br/>Schadensprognose · Portfolio-Monitoring)]
    ML -.- UseCase
    DL -.- UseCase
    TS -.- UseCase
    AI -.- UseCase

    classDef stat fill:#e8f4fd,stroke:#1a73e8,color:#0b1b2b
    classDef ml fill:#fef7e0,stroke:#f9ab00,color:#2b1b00
    classDef dl fill:#fce8e6,stroke:#ea4335,color:#3a0f0a
    classDef ts fill:#e8f5e9,stroke:#34a853,color:#0b1f10
    classDef ai fill:#f3e8fd,stroke:#7c3aed,color:#1a0b35
    classDef use fill:#f5f5f5,stroke:#666,color:#222

    class LR,SA,LT stat
    class RF,OD ml
    class LSTM,AE dl
    class MA,ES ts
    class ORCH ai
    class UseCase use
```

| Method | Typical PKV use case |
|:-------|:---------------------|
| Logistische Regression | Storno-Wahrscheinlichkeit, Risikoeinstufung |
| Random Forest | Multivariates Risiko-Scoring, Variable importance |
| LSTM | Zeitabhängige Schadensvorhersage, Krankheitsverläufe |
| Autoencoder | Anomalie-Detektion in Schadensströmen |
| Z-Score / Mahalanobis | Univariate / multivariate Ausreißer-Erkennung |
| Aktuarielle Sterbetafeln | Reservierung, Prämienberechnung |
| Moving Average / Exponential Smoothing | Kurzfristige Trendprognose |
| Survival analysis | Time-to-event-Modellierung (Erstdiagnose, Reha-Eintritt) |
| Agentische KI | Orchestrierung mehrstufiger Underwriting-Workflows |

## Stack

Vanilla HTML + CSS + JavaScript, single file. No bundler, no runtime dependencies.

## Companion projects

- [`../disease-progression/`](../disease-progression/) — production-grade implementation of survival analysis and multistate Markov on synthetic clinical cohorts.
- [`../medrisk/`](../medrisk/) — full underwriting platform that operationalizes several of these methods with confidence-calibrated failure detection.
