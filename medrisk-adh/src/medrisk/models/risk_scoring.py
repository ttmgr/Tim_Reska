"""Risk scoring models: Charlson Comorbidity Index, Elixhauser Score, and combined MRS.

The Charlson index computation is delegated to
``medrisk.data.charlson.compute_charlson_index`` which implements the
Quan-adapted ICD-10 mapping with hierarchy rules.

References:
  - Charlson ME et al. (1987). J Chronic Dis 40(5):373-383.
  - Quan H et al. (2011). Med Care 49(6):625-633. (ICD-10 adaptation)
  - van Walraven C et al. (2009). Med Care 47(6):626-633. (Elixhauser weights)
  - Charlson survival: S10 = 0.983 ^ exp(CCI * 0.9)  [Charlson 1987]
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from medrisk.data.charlson import compute_charlson_index

# ---------------------------------------------------------------------------
# Charlson wrapper (delegates to medrisk.data.charlson)
# ---------------------------------------------------------------------------


class CharlsonIndex:
    """Charlson Comorbidity Index (ICD-10 Quan adaptation).

    Each condition group contributes its weight at most once.
    Mutually exclusive pairs: only the higher-weight condition is counted.

    Survival at 10 years:
        S10 = 0.983 ^ exp(CCI * 0.9)   [Charlson 1987]
    """

    def score(self, icd10_codes: list[str]) -> int:
        """Compute CCI from a list of ICD-10 codes."""
        return compute_charlson_index(icd10_codes)

    def survival_10yr(self, cci: int) -> float:
        """Estimated 10-year survival probability using Charlson's original formula.

        S10 = 0.983 ^ exp(CCI * 0.9)
        """
        return 0.983 ** math.exp(cci * 0.9)


# ---------------------------------------------------------------------------
# Elixhauser Score (van Walraven 2009 weights)
# ---------------------------------------------------------------------------

# 31 Elixhauser conditions with van Walraven additive weights
_ELIXHAUSER_CONDITIONS: dict[str, tuple[int, list[str]]] = {
    "chf": (
        7,
        [
            "I099",
            "I110",
            "I130",
            "I132",
            "I255",
            "I420",
            "I425",
            "I426",
            "I427",
            "I428",
            "I429",
            "I43",
            "I50",
            "P290",
        ],
    ),
    "arrhythmia": (
        5,
        [
            "I441",
            "I442",
            "I443",
            "I456",
            "I459",
            "I47",
            "I48",
            "I49",
            "R000",
            "R001",
            "R008",
            "T821",
            "Z450",
            "Z950",
        ],
    ),
    "valvular": (
        -1,
        [
            "A520",
            "I05",
            "I06",
            "I07",
            "I08",
            "I091",
            "I098",
            "I34",
            "I35",
            "I36",
            "I37",
            "I38",
            "I39",
            "Q230",
            "Q231",
            "Q232",
            "Q233",
            "Z952",
            "Z953",
            "Z954",
        ],
    ),
    "pulm_circ": (4, ["I26", "I27", "I280", "I288", "I289"]),
    "pvd": (
        2,
        [
            "I70",
            "I71",
            "I731",
            "I738",
            "I739",
            "I771",
            "I790",
            "I792",
            "K551",
            "K558",
            "K559",
            "Z958",
            "Z959",
        ],
    ),
    "hypertension_unc": (-1, ["I10"]),
    "hypertension_com": (0, ["I11", "I12", "I13", "I15"]),
    "paralysis": (
        7,
        [
            "G041",
            "G114",
            "G801",
            "G802",
            "G81",
            "G82",
            "G830",
            "G831",
            "G832",
            "G833",
            "G834",
            "G839",
        ],
    ),
    "other_neuro": (
        6,
        [
            "G10",
            "G11",
            "G12",
            "G13",
            "G20",
            "G21",
            "G22",
            "G254",
            "G255",
            "G312",
            "G318",
            "G319",
            "G32",
            "G35",
            "G36",
            "G37",
            "G40",
            "G41",
            "G931",
            "G934",
            "R470",
            "R56",
        ],
    ),
    "copd": (
        3,
        [
            "J40",
            "J41",
            "J42",
            "J43",
            "J44",
            "J45",
            "J46",
            "J47",
            "J60",
            "J61",
            "J62",
            "J63",
            "J64",
            "J65",
            "J66",
            "J67",
            "I278",
            "I279",
            "J684",
            "J701",
            "J703",
        ],
    ),
    "diabetes_unc": (
        0,
        [
            "E100",
            "E101",
            "E109",
            "E110",
            "E111",
            "E119",
            "E120",
            "E121",
            "E129",
            "E130",
            "E131",
            "E139",
            "E140",
            "E141",
            "E149",
        ],
    ),
    "diabetes_com": (
        -3,
        [
            "E102",
            "E103",
            "E104",
            "E105",
            "E106",
            "E107",
            "E108",
            "E112",
            "E113",
            "E114",
            "E115",
            "E116",
            "E117",
            "E118",
            "E122",
            "E123",
            "E124",
            "E125",
            "E126",
            "E127",
            "E128",
            "E132",
            "E133",
            "E134",
            "E135",
            "E136",
            "E137",
            "E138",
            "E142",
            "E143",
            "E144",
            "E145",
            "E146",
            "E147",
            "E148",
        ],
    ),
    "hypothyroidism": (0, ["E00", "E01", "E02", "E03", "E890"]),
    "renal_failure": (
        5,
        ["I120", "I131", "N18", "N19", "N250", "Z490", "Z491", "Z492", "Z940", "Z992"],
    ),
    "liver_disease": (
        11,
        [
            "B18",
            "I85",
            "I864",
            "I982",
            "K70",
            "K711",
            "K713",
            "K714",
            "K715",
            "K717",
            "K72",
            "K73",
            "K74",
            "K760",
            "K762",
            "K763",
            "K764",
            "K765",
            "K766",
            "K767",
            "K768",
            "K769",
            "Z944",
        ],
    ),
    "pud": (0, ["K25", "K26", "K27", "K28"]),
    "hiv": (0, ["B20", "B21", "B22", "B24"]),
    "lymphoma": (9, ["C81", "C82", "C83", "C84", "C85", "C88", "C96", "C900", "C902"]),
    "metastatic": (12, ["C77", "C78", "C79", "C80"]),
    "solid_tumour": (
        4,
        [
            "C0",
            "C1",
            "C2",
            "C3",
            "C4",
            "C5",
            "C6",
            "C70",
            "C71",
            "C72",
            "C73",
            "C74",
            "C75",
            "C76",
            "C97",
        ],
    ),
    "rheumatoid": (
        0,
        [
            "L940",
            "L941",
            "L943",
            "M05",
            "M06",
            "M08",
            "M120",
            "M123",
            "M30",
            "M310",
            "M311",
            "M312",
            "M313",
            "M32",
            "M33",
            "M34",
            "M35",
            "M45",
            "M461",
            "M468",
            "M469",
        ],
    ),
    "coagulopathy": (3, ["D65", "D66", "D67", "D68", "D691", "D693", "D694", "D695", "D696"]),
    "obesity": (-4, ["E66"]),
    "weight_loss": (6, ["E40", "E41", "E42", "E43", "E44", "E45", "E46", "R634", "R64"]),
    "fluid_electrolyte": (5, ["E222", "E86", "E87"]),
    "blood_loss_anemia": (-2, ["D500"]),
    "deficiency_anemia": (-2, ["D508", "D509", "D51", "D52", "D53"]),
    "alcohol": (
        0,
        [
            "F10",
            "E52",
            "G621",
            "I426",
            "K292",
            "K700",
            "K703",
            "K709",
            "T51",
            "Z502",
            "Z714",
            "Z721",
        ],
    ),
    "drug_abuse": (-7, ["F11", "F12", "F13", "F14", "F15", "F16", "F18", "F19", "Z715", "Z722"]),
    "psychosis": (0, ["F20", "F22", "F23", "F24", "F25", "F28", "F29", "F302", "F312", "F315"]),
    "depression": (-3, ["F204", "F313", "F314", "F315", "F32", "F33", "F341", "F412", "F432"]),
}


class ElixhauserScore:
    """Elixhauser comorbidity score with van Walraven additive weights (2009).

    Returns the sum of weights for all present conditions.
    Higher scores -> higher 30-day in-hospital mortality risk.
    """

    def score(self, icd10_codes: list[str]) -> int:
        """Compute van Walraven Elixhauser score from ICD-10 codes."""
        normalised = {c.strip().upper().replace(".", "") for c in icd10_codes}
        total = 0
        for _condition, (weight, prefixes) in _ELIXHAUSER_CONDITIONS.items():
            for prefix in prefixes:
                if any(c.startswith(prefix) for c in normalised):
                    total += weight
                    break
        return total


# ---------------------------------------------------------------------------
# Morbidity Risk Scorer -- combines CCI, age/sex, and occupational class
# ---------------------------------------------------------------------------

# Age/sex relative risk multipliers (approximate, calibrated to GKV data)
_AGE_SEX_RR: dict[tuple[str, int], float] = {
    # (sex, age_band_lower): RR relative to 35-year-old male baseline
    # Age bands correspond to GKV reference table mid-points
    ("M", 15): 0.80,
    ("M", 25): 0.90,
    ("M", 35): 1.00,
    ("M", 45): 1.20,
    ("M", 55): 1.45,
    ("M", 65): 1.70,
    ("F", 15): 0.85,
    ("F", 25): 1.00,
    ("F", 35): 1.10,
    ("F", 45): 1.25,
    ("F", 55): 1.40,
    ("F", 65): 1.60,
}

# Valid age bands in _AGE_SEX_RR (sorted)
_AGE_BANDS = [15, 25, 35, 45, 55, 65]

# CCI -> RR multiplier (log-linear, consistent with Charlson 1987)
_CCI_RR = {0: 1.00, 1: 1.30, 2: 1.60, 3: 1.95, 4: 2.40, 5: 2.90, 6: 3.50}

# Occupational class -> sick-leave frequency multiplier
_OCC_RR = {1: 1.00, 2: 1.25, 3: 1.60, 4: 2.10}


@dataclass
class MorbidityRiskScorer:
    """Combined relative risk from comorbidity, age/sex, and occupation.

    RR_total = RR_cci * RR_age_sex * RR_occ

    Used as an adjustment factor in NegBinomFrequencyModel and
    WeibullDurationModel.
    """

    charlson: CharlsonIndex = field(default_factory=CharlsonIndex)

    def _age_band(self, age: int) -> int:
        """Return nearest GKV reference age band (15, 25, 35, 45, 55, 65)."""
        age_clamped = max(_AGE_BANDS[0], min(_AGE_BANDS[-1], age))
        return min(_AGE_BANDS, key=lambda a: abs(a - age_clamped))

    def age_sex_rr(self, age: int, sex: str) -> float:
        """Relative risk from age and sex."""
        sex_key = sex.upper()[:1]
        if sex_key not in ("M", "F"):
            sex_key = "M"
        band = self._age_band(age)
        return _AGE_SEX_RR.get((sex_key, band), 1.00)

    def cci_rr(self, cci: int) -> float:
        """Relative risk from Charlson score."""
        return _CCI_RR.get(min(cci, 6), 3.50 * (1.20 ** (cci - 6)))

    def occ_rr(self, occ_class: int) -> float:
        """Relative risk from occupational class (1-4)."""
        return _OCC_RR.get(occ_class, 1.00)

    def relative_risk(
        self,
        icd10_codes: list[str],
        age: int,
        sex: str,
        occ_class: int = 1,
    ) -> float:
        """Multiplicative relative risk combining CCI, age/sex, and occupation.

        Args:
            icd10_codes: Patient's ICD-10 diagnosis codes.
            age: Current age in years.
            sex: "M" or "F".
            occ_class: Occupational risk class 1-4.

        Returns:
            Combined relative risk (>= 1.00).
        """
        cci = self.charlson.score(icd10_codes)
        return self.cci_rr(cci) * self.age_sex_rr(age, sex) * self.occ_rr(occ_class)
