#!/usr/bin/env python3
"""Generate documentation PDFs for MedRisk-ADH."""

from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent.parent / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)


class DocPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(15, 15, 15)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 120, 142)
        self.cell(
            0, 5, "MedRisk-ADH v2.0 | Helmholtz Munich",
            align="R", new_x="LMARGIN", new_y="NEXT",
        )
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Page {self.page_no()} | Tim Reska | March 2026", align="C")

    def cover(self, title, subtitle):
        self.add_page()
        self.ln(40)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(13, 35, 57)
        self.multi_cell(0, 10, title, align="C")
        self.ln(3)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(43, 70, 96)
        self.multi_cell(0, 7, subtitle, align="C")
        self.ln(15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(97, 120, 142)
        self.cell(0, 5, "Tim Reska | Helmholtz Munich | March 2026", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, "Proof of Concept | All data is synthetic", align="C", new_x="LMARGIN", new_y="NEXT")

    def h2(self, text):
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(13, 35, 57)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(16, 122, 202)
        self.line(15, self.get_y(), 55, self.get_y())
        self.ln(3)

    def p(self, text):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(43, 70, 96)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def li(self, text):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(43, 70, 96)
        x = self.get_x()
        self.cell(6, 5, "-")
        self.multi_cell(164, 5, text)


def make_what_we_built():
    pdf = DocPDF()
    pdf.cover("What We Built", "MedRisk-ADH -- Complete Technical Summary")
    pdf.add_page()
    pdf.h2("Project Overview")
    pdf.p("MedRisk-ADH is an AI-driven medical underwriting system with confidence-calibrated failure mode detection. It detects when a prediction is not supported by sufficient input data -- the Plausible-but-Wrong (PBW) problem.")

    pdf.h2("Architecture (v2)")
    pdf.p("Patient Record -> Data Profile -> DQS v2 -> Model Router -> Reliability Head -> Decision + Audit")
    pdf.li("Data Profile: classifies available data (FULL / NO_LABS / NO_MEDS / MINIMAL)")
    pdf.li("DQS v2: completeness + consistency + recency + range checks + missingness classification")
    pdf.li("Model Router: one XGBoost per data profile -- no imputation")
    pdf.li("Reliability Head: P(wrong) with cost-optimal accept/review/reject")
    pdf.li("Governance: JSON Lines audit trail, human override support")

    pdf.h2("v2 Source Modules")
    pdf.li("validation/range_checks.py -- physiological range validation")
    pdf.li("features/data_profile.py -- data availability classification")
    pdf.li("models/model_router.py -- profile-aware model selection")
    pdf.li("validation/reliability_head.py -- learned error probability")
    pdf.li("evaluation/subgroup_eval.py, plots.py -- calibration, DCA")
    pdf.li("governance/audit_log.py, human_override.py -- audit trail")
    pdf.li("validation/shift_detection.py -- PSI/JS divergence")
    pdf.li("pipeline.py -- end-to-end orchestrator")

    pdf.h2("Testing & Quality")
    pdf.p("192 unit tests, all passing. Lint clean (ruff). 5 Jupyter notebooks execute without error.")

    pdf.h2("Demo Applications")
    pdf.li("Streamlit app: Patient Assessment, PBW Comparison, Portfolio Dashboard")
    pdf.li("HTML technical dashboard: index.html (Chart.js)")
    pdf.li("HTML executive overview: executive.html (plain English)")
    pdf.p("Design: Doctolib Oxygen -- light, white, Nunito Sans, #107ACA blue.")

    pdf.h2("Metrics (Synthetic Data)")
    pdf.li("AUC-ROC: 0.71 | Brier: 0.010 | C-index: 0.72")
    pdf.li("4,000 patients, 4 European markets")
    pdf.li("INT market: 2-3x higher P(wrong) than DE")

    pdf.output(str(OUT / "what_we_built.pdf"))
    print("what_we_built.pdf")


def make_app_guide():
    pdf = DocPDF()
    pdf.cover("Application Guide", "How to Use the MedRisk-ADH Demo")
    pdf.add_page()
    pdf.h2("Starting the App")
    pdf.p("Streamlit: make app (or streamlit run app/app.py) -> http://localhost:8501")
    pdf.p("HTML: open app/static/index.html or executive.html in any browser")

    pdf.h2("Page 1: Patient Assessment")
    pdf.li("Select market + patient from sidebar")
    pdf.li("DQS Gauge with tier (adequate / caution / insufficient)")
    pdf.li("Component bars: completeness, consistency, recency, range score")
    pdf.li("Decision card: risk score, P(wrong), model, recommendation")
    pdf.li("Feature importance + disease progression charts")
    pdf.li("Expandable audit entry (JSON)")

    pdf.h2("Page 2: PBW Comparison")
    pdf.p("Side-by-side: best German patient vs worst International patient.")
    pdf.li("Both show DQS, risk score, P(wrong), decision")
    pdf.li("Sliders to browse patients by data quality rank")
    pdf.p("Narrative: Same risk score, different reliability.")

    pdf.h2("Page 3: Portfolio Dashboard")
    pdf.li("KPI cards: AUC, Brier, accept rate, review+reject rate")
    pdf.li("DQS by market, decision breakdown, confidence vs DQS scatter")
    pdf.li("P(wrong) distribution, reliability coefficients, market table")

    pdf.h2("Executive Overview")
    pdf.p("app/static/executive.html -- plain English, no jargon. Problem -> solution -> demo -> results -> implications.")

    pdf.output(str(OUT / "app_guide.pdf"))
    print("app_guide.pdf")


def make_data_requirements():
    pdf = DocPDF()
    pdf.cover("Data Requirements", "What MedRisk-ADH Needs for Phase 2 Validation")
    pdf.add_page()
    pdf.h2("Minimum Requirements")
    pdf.li("50,000+ patient records, 5+ years follow-up")
    pdf.li("Linked outcomes (claims, hospitalisations, mortality)")
    pdf.li("At least 2 markets/sites with different data quality")

    pdf.h2("Demographics")
    pdf.li("Patient ID (pseudonymised), age, sex, BMI, smoking status")

    pdf.h2("Diagnoses")
    pdf.li("ICD-10-GM coded with date. Primary/secondary flag.")
    pdf.li("Cardiovascular, diabetes, renal, respiratory, neoplasm categories")

    pdf.h2("Laboratory Results")
    pdf.li("HbA1c, creatinine, eGFR, cholesterol, HDL, LDL, triglycerides")
    pdf.li("Systolic/diastolic BP, NT-proBNP")
    pdf.li("Each with: value, unit, date_collected, reference range")
    pdf.p("NOTE: German GKV claims do NOT include lab values. Only CPRD (UK) and PKV insurer data have labs.")

    pdf.h2("Medications")
    pdf.li("ATC-coded prescriptions with date and active status")

    pdf.h2("Outcomes")
    pdf.li("Event type (death, MI, stroke, HF, CKD), time to event, censoring indicator")
    pdf.li("Claims cost data if available")

    pdf.h2("Recommended Sources")
    pdf.li("1. CPRD (UK) -- only source with labs. 60M patients. 2-4 months.")
    pdf.li("2. InGef (DE) -- 8.8M GKV. German ICD-10-GM. No labs. 3-6 months.")
    pdf.li("3. CMBD (Spain) -- hospital only. Free. 2-4 months.")
    pdf.li("4. Insurer Internal -- target. Requires partnership + DPO.")

    pdf.h2("Legal Basis")
    pdf.li("Germany: SGB X Section 75 + DSGVO Art. 89")
    pdf.li("UK: UK GDPR + NHS Act 2006 Section 251")
    pdf.li("Insurer: DSGVO Art. 6(1)(f) + Art. 35 DPIA")

    pdf.h2("Data Format")
    pdf.p("CSV/Parquet, one row per patient. We provide a loader for our PatientRecord schema.")

    pdf.output(str(OUT / "data_requirements.pdf"))
    print("data_requirements.pdf")


if __name__ == "__main__":
    make_what_we_built()
    make_app_guide()
    make_data_requirements()
    print(f"All 3 PDFs at {OUT}/")
