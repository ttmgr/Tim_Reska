import {
  getAllEdges,
  getCitationBundle,
  getDisease,
  getIntervention,
  getStage,
  getStageIndex
} from "./data.mjs";

export const COST_SCORE = {
  low: 1,
  medium: 2,
  high: 3,
  very_high: 4
};

export const COST_LABEL = {
  0: "minimal",
  1: "niedrig",
  2: "mittel",
  3: "hoch",
  4: "sehr hoch"
};

const CONFIDENCE_WEIGHT = {
  high: 3,
  moderate: 2,
  low: 1
};

export function confidenceToLabel(value) {
  if (value === "high") return "hoch";
  if (value === "moderate") return "moderat";
  return "niedrig";
}

export function signalFromMortality(mortality) {
  if (mortality >= 0.28) {
    return { key: "red", label: "deutlich erhoeht" };
  }
  if (mortality >= 0.14) {
    return { key: "amber", label: "erhoeht" };
  }
  return { key: "green", label: "kontrollierbar" };
}

export function buildInterventionPatient(context, baselinePatient, activeInterventionIds = []) {
  const patient = structuredClone(baselinePatient);

  activeInterventionIds.forEach((interventionId) => {
    const intervention = getIntervention(context, interventionId);
    if (!intervention) return;
    intervention.patient_rules.forEach((rule) => {
      const currentValue = patient[rule.field];
      if (rule.mode === "set") {
        patient[rule.field] = rule.value;
      } else if (rule.mode === "set_if_lower") {
        patient[rule.field] = Math.min(Number(currentValue), Number(rule.value));
      } else if (rule.mode === "delta") {
        let nextValue = Number(currentValue) + Number(rule.value);
        if (rule.floor != null) nextValue = Math.max(nextValue, Number(rule.floor));
        if (rule.ceiling != null) nextValue = Math.min(nextValue, Number(rule.ceiling));
        patient[rule.field] = nextValue;
      } else if (rule.mode === "scale") {
        let nextValue = Number(currentValue) * Number(rule.value);
        if (rule.floor != null) nextValue = Math.max(nextValue, Number(rule.floor));
        if (rule.ceiling != null) nextValue = Math.min(nextValue, Number(rule.ceiling));
        patient[rule.field] = nextValue;
      }
    });
  });

  patient.age = Math.round(patient.age);
  return patient;
}

export function computeStageSuggestion(context, patient) {
  const disease = getDisease(context, patient.primary_disease);
  const currentStage = getStage(disease, patient.stage);
  const stageScores = disease.stages.map((stage) => ({
    stage,
    score: stageMatchScore(stage, patient),
    reasons: stageMatchReasons(stage, patient)
  }));
  stageScores.sort((left, right) => {
    if (right.score !== left.score) return right.score - left.score;
    return left.stage.severity_rank - right.stage.severity_rank;
  });

  const suggested = stageScores[0];
  return {
    disease,
    currentStage,
    suggestedStage: suggested.stage,
    suggestedScore: suggested.score,
    currentScore: currentStage ? stageMatchScore(currentStage, patient) : 0,
    reasons: suggested.reasons
  };
}

function stageMatchScore(stage, patient) {
  if (!stage.biomarker_rules?.length) return 0;
  const matches = stage.biomarker_rules.map((rule) => Number(ruleMatchesPatient(rule, patient)));
  const meanMatch = matches.reduce((sum, value) => sum + value, 0) / matches.length;
  return meanMatch + stage.severity_rank * 0.01;
}

function stageMatchReasons(stage, patient) {
  return (stage.biomarker_rules || []).map((rule) => {
    const hit = ruleMatchesPatient(rule, patient);
    return {
      label: rule.label,
      note: rule.note,
      hit,
      patientValue: formatRuleValue(patient[rule.marker], rule.unit)
    };
  });
}

function ruleMatchesPatient(rule, patient) {
  const value = patient[rule.marker];
  if (rule.operator === "range") {
    return value >= Number(rule.value[0]) && value <= Number(rule.value[1]);
  }
  if (rule.operator === ">=") return value >= Number(rule.value);
  if (rule.operator === "<=") return value <= Number(rule.value);
  if (rule.operator === "<") return value < Number(rule.value);
  if (rule.operator === "=") return value === rule.value;
  if (rule.operator === "in") return Array.isArray(rule.value) && rule.value.includes(value);
  return false;
}

function formatRuleValue(value, unit = "") {
  if (typeof value === "number") {
    return `${Number.isInteger(value) ? value : value.toFixed(1)}${unit ? ` ${unit}` : ""}`;
  }
  return `${value}${unit ? ` ${unit}` : ""}`;
}

