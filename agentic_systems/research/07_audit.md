# Agentic Frontier Primer — Orchestrator Audit Report
## Agent 7: Speed-up Opportunities Across Tim's Multi-Agent Skills

---

## /48-dd-multi-agent

**(a) Parallelism unlock:** Phases 0.5, 0.6, and 0.7 run sequentially despite zero dependencies between them — "interview synth subagent", "data fetcher subagent", and ingestion waves are independent. Collapse into a single parallel spawn message to run all three in parallel. Phase 1 (Agents A/B/C) already parallelise correctly, but starting 0.5–0.7 in the same message would save ~3–5 min wall-clock time per engagement.

**(b) Model downgrade:** Phase 0 calls Opus "with max thinking" for scope/brand/mode setup — mechanical task. Downgrade to Sonnet; reserve Opus for Phase 2a/2b synthesis and Phase 3 validation. Phase 0.5 ingestion subagents already use Sonnet (correct). Phase 1a/b/c already Sonnet (correct). No downgrade needed below Phase 2a.

**(c) Phase skip/merge:** Phase 0.6 interview synth and Phase 0.7 data fetcher both produce lightweight JSON artifacts (`customer_synthesis.json`, `external_evidence.json`) that are immediately consumed in Phase 1. Consider merging into Phase 0.7 as an optional "customer context" sub-task within Data Fetcher, gated by engagement flag — saves a subagent spawn if the engagement has no customer interviews.

---

## /42-askeras-ai-enablement

**(a) Parallelism unlock:** Phases 0.5 (ingestion) and 0.7 (data fetcher) run sequentially. Both are independent subagents with zero dependency on each other — they feed different knowledge pools into Phase 1. Spawn both in the same message to run in parallel. Also, Phase 1.5 specialists (EU AI Act, Vendor TCO, Sector benchmark) are gated as "opt-in, mandatory for `side=regulator`" but run sequentially after Phase 1a/b/c finish. Since 1.5 depends only on Phase 0 scope + 0.5/0.7 evidence, it can spawn alongside Agents A/B/C in a wave-2 message (after 0.5/0.7 complete) rather than waiting for 1a/b/c to finish writing.

**(b) Model downgrade:** Phase 0 is marked "orchestrator" (model not specified; implies Opus). If this handles setup/brand-param negotiation, it is mechanical — downgrade to Sonnet. Phase 2a (Agent D — fit matrix) runs in "main context" and calls the model "orchestrator", likely Opus; this is synthesis and should stay Opus. Phase 2b (Agent E — wave plan) also orchestrator model; this is scenario stress-test and decision-logic, legitimately Opus. Keep Opus for phases 2a/2b and validator; downgrade Phase 0 to Sonnet.

**(c) Phase skip/merge:** Phase 1.5 specialists (EU AI Act, Vendor TCO, Sector benchmark) are modular opt-ins. When `side=regulator`, Phase 1.5 EU AI Act Conformity is mandatory and runs after Phase 1a/b/c complete. Consider making it spawn in parallel with Phase 1a/b/c (depends only on Phase 0 outputs, not on 1a/b/c results) to save ~2–3 min. For non-regulator sides, Vendor TCO and Sector benchmark are truly optional — document the condition more explicitly so they can be skipped for lean engagements without overhead.

---

## /49-multi-agent-science

