# MedRisk-ADH — Technische Anleitung

## 1. Was ist MedRisk-ADH?

MedRisk-ADH ist ein Proof-of-Concept fuer KI-gestuetzte medizinische Risikopruefung mit eingebauter Fehlererkennung. Das System erkennt automatisch, wenn ein Modell eine selbstsichere Vorhersage auf schlechten Daten trifft — sogenannte "Plausible-but-Wrong" (PBW) Entscheidungen.

### Das zentrale Problem

Jedes ML-Modell in der Risikopruefung hat eine blinde Stelle: Es kann nicht zwischen "Ich bin sicher, weil die Daten gut sind" und "Ich bin sicher, weil ich mit Durchschnittswerten auffuelle" unterscheiden. Beide Faelle produzieren die gleiche Konfidenz-Zahl.

Bei 100.000 Policen pro Jahr und einer 2% PBW-Rate sind das 2.000 falsch bewertete Risiken — unsichtbar in AUC/Accuracy, aber ein reales Haftungsrisiko.

### Die Loesung

MedRisk-ADH fuegt eine **Validierungsschicht vor der Entscheidung** ein:

```
Patientendaten
    |
    v
[Datenqualitaetsscore (DQS)]  <-- VOR der Modellvorhersage
    |
    v
[Modelle: XGBoost + Cox PH + CTMC]
    |
    v
[Validierung: PBW + CCM + EPU]
    |
    +--> ACCEPT  (DQS stuetzt die Vorhersage)
    +--> REVIEW  (Mensch muss draufschauen)
    +--> REJECT  (Vorhersage wird verworfen)
```

---

## 2. Projektstruktur

```
MedRisk-ADH/
  src/medrisk/
    data/           # Datenmodelle, ICD-10, Charlson, Synthetic Generator
    features/       # Feature Engineering (ICD-10 Encoding, Feature Matrix)
    models/         # XGBoost, Cox PH, CTMC Multistate
    validation/     # DQS, PBW-Detektor, CCM, EPU
    explain/        # SHAP Erklaerbarkeit
    reporting/      # PDF-Report-Generierung
    evaluation/     # Metriken (AUC, Brier, Concordance)
  tests/            # 192 Unit-Tests
  notebooks/        # 5 Jupyter Notebooks (01-05)
  scripts/          # Slide-Deck-Generator
  configs/          # Pipeline-Konfiguration (YAML)
  docs/             # Dokumentation
```

### Wichtige Befehle

```bash
make install      # Paket installieren (dev mode)
make test         # 192 Tests ausfuehren (~4 Sekunden)
make lint         # Code-Qualitaet pruefen (ruff)
make notebooks    # Alle 5 Notebooks ausfuehren
make clean        # Build-Artefakte loeschen

python scripts/generate_slides.py   # Pitch-Deck generieren
```

---

## 3. Die Datenpipeline im Detail

### 3.1 Synthetische Patientengenerierung

**Datei:** `src/medrisk/data/synthetic.py`

Wir generieren DSGVO-sichere synthetische Patienten. Kein echtes Patientendata.

**Zwei-Stufen-Generierung:**
1. **Ground Truth**: Echte Krankheitstrajektorien via CTMC simulieren
2. **Degradierung**: Ground Truth mit marktspezifischer Unvollstaendigkeit und Rauschen ueberlagern

```python
from medrisk.data.synthetic import generate_cohort, cohort_to_dataframe

# 5000 Patienten pro Markt, 4 Maerkte = 20.000 Patienten
cohort = generate_cohort(n_per_market=5000, seed=42)
df = cohort_to_dataframe(cohort)
```

**Vier Marktprofile:**

| Markt | Coding | Labor | Rauschen | Diagnose-Lag |
|-------|--------|-------|----------|-------------|
| DE    | 95%    | 92%   | 2%       | 14 +/- 7 Tage |
| FR    | 90%    | 88%   | 3%       | 60 +/- 30 Tage |
| ES    | 80%    | 75%   | 5%       | 30 +/- 20 Tage |
| INT   | 60%    | 50%   | 10%     | 90 +/- 60 Tage |

**28 Baseline-Praevalenzen** mit altersabhaengigen Multiplikatoren und Komorbiditaets-Netzwerk (z.B. Diabetes erhoet IHD-Risiko um Faktor 2.0).

### 3.2 Datenqualitaetsscore (DQS)

**Datei:** `src/medrisk/validation/data_quality.py`

Der DQS wird **vor** jeder Modellvorhersage berechnet. Er beantwortet: "Wie sehr sollte das Modell seinen eigenen Input vertrauen?"