export function buildScenarioBundle(context, patient, activeInterventionIds = [], options = {}) {
  const scenarioPatient = buildInterventionPatient(context, patient, activeInterventionIds);
  const disease = getDisease(context, scenarioPatient.primary_disease);
  const stage = getStage(disease, scenarioPatient.stage);
  const stageIndex = getStageIndex(disease, scenarioPatient.stage);
  const riskDrivers = computeRiskDrivers(context, scenarioPatient, stage, activeInterventionIds);
  const simulation = simulateTrajectory(context, scenarioPatient, activeInterventionIds, options);
  const confidence = deriveScenarioConfidence(disease, stage, simulation.topFutureDiseases);
  const signal = signalFromMortality(simulation.mortality10);

  return {
    patient: scenarioPatient,
    disease,
    stage,
    stageIndex,
    activeInterventionIds,
    confidence,
    signal,
    riskDrivers,
    simulation,
    summary: {
      mortality10: simulation.mortality10,
      mortality10Interval: simulation.mortality10Interval,
      currentAnnualMortality: computeCurrentAnnualMortality(context, scenarioPatient, stage, activeInterventionIds),
      medianSurvival: simulation.medianSurvival,
      topFutureDisease: simulation.topFutureDiseases[0] || null,
      topFutureDiseases: simulation.topFutureDiseases
    },
    comparisonRows: buildComparisonRows(patient, scenarioPatient),
    narrative: buildScenarioNarrative(disease, stage, signal, confidence, riskDrivers, simulation)
  };
}

function buildScenarioNarrative(disease, stage, signal, confidence, riskDrivers, simulation) {
  const leadDriver = riskDrivers[0];
  const topFuture = simulation.topFutureDiseases[0];
  return {
    intro: `${disease.label} in Stage "${stage.label}" liefert aktuell ein ${signal.label}es Underwriting-Signal mit ${confidenceToLabel(confidence)}er Evidenzdichte.`,
    driver: leadDriver
      ? `${leadDriver.label} wirkt derzeit als staerkster Hazard-Verstaerker.`
      : "Aktuell dominiert der Stage-Status selbst das Risikoprofil.",
    future: topFuture
      ? `Die naechste wahrscheinliche Folgeerkrankung ist ${topFuture.label} mit etwa ${Math.round(topFuture.probability10 * 100)}% Modellwahrscheinlichkeit nach 10 Jahren.`
      : "Im aktuellen Zeithorizont zeigt das Modell keine dominante neue Folgediagnose."
  };
}

function deriveScenarioConfidence(disease, stage, topFutureDiseases) {
  const values = [
    CONFIDENCE_WEIGHT[disease.confidence] || 1,
    CONFIDENCE_WEIGHT[stage.confidence] || 1
  ];
  topFutureDiseases.slice(0, 2).forEach((entry) => {
    values.push(CONFIDENCE_WEIGHT[entry.confidence] || 1);
  });
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  if (avg >= 2.5) return "high";
  if (avg >= 1.75) return "moderate";
  return "low";
}

function computeCurrentAnnualMortality(context, patient, stage, activeInterventionIds) {
  const baseQx = getBaselineMortality(context, patient.age, patient.sex);
  const currentHazardFactor = Math.exp(computeLogHazard(context, patient, [{ disease_id: patient.primary_disease, stage }], activeInterventionIds));
  const baseHazard = -Math.log(Math.max(1e-9, 1 - baseQx));
  return 1 - Math.exp(-baseHazard * currentHazardFactor);
}

export function computeRiskDrivers(context, patient, stage, activeInterventionIds = []) {
  const drivers = [];

  drivers.push({
    id: stage.id,
    label: `Stage: ${stage.label}`,
    value: stage.mortality_hr,
    valueLabel: `HR ${stage.mortality_hr.toFixed(2)}`,
    logHazard: Math.log(stage.mortality_hr),
    kind: "stage"
  });

  biomarkerDriverEntries(patient).forEach((driver) => {
    if (driver.logHazard > 0.001) drivers.push(driver);
  });

  activeInterventionIds.forEach((interventionId) => {
    const intervention = getIntervention(context, interventionId);
    if (!intervention) return;
    const stageEffect = (stage.intervention_effects || []).find((effect) => effect.intervention_id === interventionId);
    if (stageEffect?.hazard_multiplier && stageEffect.hazard_multiplier < 1) {
      drivers.push({
        id: interventionId,
        label: `Intervention: ${intervention.label}`,
        value: stageEffect.hazard_multiplier,
        valueLabel: `${Math.round((1 - stageEffect.hazard_multiplier) * 100)}% Hazard-Entlastung`,
        logHazard: Math.log(stageEffect.hazard_multiplier),
        kind: "intervention"
      });
    }
  });

  return drivers.sort((left, right) => Math.abs(right.logHazard) - Math.abs(left.logHazard));
}

