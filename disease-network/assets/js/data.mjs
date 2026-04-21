const DATA_URL = new URL("../../diseases.json", import.meta.url);

export async function loadDiseaseData() {
  const response = await fetch(DATA_URL);
  if (!response.ok) {
    throw new Error(`Konnte diseases.json nicht laden (${response.status})`);
  }
  const raw = await response.json();
  return createDataContext(raw);
}

export function createDataContext(raw) {
  const diseasesById = new Map(raw.diseases.map((disease) => [disease.id, disease]));
  const citationsById = new Map(raw.citations.map((citation) => [citation.id, citation]));
  const interventionsById = new Map(raw.meta.interventions.map((entry) => [entry.id, entry]));
  const stagesById = new Map();
  const edgesById = new Map();

  raw.diseases.forEach((disease) => {
    disease.stages.forEach((stage, index) => {
      stagesById.set(stage.id, { ...stage, disease_id: disease.id, stage_index: index });
    });
    (disease.outgoing_edges || []).forEach((edge) => {
      edgesById.set(edge.id, { ...edge, source: disease.id });
    });
  });

  return {
    raw,
    meta: raw.meta,
    diseases: raw.diseases,
    diseasesById,
    citations: raw.citations,
    citationsById,
    interventions: raw.meta.interventions,
    interventionsById,
    stagesById,
    edgesById
  };
}

export function getDefaultPatient(context) {
  return structuredClone(context.meta.default_patient);
}

export function getDisease(context, diseaseId) {
  return context.diseasesById.get(diseaseId);
}

export function getStage(disease, stageId) {
  return disease.stages.find((stage) => stage.id === stageId);
}

export function getStageIndex(disease, stageId) {
  return disease.stages.findIndex((stage) => stage.id === stageId);
}

export function firstStageId(disease) {
  return disease.stages[0]?.id;
}

export function getAllEdges(context) {
  return context.diseases.flatMap((disease) =>
    (disease.outgoing_edges || []).map((edge) => ({ ...edge, source: disease.id }))
  );
}

export function getCitationBundle(context, citationIds = []) {
  return citationIds
    .map((citationId) => context.citationsById.get(citationId))
    .filter(Boolean);
}

export function getIntervention(context, interventionId) {
  return context.interventionsById.get(interventionId);
}

export function normalizePatient(context, patientLike) {
  const normalized = { ...getDefaultPatient(context), ...patientLike };
  [
    "age",
    "bmi",
    "systolic_bp",
    "hba1c",
    "egfr",
    "ldl",
    "albuminuria_acr",
    "phq9"
  ].forEach((field) => {
    normalized[field] = Number(normalized[field]);
  });
  normalized.age = Math.round(normalized.age);
  return normalized;
}

export function getInputConfig(context, inputKey) {
  return context.meta.input_schema[inputKey];
}

export function getClusterMeta(context, clusterKey) {
  return context.meta.clusters[clusterKey];
}