**(a) Parallelism unlock:** Phase 0.5 ingestion runs as a single Haiku subagent. After it completes, Phases 1a, 1b, 1c spawn in parallel (already correct). However, Phase 0.5 is a pure extraction/structuring task — consider running it inline (not as a subagent spawn) to save context-switch overhead, since Haiku is doing simple parse-and-normalise, not reasoning. Alternatively: Phase 0.5 can spawn with unlimited latency tolerance (fire-and-forget) while the orchestrator prefills Phase 1a/b/c prompts in parallel, then await both. This surfaces parallelism earlier (Phase 1 starts earlier, overlapping 0.5's runtime).

**(b) Model downgrade:** Phase 0 is Opus + max thinking — orchestrator, scope, hypothesis; this is high-stakes reasoning (affects all downstream work) and earns Opus. Phases 1a/b/c are Sonnet — correct, they are specialist retrieval + structured analysis at lower cost. Phase 2a/2b (Agent D — interpretation; Agent E — limitations) are Opus + max thinking — these are synthesis and stress-test, correctly stay Opus. Phase 3 Reviewer is Opus + max thinking — the comment states "it is the only guard against overconfidence"; downgrade here is forbidden. Phase 4 synthesis is Opus + max thinking — correct (must reconcile A+B+C+D+E+Reviewer). Phase 5 deliverables downgrade to Sonnet — correct. No downgrades available without losing quality; this skill's model assignment is near-optimal for reasoning load.

**(c) Phase skip/merge:** Phase 0.5 ingestion exists to normalise messy inputs. For a clean drop (preprint + data summary + clear methods), Phase 0.5 adds latency with minimal value. Gate it explicitly: only spawn Phase 0.5 if `inputs/` contains >5 files or the orchestrator flags "messy drop". For single-file inputs (polished preprint only), skip 0.5 and have Phase 1 agents read the inputs directly. This saves 30–60 sec for clean engagements.

---

## /78-multi-agent-qc

**(a) Parallelism unlock:** The hub-routed fan-out (step 1) already dispatches one Sonnet Explore agent per navigation node "in a single message" — this is correct parallelism. The verification pass (step 3) groups falsifiable claims by **theme** and dispatches one Opus verifier per theme group "all in a single message" — also correct. No additional parallelism available here; the skill already maximises fan-out within each phase.

**(b) Model downgrade:** Sonnet for fan-out breadth is correct. Opus for verification only (step 3) is correct — "a false-positive bug report is costly; pay for proof exactly where it matters." However, step 3 instruction says "For each theme group, dispatch an `Explore` agent with `model=opus`"  — if multiple theme groups exist, each gets its own Opus agent. This is correct (parallel verification scales with claim volume), but confirm that grouping by theme is aggressive enough to avoid N subagents for N claims. For a high-volume QC run (100+ findings), theme grouping could collapse to 5–8 verification agents; verify the grouping heuristic is strong. No downgrade recommended.

**(c) Phase skip/merge:** The triage phase (step 2) is synchronous prose between the fan-out and verification. For thin codebases (few findings), the overhead is negligible. For large codebases, consider collapsing triage into the verification dispatch: have the Opus verifier receive the raw Sonnet findings (not triaged) and emit the triage+verification result in one pass. This saves a prose round-trip; trade-off is the Opus prompt becomes larger. Recommend this optimisation only if a large-codebase engagement proves slow.

---

## /71-llm-coding-radar

**(a) Parallelism unlock:** The fan-out (step 2) dispatches "one agent per cluster, in parallel (single message, multiple Agent calls)" — this is correct. Six clusters (Anthropic/Claude, OpenAI, Google, open-source agents, IDE/MCP, research) spawn in one message. No additional parallelism available; the skill already maximises breadth.

**(b) Model downgrade:** All fan-out agents use `subagent_type=general-purpose` with no explicit model specified. For a curation/research task (WebSearch + WebFetch), Sonnet is the right pick — it retrieves, filters, and structures. Confirm the skill is not accidentally using Opus for the research agents. If it is, downgrade to Sonnet; if it is already Sonnet, no change needed.

**(c) Phase skip/merge:** Synthesis and curation (step 3) is a synchronous prose pass over the pooled findings. For a high-velocity ecosystem (100+ items per week), consider having one agent do synthesis directly from the raw fan-out results (no separate triage). The agent would emit "new items" + "updates to known items" + "still developing" in one pass, skipping the manual dedup/rank/curate step. Trade-off is the agent prompt becomes prescriptive about ranking; benefit is faster turnaround (30 sec vs 3–5 min) for a high-volume scan. Not critical for weekly runs, but document as an option.

---

## Cross-skill patterns

1. **Phase 0 mechanical work**: Across `/48-dd`, `/42-askeras`, and `/49-science`, Phase 0 orchestrator setups (scope, brand, hypothesis) are scoped as "Opus + max thinking" but contain mechanical busywork (restate target name, set environment variables, confirm font choice). Push this to Sonnet; reserve Opus for the first synthesis phase (Phase 2a or later) where reasoning matters. Estimated savings: ~15–20% of Opus token budget per engagement.

2. **Sequential Phase 0.X independence**: Both `/48-dd` and `/42-askeras` have phases 0.5, 0.6, 0.7 (or 0.5, 0.7) that spawn one after the other despite zero dependencies. Single message with parallel spawns saves 2–5 min per engagement. `/49-science` Phase 0.5 should gate on input messiness to avoid latency tax on clean drops.

3. **Verification pattern load-bearing**: All three due-diligence skills (`/48-dd`, `/42-askeras`, `/49-science`) use a blind Phase-3 validator (Opus + max thinking) as the "single most consequential use of Opus". This pattern is load-bearing — never downgrade. However, Phase 3 triage (grouping falsifiable claims) should be aggressive to minimise the number of Opus verifier spawns for high-volume findings.

4. **Deliverable templating**: `/48-dd`, `/42-askeras`, and `/49-science` all emit structured JSON at the end of phases 1/2/3. The schema structure is nearly identical (facts/assumptions/interpretations/key_risks/open_questions/confidence). Consider centralising the JSON schema into a shared reference (`_assets/schemas/multi-agent-shared.schema.json`) and validating all three skills against it. This decouples schema evolution from skill rewrites.

5. **Ingestion as optional gate**: `/49-science` has a candidate to skip Phase 0.5 for clean inputs; `/48-dd` and `/42-askeras` could adopt the same gate. For thin ingestion work (single document, no manual interviews), spawn Phase 0.5 as async/fire-and-forget to let Phase 1 agents start earlier. Upside: shaves ~1 min on clean engagements. Downside: slightly trickier orchestrator logic. Recommend this for `/49-science` first (where Phase 0.5 ingestion is explicitly optional); revisit for the others if engagements frequently include clean data.