function biomarkerDriverEntries(patient) {
  const entries = [];

  if (patient.smoking_status === "active") {
    entries.push({ id: "smoking", label: "Aktives Rauchen", value: patient.smoking_status, valueLabel: "aktiv", logHazard: 0.28, kind: "biomarker" });
  } else if (patient.smoking_status === "former") {
    entries.push({ id: "smoking", label: "Frueheres Rauchen", value: patient.smoking_status, valueLabel: "Ex-Raucher:in", logHazard: 0.08, kind: "biomarker" });
  }

  if (patient.bmi > 25) {
    const logHazard = clamp((patient.bmi - 25) * 0.018, 0, 0.24);
    entries.push({ id: "bmi", label: "BMI ueber Ziel", value: patient.bmi, valueLabel: `${patient.bmi.toFixed(1)} kg/m2`, logHazard, kind: "biomarker" });
  }

  if (patient.systolic_bp > 120) {
    const logHazard = clamp((patient.systolic_bp - 120) * 0.0048, 0, 0.30);
    entries.push({ id: "sbp", label: "Erhoehter SBP", value: patient.systolic_bp, valueLabel: `${patient.systolic_bp.toFixed(0)} mmHg`, logHazard, kind: "biomarker" });
  }

  if (patient.hba1c > 5.7) {
    const logHazard = clamp((patient.hba1c - 5.7) * 0.12, 0, 0.34);
    entries.push({ id: "hba1c", label: "Hyperglykaemie", value: patient.hba1c, valueLabel: `${patient.hba1c.toFixed(1)}%`, logHazard, kind: "biomarker" });
  }

  if (patient.egfr < 90) {
    const logHazard = patient.egfr < 60
      ? clamp((90 - patient.egfr) * 0.007, 0, 0.32)
      : clamp((90 - patient.egfr) * 0.003, 0, 0.09);
    entries.push({ id: "egfr", label: "Reduzierte Nierenfunktion", value: patient.egfr, valueLabel: `${patient.egfr.toFixed(0)} mL/min/1.73m2`, logHazard, kind: "biomarker" });
  }

  if (patient.ldl > 100) {
    const logHazard = clamp((patient.ldl - 100) * 0.0022, 0, 0.20);
    entries.push({ id: "ldl", label: "LDL oberhalb Ziel", value: patient.ldl, valueLabel: `${patient.ldl.toFixed(0)} mg/dL`, logHazard, kind: "biomarker" });
  }

  if (patient.albuminuria_acr >= 30) {
    const logHazard = clamp(Math.log(patient.albuminuria_acr / 30 + 1) * 0.16, 0, 0.24);
    entries.push({ id: "acr", label: "Albuminurie", value: patient.albuminuria_acr, valueLabel: `${patient.albuminuria_acr.toFixed(0)} mg/g`, logHazard, kind: "biomarker" });
  }

  if (patient.phq9 >= 5) {
    const logHazard = clamp((patient.phq9 - 5) * 0.013, 0, 0.18);
    entries.push({ id: "phq9", label: "Psychische Belastung", value: patient.phq9, valueLabel: `PHQ-9 ${patient.phq9}`, logHazard, kind: "biomarker" });
  }

  return entries;
}

function buildComparisonRows(baselinePatient, scenarioPatient) {
  const definitions = [
    ["smoking_status", "Rauchstatus", "", formatSmoking],
    ["bmi", "BMI", "kg/m2", formatNumber],
    ["systolic_bp", "SBP", "mmHg", formatNumber],
    ["hba1c", "HbA1c", "%", formatNumber],
    ["egfr", "eGFR", "mL/min/1.73m2", formatNumber],
    ["ldl", "LDL", "mg/dL", formatNumber],
    ["albuminuria_acr", "Albuminurie ACR", "mg/g", formatNumber],
    ["phq9", "PHQ-9", "", formatNumber]
  ];

  return definitions.map(([field, label, unit, formatter]) => ({
    field,
    label,
    unit,
    baseline: formatter(baselinePatient[field], unit),
    intervention: formatter(scenarioPatient[field], unit),
    changed: baselinePatient[field] !== scenarioPatient[field]
  }));
}

