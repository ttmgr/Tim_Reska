# Claude Agentic Cost & Speed Optimization Patterns

## Prompt Caching

**What it does.** Stores stable request prefixes (system prompts, tools, context) and charges cache-write costs once, then 90% less on subsequent cache-hits within a 5-minute window.

**When it pays off.** Caching is most valuable when the same system prompt, tools, or context documents are used repeatedly (same user session, batch processing the same schema, or multi-turn conversations). The minimum cacheable prefix is 1,024–4,096 tokens depending on model; for smaller prompts, caching adds no value and wastes cache-write overhead. Caching becomes profitable after one cache hit for 5-minute TTL (cache write costs 1.25x standard input; cache read costs 0.1x). For 1-hour extended TTL (2x write cost), break-even is two reads. On Sonnet 4.6, a 100K-token system prompt costs $0.625 to write but only $0.05 per cache hit—a 92% saving. Caching stacks with batch API (potential combined discount up to 95%).

**When NOT to use it.** Do not cache prompts under the minimum threshold, and do not place cache breakpoints on content that changes every request (user input, timestamps, per-request parameters). If your prefix changes constantly, the cache hash invalidates and you pay write costs with zero hits.

**Implementation.** Cacheable content: system prompts, tool definitions, text/image/document blocks in messages, tool-use results. Place `cache_control` on the last block that remains stable. Monitor hit rate via `response.usage.cache_creation_input_tokens` and `cache_read_input_tokens`; zero cache reads indicates breakpoint placement on changing content.

---

## Model Selection Economics

**What it does.** Match model capability to task complexity; use cheaper models (Haiku, Sonnet) for tasks that don't require Opus-level reasoning, and reserve Opus for irreducible complexity.

**When it pays off.** Cost ratios: Haiku 4.5 ($1/$5 per MTok), Sonnet 4.6 ($3/$15), Opus 4.7 ($5/$25). Sonnet achieves 79.6% on SWE-bench to Opus's 80.8%—a 1.2-point gap—at 40% cheaper and 2x faster. Use Haiku for code classification, routing, linting, documentation, and test scaffolding. Use Sonnet for feature implementation, code review, standard refactoring, and bug fixes. Reserve Opus for multi-file refactoring, architecture decisions, complex debugging, and deep scientific reasoning (GPQA Diamond: Opus 91.3% vs Sonnet 74.1%). A three-tier routing strategy (Haiku 70% of volume, Sonnet 20%, Opus 10%) delivers 50–80% cost reduction versus uniform Opus deployment.

**When NOT to use it.** Do not use Haiku for multi-file refactors, security-sensitive reviews, or tasks requiring coherence across distant code regions; Haiku's reasoning falls off sharply. Do not use Sonnet when deep scientific reasoning or multi-step autonomous agent workflows demand Opus's depth.

---

## Batch API

**What it does.** Submits requests asynchronously for processing within 24 hours at 50% discount on both input and output tokens; stacks with prompt caching.

**When it pays off.** Batching is profitable for any workload that tolerates 24-hour latency: bulk content generation, dataset labeling, model evaluation, historical analysis, report synthesis, or non-realtime agent workflows. On Sonnet 4.6, the same 10M-token input / 2M-token output costs $60 at standard rates and $30 in batch. Discount stacks with caching (potential 90% savings on cached reads, 50% on uncached). Start with batch for any offline pipeline or post-processing task.

**When NOT to use it.** Do not batch realtime requirements (chat, live agent interactions, decision-support). Do not batch if output latency is load-bearing (API responses, interactive systems, multi-step agent chains where next step depends on previous output).

---

## Deferred Tool Loading (ToolSearch)

**What it does.** Defers tool schema inclusion until the model signals intent to use a specific tool, reducing upfront token cost for large tool lists.

**When it pays off.** ToolSearch is valuable when you define 20+ tools but the model typically calls only 2–3. The upfront cost is a single routing round-trip where the model selects which tool to load; subsequent requests include only the selected tool schema. For a 50-tool system (100K tokens of schemas), deferring saves upfront overhead and avoids paying for unused schema definitions across the conversation.

**When NOT to use it.** Do not use ToolSearch for small tool lists (< 5 tools, < 10K tokens total). Do not use it if the model must commit to multiple tools in a single turn; deferred loading forces sequential tool execution.

---

## Background Execution

**What it does.** Marks long-running tasks (`run_in_background: true`) to complete asynchronously while the agent proceeds with other work; caller receives event notifications instead of blocking.

**When it pays off.** Background execution is valuable for chains of independent subagents (Haiku filters, Sonnet analytes, Opus synthesist run in parallel), long-running file operations (HPC cluster jobs, multi-hour ML training), or batch API request submission. Deploy subagents in parallel when their outputs do not feed each other's inputs; notification-driven continuation avoids polling and keeps the main agent responsive.

**When NOT to use it.** Do not use background execution for agent chains where output feeds the next step—sequential dependencies require foreground (blocking) execution. Do not use it if you need the result immediately to make a routing or gating decision.

---

## Parallel Fan-out vs Sequential Execution

**What it does.** Launches multiple independent agents in parallel (fan-out) when their work is independent, or sequences them (serial) when one's output feeds the next.

**When it pays off.** Fan-out is profitable when subagents' tasks are independent: Haiku pre-filters multiple documents in parallel, Sonnet performs distinct analyses (code review, design check, security audit) on the same input, Opus synthesizes results from the fan-out. Real-world example: five Haiku triage agents (cost $5 total) running in parallel on five queries beats sequential Opus ($25 per query). Fan-out also reduces wall-clock time by N-fold (3 parallel agents = 1/3 latency).

