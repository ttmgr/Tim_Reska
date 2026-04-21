import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { createDataContext } from "../assets/js/data.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const raw = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "diseases.json"), "utf8"));
const context = createDataContext(raw);

const errors = [];
const interventionIds = new Set(context.interventions.map((entry) => entry.id));

context.diseases.forEach((disease) => {
  if (!disease.stages.length) {
    errors.push(`${disease.id}: keine Stages definiert`);
  }

  const severityRanks = disease.stages.map((stage) => stage.severity_rank);
  for (let index = 1; index < severityRanks.length; index += 1) {
    if (severityRanks[index] <= severityRanks[index - 1]) {
      errors.push(`${disease.id}: severity_rank nicht strikt steigend`);
    }
  }

  disease.citation_ids.forEach((citationId) => {
    if (!context.citationsById.has(citationId)) {
      errors.push(`${disease.id}: unbekannte disease citation ${citationId}`);
    }
  });

  disease.stages.forEach((stage) => {
    if (stage.annual_progression_prob < 0 || stage.annual_progression_prob > 1) {
      errors.push(`${stage.id}: annual_progression_prob ausserhalb [0,1]`);
    }
    if (!Array.isArray(stage.biomarker_rules) || !stage.biomarker_rules.length) {
      errors.push(`${stage.id}: biomarker_rules fehlen`);
    }
    if (!stage.citation_ids.every((citationId) => context.citationsById.has(citationId))) {
      errors.push(`${stage.id}: mind. eine citation_id ist unaufloesbar`);
    }
    if (stage.uncertainty_range?.annual_progression_prob) {
      const [low, high] = stage.uncertainty_range.annual_progression_prob;
      if (low > high) errors.push(`${stage.id}: Progressionsband nicht geordnet`);
    }
    if (stage.uncertainty_range?.mortality_hr) {
      const [low, high] = stage.uncertainty_range.mortality_hr;
      if (low > high) errors.push(`${stage.id}: HR-Band nicht geordnet`);
    }
    (stage.biomarker_rules || []).forEach((rule) => {
      if (rule.operator === "range" && Array.isArray(rule.value) && rule.value[0] > rule.value[1]) {
        errors.push(`${stage.id}: range rule fuer ${rule.marker} ist nicht geordnet`);
      }
    });
    (stage.intervention_effects || []).forEach((effect) => {
      if (!interventionIds.has(effect.intervention_id)) {
        errors.push(`${stage.id}: unbekannte intervention ${effect.intervention_id}`);
      }
    });
  });

  (disease.outgoing_edges || []).forEach((edge) => {
    if (!context.diseasesById.has(edge.target)) {
      errors.push(`${edge.id}: Ziel ${edge.target} existiert nicht`);
    }
    if (!disease.stages.some((stage) => stage.id === edge.stage_from)) {
      errors.push(`${edge.id}: stage_from ${edge.stage_from} existiert nicht in ${disease.id}`);
    }
    if (edge.annual_incidence_prob < 0 || edge.annual_incidence_prob > 1) {
      errors.push(`${edge.id}: annual_incidence_prob ausserhalb [0,1]`);
    }
    if (!Array.isArray(edge.biomarker_rules) || !edge.biomarker_rules.length) {
      errors.push(`${edge.id}: biomarker_rules fehlen`);
    }
    if (!edge.citation_ids.every((citationId) => context.citationsById.has(citationId))) {
      errors.push(`${edge.id}: mind. eine citation_id ist unaufloesbar`);
    }
    if (edge.uncertainty_range?.annual_incidence_prob) {
      const [low, high] = edge.uncertainty_range.annual_incidence_prob;
      if (low > high) errors.push(`${edge.id}: Inzidenzband nicht geordnet`);
    }
    (edge.biomarker_rules || []).forEach((rule) => {
      if (rule.operator === "range" && Array.isArray(rule.value) && rule.value[0] > rule.value[1]) {
        errors.push(`${edge.id}: range rule fuer ${rule.marker} ist nicht geordnet`);
      }
    });
    (edge.intervention_effects || []).forEach((effect) => {
      if (!interventionIds.has(effect.intervention_id)) {
        errors.push(`${edge.id}: unbekannte intervention ${effect.intervention_id}`);
      }
    });
  });
});

context.interventions.forEach((intervention) => {
  intervention.citation_ids.forEach((citationId) => {
    if (!context.citationsById.has(citationId)) {
      errors.push(`intervention ${intervention.id}: unbekannte citation ${citationId}`);
    }
  });
});

if (errors.length) {
  console.error("VALIDATION FAILED");
  errors.forEach((entry) => console.error(`- ${entry}`));
  process.exit(1);
}

console.log("VALIDATION PASSED");