function formatSmoking(value) {
  if (value === "active") return "Aktiv";
  if (value === "former") return "Ex";
  return "Nie";
}

function formatNumber(value, unit) {
  if (typeof value !== "number") return value;
  const rendered = Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1);
  return unit ? `${rendered} ${unit}` : rendered;
}

export function deriveTimelineModel(context, patient) {
  const primary = getDisease(context, patient.primary_disease);
  const primaryIndex = getStageIndex(primary, patient.stage);
  const primaryEdges = (primary.outgoing_edges || []).slice().sort((left, right) => right.annual_incidence_prob - left.annual_incidence_prob);

  const lanes = [
    {
      disease: primary,
      role: "primary",
      relationScore: 1,
      relationLabel: "Primordiagnose",
      currentStageId: patient.stage,
      stages: primary.stages
    }
  ];

  context.diseases
    .filter((candidate) => candidate.id !== primary.id)
    .map((candidate) => {
      const directEdge = primaryEdges.find((edge) => edge.target === candidate.id);
      return {
        disease: candidate,
        role: directEdge ? "direct" : "context",
        relationScore: directEdge ? directEdge.annual_incidence_prob : 0,
        relationLabel: directEdge
          ? `Direkter Pfad ab ${directEdge.stage_from}`
          : "Kein direkter Primarpfad"
      };
    })
    .sort((left, right) => right.relationScore - left.relationScore)
    .forEach((entry) => {
      lanes.push({
        ...entry,
        currentStageId: null,
        stages: entry.disease.stages
      });
    });

  const elapsedYears = primary.stages
    .slice(0, Math.max(primaryIndex, 0))
    .reduce((sum, stage) => sum + Number(stage.years_in_stage_median || 0), 0);

  return {
    lanes,
    onsetAge: clamp(patient.age - elapsedYears, 18, patient.age),
    elapsedYears,
    currentStage: primary.stages[primaryIndex]
  };
}

export function deriveNetworkModel(context, patient, filters = {}) {
  const search = String(filters.search || "").trim().toLowerCase();
  const cluster = filters.cluster || "all";
  const modifiableOnly = Boolean(filters.modifiableOnly);
  const fromCurrentStageOnly = Boolean(filters.fromCurrentStageOnly);
  const pinnedDiseaseId = filters.pinnedDiseaseId || null;

  const primary = getDisease(context, patient.primary_disease);
  const currentIndex = getStageIndex(primary, patient.stage);
  const reachedStages = new Set(primary.stages.slice(0, currentIndex + 1).map((stage) => stage.id));

  const allEdges = getAllEdges(context).map((edge) => {
    const relevance =
      edge.source === primary.id
        ? reachedStages.has(edge.stage_from) ? 2 : 1
        : 0;
    return { ...edge, relevance };
  });

  const filteredEdges = allEdges.filter((edge) => {
    if (modifiableOnly && !edge.modifiable) return false;
    if (fromCurrentStageOnly && edge.relevance !== 2) return false;
    if (cluster !== "all") {
      const sourceDisease = getDisease(context, edge.source);
      const targetDisease = getDisease(context, edge.target);
      if (sourceDisease.cluster !== cluster && targetDisease.cluster !== cluster) return false;
    }
    return true;
  });

  const pathTrace = pinnedDiseaseId
    ? findDirectedPath(primary.id, pinnedDiseaseId, filteredEdges)
    : [];
  const pathEdgeIds = new Set();
  for (let index = 0; index < pathTrace.length - 1; index += 1) {
    const edge = filteredEdges.find(
      (candidate) => candidate.source === pathTrace[index] && candidate.target === pathTrace[index + 1]
    );
    if (edge) pathEdgeIds.add(edge.id);
  }

  const nodes = context.diseases.map((disease) => {
    const matchesSearch = !search || disease.label.toLowerCase().includes(search) || disease.icd10.toLowerCase().includes(search);
    const inCluster = cluster === "all" || disease.cluster === cluster;
    const connected = filteredEdges.some((edge) => edge.source === disease.id || edge.target === disease.id);
    return {
      id: disease.id,
      label: disease.label,
      shortLabel: disease.short_label,
      icd10: disease.icd10,
      prevalence: disease.prevalence_germany,
      cluster: disease.cluster,
      confidence: disease.confidence,
      isPrimary: disease.id === primary.id,
      isPinned: disease.id === pinnedDiseaseId,
      matchesSearch,
      visible: (matchesSearch || disease.id === primary.id || disease.id === pinnedDiseaseId) && (inCluster || disease.id === primary.id || connected),
      directRisk: filteredEdges
        .filter((edge) => edge.source === primary.id && edge.target === disease.id)
        .reduce((sum, edge) => sum + edge.annual_incidence_prob, 0)
    };
  });

  const visibleNodeIds = new Set(nodes.filter((node) => node.visible).map((node) => node.id));
  return {
    nodes: nodes.filter((node) => visibleNodeIds.has(node.id)),
    edges: filteredEdges
      .filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
      .map((edge) => ({ ...edge, onPinnedPath: pathEdgeIds.has(edge.id) })),
    pathTrace,
    pinnedDiseaseId
  };
}