**When NOT to use it.** Sequential only when genuinely dependent: agent-A's output is agent-B's required input, or the pipeline must gate on intermediate results. Parallel fan-out for dependent chains wastes cost because agents block waiting for upstreams.

---

## Context Window Management

**What it does.** Leverages the 1M-token context window in Opus 4.7 to include massive multi-document context in a single request, versus chunking into separate calls.

**When it pays off.** The 1M context is worth the per-token cost when you have >100K tokens of context and must maintain coherence across the entire span. Example: a legal review task requiring access to 500 pages of contracts, case law, and regulatory guidance can fit in one Opus call (1M window) at $5/MTok input vs multiple Sonnet calls that lose inter-document coherence. Combine with caching: cache the shared context prefix (regulations, precedent, guidance) across reviews.

**When NOT to use it.** Do not use 1M context for small documents or when context is truly independent (separate analyses benefit from separate calls). Do not rely on full-window coherence for tasks requiring precise reasoning in later pages; degradation appears past ~200K tokens (empirical, model-dependent).

---

## The Haiku-as-Pre-filter Pattern

**What it does.** Routes incoming requests through a cheap, fast Haiku classifier that decides whether the request is routine (Haiku handles it), mid-complexity (route to Sonnet), or hard (escalate to Opus).

**When it pays off.** Pre-filtering works when ~60–70% of requests are routine: simple customer queries, document categorization, API routing decisions, test selection. A Haiku pre-filter on a million-request stream costs ~$1K (1M tokens × $1/MTok) vs full-Opus at $5M. The filter overhead (one extra API call) amortizes to <1% when filtering high-volume. Combined with multi-agent parallelism: Haiku fans out to classify 10 documents in parallel, then routes survivors to Sonnet or Opus.

**When NOT to use it.** Do not pre-filter if Haiku itself is unreliable at classification; a misrouted hard task bouncing back to Opus wastes tokens and adds latency. Do not pre-filter if request volume is low (< 1K/month): overhead cost exceeds savings.

---

## Optimization Rubric

When a pipeline feels slow or expensive, pull levers in this order:

1. **Model selection first.** Can you replace Opus with Sonnet? Sonnet with Haiku? Three-tier routing (Haiku 70%, Sonnet 20%, Opus 10%) typically delivers the largest single improvement (50–80% cost reduction). Check: are you running Opus on tasks that Sonnet or Haiku can handle?

2. **Prompt caching second.** If system prompts, tools, or context are stable and reused, add cache control. Minimum investment: mark the largest static block (system prompt or legal context). Expected gain: 10–92% cost reduction on cache hits.

3. **Batch API third.** If any task tolerates 24-hour latency, migrate to batch. One-time shift in architecture; typically 50% cost reduction. Check: are you waiting for results immediately, or can you run offline?

4. **Parallel fan-out fourth.** If subagent work is independent, deploy in parallel (especially cheap Haiku agents). Trade: wall-clock latency for throughput. Check: do outputs feed subsequent inputs, or are tasks independent?

5. **Context window consolidation fifth.** If you're chunking large documents across multiple calls and losing coherence, consolidate into a single 1M-context Opus call plus caching. Check: is coherence loss measurable across chunks?

6. **Deferred tool loading sixth.** Only if tool count is large (20+) and selection narrow (2–3 out of 20+). Overhead of routing round-trip must be worth the schema token savings.

7. **Background execution seventh.** For truly parallel subagent orchestration or long-running offline tasks. Check: can the next step wait, or does it depend on the result?

---

## Sources

- [Claude API Pricing: Haiku 4.5, Sonnet 4.6, and Opus 4.7 (April 2026) | BenchLM.ai](https://benchlm.ai/blog/posts/claude-api-pricing)
- [Anthropic Claude API Pricing 2026: Opus, Sonnet & Haiku Costs - DevTk.AI](https://devtk.ai/en/blog/claude-api-pricing-guide-2026/)
- [Claude Prompt Caching in 2026: The 5-Minute TTL Change That's Costing You Money - DEV Community](https://dev.to/whoffagents/claude-prompt-caching-in-2026-the-5-minute-ttl-change-thats-costing-you-money-4363)
- [Claude API Cache Pricing 2026: 90% Input Savings Explained - TokenMix Blog](https://tokenmix.ai/blog/claude-api-cache-pricing)
- [Anthropic API Pricing in 2026: Complete Guide — Models, Caching, Batch & Optimization](https://www.finout.io/blog/anthropic-api-pricing)
- [Claude Batch API for Bulk AI Processing: 50% Cost Cut at Scale | PADISO Blog](https://www.padiso.co/blog/claude-batch-api-bulk-ai-processing-cost-reduction/)
- [Choosing the right model - Claude API Docs](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
- [Claude Opus 4.6 vs Sonnet 4.6 vs Haiku 4.5 [2026 Tested]](https://tech-insider.org/claude-opus-vs-sonnet-vs-haiku-2026/)
- [Best Claude Models in 2026 — Sonnet vs Opus vs Haiku Compared | Remote OpenClaw](https://www.remoteopenclaw.com/blog/best-claude-models-2026)
- [Best AI Model for Coding Agents in 2026: A Routing Guide | Augment Code](https://www.augmentcode.com/guides/ai-model-routing-guide)
- [AI Agent Cost Optimization in 2026: How to Cut Token Spend by 60%](https://niteagent.com/blog/ai-agent-cost-optimization-2026/)