```python
from medrisk.validation.data_quality import compute_dqs

result = compute_dqs(patient)
# result.dqs          -> 0.73
# result.tier         -> "caution"
# result.completeness -> 0.81
# result.consistency  -> 0.60
# result.recency      -> 0.72
```

**Formel:**
```
DQS = 0.40 * Completeness + 0.35 * Consistency + 0.25 * Recency
```

**Completeness (Gewicht 0.40):**
Anteil der vorhandenen Features an den erwarteten. Erwartet werden: 5 demografische, 17 Charlson-Kategorien, 10 Laborwerte, 8 Medikamenten-Flags = 40 total.

**Consistency (Gewicht 0.35):**
5 klinische Plausibilitaetsregeln:
- Diabetes-Code (E11*) → HbA1c >= 5.7%
- CKD Stage 4-5 → eGFR < 30
- Herzinsuffizienz (I50*) → NT-proBNP > 125
- Hypertonie (I10*) → SBP > 120 oder Antihypertensiva
- Kein Diabetes-Code → HbA1c < 6.5%

Ergebnis: Anteil der erfuellten Regeln an den anwendbaren Regeln.

**Recency (Gewicht 0.25):**
Exponentieller Abfall auf Laborwert-Alter:
```
weight = exp(-ln(2) / 1.4 * alter_in_jahren)
```
Halbwertszeit 1.4 Jahre. Ein 3 Jahre altes Labor zaehlt nur noch ~23%.

**Tier-Schwellen:**
- >= 0.80: **Adequate** → Automatisierte Entscheidung moeglich
- 0.60 - 0.80: **Caution** → Menschliche Pruefung
- < 0.60: **Insufficient** → Vorhersage wird abgelehnt

### 3.3 Feature Engineering

**Datei:** `src/medrisk/features/engineering.py`

```python
from medrisk.features.engineering import build_feature_matrix, get_targets

X, feature_names = build_feature_matrix(df)  # ~53 Features
events, times = get_targets(df)
```

Features (in Reihenfolge):
1. Numerisch: `age`, `bmi`
2. One-Hot: `sex_male`, `smoking_former`, `smoking_current`
3. Charlson: `charlson_index`
4. Diagnose-Flags: `has_diabetes`, `has_hypertension`, ... (28 Stueck)
5. Laborwerte: `lab_hba1c`, `lab_egfr`, ... (10 Stueck, Median-imputiert)
6. Medikamenten-Flags: `med_metformin`, `med_atorvastatin`, ... (8 Stueck)

### 3.4 Modelle

#### XGBoost Risk Classifier
**Datei:** `src/medrisk/models/xgb_classifier.py`

Binaere Klassifikation: hohes vs. niedriges Risiko.

```python
from medrisk.models.xgb_classifier import RiskClassifier

clf = RiskClassifier()  # 200 Baeume, Tiefe 6, lr 0.05
clf.fit(X_train, y_train, X_val=X_val, y_val=y_val)

proba = clf.predict_proba(X_test)          # Rohe Wahrscheinlichkeit
proba_cal = clf.predict_proba_calibrated(X_test)  # Nach Platt-Kalibrierung
```

Optional: Platt-Kalibrierung (Sigmoid) fuer besser kalibrierte Wahrscheinlichkeiten:
```python
clf.calibrate(X_cal, y_cal, method="sigmoid")
```

#### Cox Proportional Hazards
**Datei:** `src/medrisk/models/cox_ph.py`

Ueberlebensanalyse: Wann tritt ein Event (Tod, MI, Stroke, etc.) ein?

```python
from medrisk.models.cox_ph import CoxPHModel

cox = CoxPHModel(penalizer=0.01)
cox.fit(df, feature_cols=["age", "bmi", "charlson_index", ...])

print(cox.concordance_index)  # ~0.72
print(cox.hazard_ratios())    # Hazard Ratios pro Feature
```

#### CTMC Multistate Model
**Datei:** `src/medrisk/models/multistate.py`

Continuous-Time Markov Chain mit 5 Zustaenden:

```
Gesund (0) --> Risikofaktoren (1) --> Chronisch (2) --> Komplikation (3) --> Event (4, absorbierend)
```

```python
from medrisk.models.multistate import MultistateModel

msm = MultistateModel()
msm.set_intensities({(0,1): 0.08, (1,2): 0.06, (2,3): 0.04, (3,4): 0.03, ...})

# Aufenthaltswahrscheinlichkeiten ueber Zeit
probs = msm.state_occupation_probabilities(start_state=0, times=np.linspace(0, 30, 200))
```

### 3.5 PBW-Detektor

**Datei:** `src/medrisk/validation/failure_detection.py`