function findDirectedPath(sourceId, targetId, edges) {
  if (!targetId || sourceId === targetId) return [sourceId];
  const queue = [[sourceId]];
  const seen = new Set([sourceId]);

  while (queue.length) {
    const path = queue.shift();
    const current = path[path.length - 1];
    const neighbours = edges.filter((edge) => edge.source === current).map((edge) => edge.target);
    for (const next of neighbours) {
      if (seen.has(next)) continue;
      const nextPath = [...path, next];
      if (next === targetId) return nextPath;
      seen.add(next);
      queue.push(nextPath);
    }
  }

  return [];
}

export function simulateTrajectory(context, patient, activeInterventionIds = [], options = {}) {
  const horizon = Math.min(options.horizon ?? 30, 95 - patient.age);
  const samples = options.samples ?? 240;
  const seed = options.seed ?? 1;
  const paths = [];

  for (let index = 0; index < samples; index += 1) {
    paths.push(runOnePath(context, patient, activeInterventionIds, horizon, mulberry32(seed + index * 9973)));
  }

  const survival = Array.from({ length: horizon + 1 }, (_, year) => {
    const aliveCount = paths.reduce((sum, path) => sum + path.alive[year], 0);
    return aliveCount / samples;
  });

  const survivalLow = survival.map((value) => clamp(value - 1.96 * Math.sqrt((value * (1 - value)) / samples), 0, 1));
  const survivalHigh = survival.map((value) => clamp(value + 1.96 * Math.sqrt((value * (1 - value)) / samples), 0, 1));

  const diseaseAtYear = new Map();
  context.diseases.forEach((disease) => {
    diseaseAtYear.set(
      disease.id,
      Array.from({ length: horizon + 1 }, (_, year) => {
        const count = paths.reduce((sum, path) => sum + Number(path.activeByYear[year].has(disease.id)), 0);
        return count / samples;
      })
    );
  });

  const costMean = Array.from({ length: horizon + 1 }, (_, year) => mean(paths.map((path) => path.cost[year])));
  const costP25 = Array.from({ length: horizon + 1 }, (_, year) => quantile(paths.map((path) => path.cost[year]), 0.25));
  const costP75 = Array.from({ length: horizon + 1 }, (_, year) => quantile(paths.map((path) => path.cost[year]), 0.75));

  const onsetCounts = new Map();
  context.diseases.forEach((disease) => onsetCounts.set(disease.id, 0));
  paths.forEach((path) => {
    Object.entries(path.onsetYears).forEach(([diseaseId, year]) => {
      if (year > 0) onsetCounts.set(diseaseId, onsetCounts.get(diseaseId) + 1);
    });
  });

  const topFutureDiseases = context.diseases
    .filter((disease) => disease.id !== patient.primary_disease)
    .map((disease) => {
      const edgeConfidence = maxEdgeConfidenceForTarget(context, disease.id);
      return {
        id: disease.id,
        label: disease.label,
        probability10: diseaseAtYear.get(disease.id)[Math.min(10, horizon)] || 0,
        probability20: diseaseAtYear.get(disease.id)[Math.min(20, horizon)] || 0,
        firstEventShare: (onsetCounts.get(disease.id) || 0) / samples,
        confidence: edgeConfidence
      };
    })
    .filter((entry) => entry.probability10 > 0.01 || entry.firstEventShare > 0.01)
    .sort((left, right) => right.probability10 - left.probability10);

  const medianSurvival = findMedianSurvival(survival, horizon);
  const mortality10 = 1 - (survival[Math.min(10, horizon)] ?? 1);
  const mortality10Interval = [
    1 - (survivalHigh[Math.min(10, horizon)] ?? 1),
    1 - (survivalLow[Math.min(10, horizon)] ?? 1)
  ];

  return {
    horizon,
    labels: Array.from({ length: horizon + 1 }, (_, year) => year),
    survival,
    survivalLow,
    survivalHigh,
    costMean,
    costP25,
    costP75,
    diseaseAtYear,
    topFutureDiseases,
    mortality10,
    mortality10Interval,
    medianSurvival,
    activeCount10: mean(paths.map((path) => path.activeByYear[Math.min(10, horizon)].size)),
    costAt10: mean(paths.map((path) => path.cost[Math.min(10, horizon)]))
  };
}

