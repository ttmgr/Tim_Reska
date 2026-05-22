// Single source of truth for nanopore-advisor field semantics: which question
// fields exist, which are "core" (their answers unlock a recommendation) vs
// "constraint" (optional refinements), and how a field maps to its page.
//
// Loaded before recommendation-engine.js and app.js, which previously each
// re-declared these (CORE_FIELDS, the constraint list, fieldToPageId) and could
// drift apart when a question field was added. Field *labels* deliberately stay
// local to each file: the engine uses lowercase sentence fragments for inline
// messages ("revisit your molecule type"), the UI uses Title Case chips.

const CORE_FIELDS = ['molecule', 'study_type', 'priority'];

const CONSTRAINT_FIELDS = [
  'input_amount', 'input_quality', 'host_background',
  'barcoding_needed', 'device', 'compute_gpu'
];

function isConstraintField(field) {
  return !CORE_FIELDS.includes(field);
}

function fieldToPageId(field) {
  return CORE_FIELDS.includes(field) ? field : 'constraints';
}
