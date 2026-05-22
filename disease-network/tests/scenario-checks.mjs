import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { createDataContext } from "../assets/js/data.mjs";
import {
  buildScenarioBundle,
  deriveNetworkModel,
  deriveTimelineModel,
  pickIncidenceRows
} from "../assets/js/model.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const raw = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "diseases.json"), "utf8"));
const context = createDataContext(raw);

const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

function scenario(patient, activeInterventions = [], seed = 11) {
  return buildScenarioBundle(context, patient, activeInterventions, {
    seed,
    samples: 180
  });
}

for (const disease of context.diseases) {
  if (disease.stages.length < 2) continue;
  const patient = {
    ...context.meta.default_patient,
    primary_disease: disease.id
  };
  const early = scenario({ ...patient, stage: disease.stages[0].id }, [], 17);
  const late = scenario({ ...patient, stage: disease.stages[disease.stages.length - 1].id }, [], 23);
  assert(
    late.summary.mortality10 >= early.summary.mortality10,
    `${disease.id}: spaetere Stage hat keine hoehere 10-Jahres-Mortalitaet`
  );
}

const t2dBaseline = scenario(
  {
    ...context.meta.default_patient,
    primary_disease: "diabetes_t2",
    stage: "t2d_uncontrolled",
    hba1c: 8.8,
    albuminuria_acr: 110
  },
  [],
  31
);
const t2dImproved = scenario(
  {
    ...context.meta.default_patient,
    primary_disease: "diabetes_t2",
    stage: "t2d_uncontrolled",
    hba1c: 8.8,
    albuminuria_acr: 110
  },
  ["glucose_control", "renal_protection"],
  31
);
assert(
  t2dImproved.summary.mortality10 <= t2dBaseline.summary.mortality10,
  "T2D-Intervention verschlechtert die 10-Jahres-Mortalitaet"
);

const htnBaseline = scenario(
  {
    ...context.meta.default_patient,
    primary_disease: "hypertension",
    stage: "htn_grade2_uncontrolled",
    systolic_bp: 172
  },
  [],
  41
);
const htnImproved = scenario(
  {
    ...context.meta.default_patient,
    primary_disease: "hypertension",
    stage: "htn_grade2_uncontrolled",
    systolic_bp: 172
  },
  ["bp_control", "smoking_cessation"],
  41
);
assert(
  htnImproved.summary.mortality10 <= htnBaseline.summary.mortality10,
  "BP-Kontrolle verschlechtert Hypertonie-Szenario"
);

const depressionMild = scenario(
  {
    ...context.meta.default_patient,
    primary_disease: "depression",
    stage: "depression_subclinical",
    phq9: 6
  },
  [],
  51
);
const depressionSevere = scenario(
  {
    ...context.meta.default_patient,
    primary_disease: "depression",
    stage: "depression_severe_recurrent",
    phq9: 19
  },
  [],
  51
);
const severeTop = depressionSevere.simulation.topFutureDiseases.find((entry) => entry.id === "cvd_khk");
const mildTop = depressionMild.simulation.topFutureDiseases.find((entry) => entry.id === "cvd_khk");
assert(
  (severeTop?.probability10 || 0) >= (mildTop?.probability10 || 0),
  "Schwere Depression verstaerkt die CVD-Bruecke nicht"
);

const survival = t2dBaseline.simulation.survival;
for (let index = 1; index < survival.length; index += 1) {
  assert(survival[index] <= survival[index - 1] + 1e-9, "Survival-Kurve steigt im Verlauf an");
}

const incidenceRows = pickIncidenceRows(context, t2dBaseline, t2dImproved);
assert(incidenceRows.length <= 5, "pickIncidenceRows liefert mehr als 5 Zeilen");
assert(
  incidenceRows.every(
    (row) =>
      typeof row.label === "string" &&
      Number.isFinite(row.baseline) &&
      Number.isFinite(row.intervention)
  ),
  "pickIncidenceRows-Zeile hat kein Label oder keine endlichen Wahrscheinlichkeiten"
);
for (let index = 1; index < incidenceRows.length; index += 1) {
  const previous = Math.max(incidenceRows[index - 1].baseline, incidenceRows[index - 1].intervention);
  const current = Math.max(incidenceRows[index].baseline, incidenceRows[index].intervention);
  assert(
    current <= previous + 1e-9,
    "pickIncidenceRows ist nicht absteigend nach max(Baseline, Intervention) sortiert"
  );
}

const syncPatient = {
  ...context.meta.default_patient,
  primary_disease: "diabetes_t2",
  stage: "t2d_uncontrolled"
};
const timeline = deriveTimelineModel(context, syncPatient);
const network = deriveNetworkModel(context, syncPatient, {
  search: "",
  cluster: "all",
  modifiableOnly: false,
  fromCurrentStageOnly: true,
  pinnedDiseaseId: null
});
assert(
  timeline.lanes[0].currentStageId === syncPatient.stage,
  "Timeline verwendet nicht die aktuelle gemeinsame Stage"
);
assert(
  network.edges.some((edge) => edge.source === syncPatient.primary_disease && edge.relevance === 2),
  "Network markiert keine patientennahe Relevanz fuer die aktuelle Primordiagnose"
);

if (failures.length) {
  console.error("SCENARIO CHECKS FAILED");
  failures.forEach((message) => console.error(`- ${message}`));
  process.exit(1);
}

console.log("SCENARIO CHECKS PASSED");