function runOnePath(context, patient, activeInterventionIds, horizon, rng) {
  const active = new Map();
  const primaryDisease = getDisease(context, patient.primary_disease);
  const startIndex = getStageIndex(primaryDisease, patient.stage);
  active.set(primaryDisease.id, startIndex);

  const visitedStages = new Map();
  visitedStages.set(primaryDisease.id, new Set(primaryDisease.stages.slice(0, startIndex + 1).map((stage) => stage.id)));

  const onsetYears = { [primaryDisease.id]: 0 };
  const alive = new Array(horizon + 1).fill(1);
  const cost = new Array(horizon + 1).fill(costForStage(primaryDisease.stages[startIndex]));
  const activeByYear = new Array(horizon + 1).fill(null).map(() => new Set());
  activeByYear[0] = new Set([primaryDisease.id]);

  for (let year = 1; year <= horizon; year += 1) {
    for (const [diseaseId, stageIndex] of [...active.entries()]) {
      const disease = getDisease(context, diseaseId);
      const stage = disease.stages[stageIndex];
      if (!stage || !stage.annual_progression_prob) continue;
      if (stageIndex >= disease.stages.length - 1) continue;
      const sampledProgression = sampleRange(rng, stage.uncertainty_range?.annual_progression_prob, stage.annual_progression_prob);
      const progressionMultiplier = computeProgressionMultiplier(disease, stage, patient, activeInterventionIds);
      if (rng() < clamp(sampledProgression * progressionMultiplier, 0, 0.85)) {
        const nextIndex = stageIndex + 1;
        active.set(diseaseId, nextIndex);
        if (!visitedStages.has(diseaseId)) visitedStages.set(diseaseId, new Set());
        visitedStages.get(diseaseId).add(disease.stages[nextIndex].id);
      }
    }

    for (const [diseaseId, stageIndex] of [...active.entries()]) {
      const disease = getDisease(context, diseaseId);
      const currentStage = disease.stages[stageIndex];
      for (const edge of disease.outgoing_edges || []) {
        if (active.has(edge.target)) continue;
        const hasReachedSourceStage = visitedStages.get(diseaseId)?.has(edge.stage_from) || currentStage.id === edge.stage_from;
        if (!hasReachedSourceStage) continue;
        const sampledIncidence = sampleRange(rng, edge.uncertainty_range?.annual_incidence_prob, edge.annual_incidence_prob);
        const incidenceMultiplier = computeEdgeMultiplier(context, edge, patient, activeInterventionIds);
        const annualProbability = clamp(sampledIncidence * incidenceMultiplier, 0, 0.80);
        if (rng() < annualProbability) {
          active.set(edge.target, 0);
          if (!visitedStages.has(edge.target)) visitedStages.set(edge.target, new Set());
          const targetDisease = getDisease(context, edge.target);
          visitedStages.get(edge.target).add(targetDisease.stages[0].id);
          onsetYears[edge.target] = year;
        }
      }
    }

    const activeStages = [...active.entries()].map(([diseaseId, stageIndex]) => ({
      disease_id: diseaseId,
      stage: getDisease(context, diseaseId).stages[stageIndex]
    }));

    const baseQx = getBaselineMortality(context, patient.age + year, patient.sex);
    const baseHazard = -Math.log(Math.max(1e-9, 1 - baseQx));
    const totalLogHazard = computeLogHazard(context, patient, activeStages, activeInterventionIds);
    const annualDeathProbability = clamp(1 - Math.exp(-baseHazard * Math.exp(totalLogHazard)), 0, 0.95);

    if (rng() < annualDeathProbability) {
      for (let futureYear = year; futureYear <= horizon; futureYear += 1) {
        alive[futureYear] = 0;
        activeByYear[futureYear] = new Set(activeByYear[Math.max(year - 1, 0)]);
        cost[futureYear] = cost[year - 1];
      }
      break;
    }

    alive[year] = 1;
    activeByYear[year] = new Set([...active.keys()]);
    cost[year] = maxCostScore(active, context);
  }

  return { alive, cost, activeByYear, onsetYears };
}