Drei Signale, ein Hard-Flag:

1. **PBW (Hard Flag):** `confidence > 0.80 AND dqs < 0.60` → REJECT
   - Das Modell ist sehr sicher, aber die Daten stuetzen das nicht

2. **CCM (Soft Flag):** `|raw_proba - calibrated_proba| > 0.20`
   - Rohe und kalibrierte Wahrscheinlichkeit weichen stark ab → Modell ist intern inkonsistent

3. **EPU (Soft Flag):** Modell-Disagreement ueber Dezile > 3
   - Verschiedene Modellperspektiven kommen zu verschiedenen Ergebnissen

**Entscheidungslogik:**
- PBW geflaggt → **reject_prediction**
- CCM oder EPU geflaggt → **review**
- Nichts geflaggt → **accept**

### 3.6 SHAP Erklaerbarkeit

**Datei:** `src/medrisk/explain/shap_layer.py`

```python
from medrisk.explain.shap_layer import explain_xgboost, get_top_features

sv = explain_xgboost(clf.model, X_test, feature_names=feature_names)
top = get_top_features(sv, n_top=10)  # Top 10 Features nach |SHAP|
```

Enthaelt SHAP/XGBoost-Kompatibilitaetsfix fuer neuere XGBoost-Versionen (bracketed base_score in UBJSON).

### 3.7 PDF-Report

**Datei:** `src/medrisk/reporting/pdf_report.py`

```python
from medrisk.reporting.pdf_report import generate_report, ReportData

data = ReportData(
    patient_id="...", market="DE", age=62, sex="M",
    dqs=0.85, dqs_tier="adequate",
    risk_probability=0.23, risk_class="moderate",
    validation_recommendation="accept",
    ...
)
generate_report(data, "data/reports/patient_report.pdf")
```

---

## 4. Notebooks

| # | Name | Was es zeigt |
|---|------|-------------|
| 01 | Synthetic Cohort | Datengenerierung, DQS-Verteilung nach Markt |
| 02 | Risk Classification | XGBoost Training, SHAP, Kalibrierung |
| 03 | Disease Progression | Cox PH Survival, CTMC Zustandsuebergaenge |
| 04 | Failure Modes | PBW-Demonstration, Confidence vs. DQS Scatter |
| 05 | Underwriting Report | Komplette Pipeline → PDF fuer sauberen + geflaggten Fall |

---

## 5. Konfiguration

**Datei:** `configs/default.yaml`

Alle Hyperparameter und Schwellenwerte zentral konfiguriert:

```yaml
cohort:
  patients_per_market: 5000
  markets: ["DE", "ES", "FR", "INT"]

validation:
  dqs_weights:
    completeness: 0.40
    consistency: 0.35
    recency: 0.25
  dqs_thresholds:
    adequate: 0.80
    caution: 0.60
  pbw:
    confidence_threshold: 0.80
    dqs_threshold: 0.60
  ccm_threshold: 0.20
  epu_decile_threshold: 3
```

---

## 6. Bekannte Limitierungen

### Technisch
- **Keine echten Daten** — alles synthetisch, Schwellenwerte heuristisch
- **8 ICD-10-CM Codes ungueltig fuer ICD-10-GM** (deutscher Markt)
- **6 Praevalenzraten >50% daneben** vs. publizierte Epidemiologie
- **PBW 0.80-Schwelle triggert nie** bei 1% Event-Rate (Konfidenz erreicht max 0.73)

### Konzeptionell
- DQS-Gewichte (0.40/0.35/0.25) sind Designentscheidungen, nicht empirisch validiert
- Kein realer Validierungsdatensatz (Phase 2 erforderlich)
- Keine EU AI Act Compliance (Phase 3)

---

## 7. Naechste Schritte

### Sofort machbar
1. 8 ICD-10-GM Codes fixen (GM-Layer in `icd10.py`)
2. 6 Praevalenzraten aktualisieren (`synthetic.py`)
3. PBW-Schwelle relativieren (Top-Dezil statt absolut 0.80)
4. Initial Git Commit

### Phase 2 (3-6 Monate)
1. CPRD (UK) — volle DQS-Validierung mit Laborwerten
2. InGef (DE) — Marktkompatibilitaet auf deutschen GKV-Daten
3. DQS-Schwellen via Kosten-Optimierung kalibrieren
4. PBW-Rate gegen echte Schadensverlaeufe validieren

### Phase 3 (12-18 Monate)
1. REST API fuer Echtzeit-Scoring
2. Human-in-the-Loop UI fuer geflaggte Faelle
3. Model Drift Monitoring
4. EU AI Act Compliance (DPIA, Modellkarten, Audit Trail)