function computeLogHazard(context, patient, activeStages, activeInterventionIds) {
  let total = 0;
  activeStages.forEach(({ disease_id, stage }, index) => {
    const baseLog = Math.log(sampleStageHr(stage));
    total += index === 0 || disease_id === patient.primary_disease ? baseLog : baseLog * 0.72;
    (stage.intervention_effects || []).forEach((effect) => {
      if (activeInterventionIds.includes(effect.intervention_id) && effect.hazard_multiplier) {
        total += Math.log(effect.hazard_multiplier);
      }
    });
  });

  biomarkerDriverEntries(patient).forEach((entry) => {
    total += entry.logHazard;
  });

  const activeConditions = Math.max(0, activeStages.length - 1);
  total += activeConditions * 0.07;

  return clamp(total, -0.6, 2.6);
}

function sampleStageHr(stage) {
  return stage.mortality_hr;
}

function computeProgressionMultiplier(disease, stage, patient, activeInterventionIds) {
  let multiplier = 1;

  if (disease.cluster === "metabolic") {
    if (patient.bmi >= 30) multiplier *= 1.08;
    if (patient.hba1c >= 7) multiplier *= 1.12;
    if (patient.ldl >= 130) multiplier *= 1.05;
  }
  if (disease.cluster === "cardiorenal") {
    if (patient.systolic_bp >= 140) multiplier *= 1.12;
    if (patient.egfr < 60) multiplier *= 1.08;
    if (patient.albuminuria_acr >= 30) multiplier *= 1.10;
  }
  if (disease.cluster === "mental") {
    if (patient.phq9 >= 10) multiplier *= 1.14;
    if (patient.smoking_status === "active") multiplier *= 1.05;
  }
  if (patient.smoking_status === "active" && disease.cluster !== "mental") {
    multiplier *= 1.04;
  }

  (stage.intervention_effects || []).forEach((effect) => {
    if (activeInterventionIds.includes(effect.intervention_id) && effect.progression_multiplier) {
      multiplier *= effect.progression_multiplier;
    }
  });

  return clamp(multiplier, 0.45, 1.65);
}

function computeEdgeMultiplier(context, edge, patient, activeInterventionIds) {
  const targetDisease = getDisease(context, edge.target);
  let multiplier = 1;

  if (targetDisease.cluster === "cardiorenal") {
    if (patient.systolic_bp >= 140) multiplier *= 1.12;
    if (patient.ldl >= 130) multiplier *= 1.08;
    if (patient.smoking_status === "active") multiplier *= 1.10;
    if (patient.egfr < 60) multiplier *= 1.09;
  }
  if (targetDisease.cluster === "metabolic") {
    if (patient.bmi >= 30) multiplier *= 1.12;
    if (patient.hba1c >= 6.5) multiplier *= 1.09;
    if (patient.ldl >= 130) multiplier *= 1.05;
  }
  if (targetDisease.cluster === "mental") {
    if (patient.phq9 >= 10) multiplier *= 1.15;
    if (patient.smoking_status === "active") multiplier *= 1.05;
  }
  if (patient.albuminuria_acr >= 30 && edge.target === "ckd") multiplier *= 1.15;

  (edge.intervention_effects || []).forEach((effect) => {
    if (activeInterventionIds.includes(effect.intervention_id) && effect.incidence_multiplier) {
      multiplier *= effect.incidence_multiplier;
    }
  });

  return clamp(multiplier, 0.45, 1.80);
}

export function getBaselineMortality(context, age, sex) {
  const anchors = context.meta.baseline_mortality[sex] || context.meta.baseline_mortality.male;
  if (age <= anchors[0].age) return anchors[0].qx;
  if (age >= anchors[anchors.length - 1].age) return anchors[anchors.length - 1].qx;

  for (let index = 0; index < anchors.length - 1; index += 1) {
    const current = anchors[index];
    const next = anchors[index + 1];
    if (age >= current.age && age <= next.age) {
      const weight = (age - current.age) / (next.age - current.age);
      const logQx = Math.log(current.qx) + (Math.log(next.qx) - Math.log(current.qx)) * weight;
      return Math.exp(logQx);
    }
  }

  return anchors[anchors.length - 1].qx;
}

function findMedianSurvival(survival, horizon) {
  for (let year = 0; year <= horizon; year += 1) {
    if (survival[year] <= 0.5) return year;
  }
  return horizon;
}

function maxEdgeConfidenceForTarget(context, diseaseId) {
  const confidenceWeight = getAllEdges(context)
    .filter((edge) => edge.target === diseaseId)
    .reduce((max, edge) => Math.max(max, CONFIDENCE_WEIGHT[edge.confidence] || 1), 1);
  if (confidenceWeight >= 3) return "high";
  if (confidenceWeight >= 2) return "moderate";
  return "low";
}

function costForStage(stage) {
  return COST_SCORE[stage.cost_class] || 0;
}

function maxCostScore(activeMap, context) {
  let max = 0;
  [...activeMap.entries()].forEach(([diseaseId, stageIndex]) => {
    const stage = getDisease(context, diseaseId).stages[stageIndex];
    max = Math.max(max, costForStage(stage));
  });
  return max;
}

export function buildEvidencePayload(context, descriptor) {
  if (!descriptor) return null;

  if (descriptor.type === "disease") {
    const disease = getDisease(context, descriptor.id);
    return {
      type: "disease",
      kicker: "Diagnose",
      title: disease.label,
      subtitle: `${disease.icd10} · ${disease.cluster}`,
      summary: disease.clinical_basis,
      confidence: disease.confidence,
      citations: getCitationBundle(context, disease.citation_ids),
      bullets: [
        `Praevalenz DE: ${(disease.prevalence_germany * 100).toFixed(1)}%`,
        `Nicht diagnostiziert: ${(disease.undiagnosed_fraction * 100).toFixed(0)}%`,
        `Underwriting-Rolle: ${disease.underwriting_role}`
      ],
      rules: disease.supported_inputs.map((inputId) => ({ label: inputId, note: "relevanter Eingabekanal" }))
    };
  }

  if (descriptor.type === "stage") {
    const disease = getDisease(context, descriptor.diseaseId);
    const stage = getStage(disease, descriptor.id);
    return {
      type: "stage",
      kicker: "Stage",
      title: stage.label,
      subtitle: `${disease.label} · ${stage.stage_definition}`,
      summary: stage.clinical_basis,
      confidence: stage.confidence,
      citations: getCitationBundle(context, stage.citation_ids),
      bullets: [
        `Mortalitaets-HR: ${stage.mortality_hr.toFixed(2)} (${stage.uncertainty_range?.mortality_hr?.join(" - ") || "ohne Band"})`,
        `Jaehrliche Progression: ${Math.round(stage.annual_progression_prob * 100)}%`,
        `Medianer Verbleib: ${stage.years_in_stage_median} Jahre`,
        `Kostenklasse: ${stage.cost_class}`
      ],
      rules: stage.biomarker_rules || [],
      interventions: (stage.intervention_effects || []).map((effect) => {
        const intervention = getIntervention(context, effect.intervention_id);
        return {
          label: intervention?.label || effect.intervention_id,
          note: effect.note
        };
      })
    };
  }

  if (descriptor.type === "edge") {
    const edge = context.edgesById.get(descriptor.id);
    const source = getDisease(context, edge.source);
    const target = getDisease(context, edge.target);
    return {
      type: "edge",
      kicker: "Pfad",
      title: `${source.short_label} -> ${target.short_label}`,
      subtitle: `Ab Stage ${edge.stage_from} · Lag ${edge.lag_years} Jahre`,
      summary: edge.clinical_basis,
      confidence: edge.confidence,
      citations: getCitationBundle(context, edge.citation_ids),
      bullets: [
        `Annualisierte Inzidenzannahme: ${(edge.annual_incidence_prob * 100).toFixed(1)}%`,
        `Modifizierbar: ${edge.modifiable ? "ja" : "nein"}`,
        `Bidirektional: ${edge.bidirectional ? "ja" : "nein"}`
      ],
      rules: edge.biomarker_rules || [],
      interventions: (edge.intervention_effects || []).map((effect) => {
        const intervention = getIntervention(context, effect.intervention_id);
        return {
          label: intervention?.label || effect.intervention_id,
          note: effect.note
        };
      })
    };
  }

  return null;
}

export function buildSourceCards(context) {
  return context.citations.map((citation) => ({
    ...citation,
    diseaseCount: context.diseases.filter((disease) => disease.citation_ids.includes(citation.id)).length
  }));
}

function sampleRange(rng, range, fallback) {
  if (!Array.isArray(range) || range.length !== 2) return fallback;
  return range[0] + (range[1] - range[0]) * rng();
}

function quantile(values, percentile) {
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.max(0, Math.floor(percentile * sorted.length)));
  return sorted[index] ?? 0;
}

function mean(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function mulberry32(seed) {
  let t = seed >>> 0;
  return function next() {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}
