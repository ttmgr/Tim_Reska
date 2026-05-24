# Anthropic & Claude Code Release Timeline: October 2025 – May 2026

A dated inventory of shipments that matter for builders of agentic systems. Ordered newest-first; grouped by quarter for scannability.

---

## Q2 2026 (April–May)

**2026-05-06**
**Shipment**: Claude Managed Agents "dreaming" — self-improving memory that reviews past agent sessions for patterns. Research preview. Edge case unlocked: Autonomous agents can now reason about their own decision-making patterns across multi-session traces without human annotation. Source: [Claude Updates by Anthropic - May 2026](https://releasebot.io/updates/anthropic/claude)

**2026-05-02**
**Shipment**: Prompt caching extended TTL tiers ship: 5-minute cache (write 1.25x, read 0.1x base input cost) and 1-hour cache (write 2x, read 0.1x). Cache read tokens cost 90% less than fresh input. Edge case unlocked: Long-context RAG pipelines can now maintain semantic indices across 1-hour windows at true commodity cost, enabling sub-hour re-ranking of 10M+ token corpora. Source: [Anthropic API Pricing in 2026](https://www.finout.io/blog/anthropic-api-pricing)

**2026-04-16**
**Shipment**: Claude Opus 4.7 — most capable general-availability model; 1M context, 128k max output, high-resolution vision (2576px/3.75MP, 1:1 pixel coordinate mapping), adaptive thinking (off by default), xhigh effort level, task budgets (beta, soft token advisory per agentic loop). Breaking changes: sampling parameters removed (no temperature/top_p/top_k), extended thinking budgets removed, new tokenizer (+35% token inflation vs 4.6). Edge case unlocked: Computer use workflows can now manipulate screenshots at native resolution and self-calibrate work scope in real-time via budget countdown; knowledge workers can visually verify their own edits (.pptx redlining, chart analysis) before returning. Source: [What's new in Claude Opus 4.7](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7)

**2026-04-22**
**Shipment**: MCP ecosystem official registry crosses 800 servers. Broader ecosystem spans 10,000+ public + 3,000+ private servers. Edge case unlocked: Agentic systems can now query from a table-stakes ecosystem size; no single vendor controls tool availability; third-party middleware (gateways, authentication brokers) becomes viable. Source: [MCP Server Ecosystem 2026](https://www.qcode.cc/mcp-servers-ecosystem-2026)

---

## Q1 2026 (January–March)

**2026-03-02**
**Shipment**: Claude Memory — chat-based memory construction becomes free-tier and all-user. Chat search + import/export. Edge case unlocked: Multi-turn workflows can now build persistent context without subscribing to Team or managing .md files; memory compaction happens automatically during storage, not at request time. Source: [Claude Updates by Anthropic - May 2026](https://releasebot.io/updates/anthropic/claude)

**2026-02-17**
**Shipment**: Claude Sonnet 4.6 — cost-optimized model featuring adaptive thinking (dynamic budget, reads task context to pick thinking depth), 1M context window, same tool ecosystem as Opus 4.6. Pricing: $3 input / $15 output per million tokens. Edge case unlocked: Opus-class coding capability at Sonnet price point via cost-aware thinking, enabling per-token ROI optimization for batch and scheduled agents. Source: [Claude Sonnet 4.6 release](https://www.anthropic.com/news/claude-opus-4-6)

**2026-02-04**
**Shipment**: Claude Opus 4.6 — 1M context, adaptive thinking (replaces fixed extended-thinking budgets; off by default), effort parameter for cost-capability trade-offs. Structured output (JSON schema enforcement) becomes GA on Claude Developer Platform, Amazon Bedrock for Opus 4.5 + Sonnet 4.5 + Haiku 4.5. Edge case unlocked: Agentic loops can now trade thinking budget dynamically per task complexity; structured output shifts from prompting guarantee to compiler guarantee (impossible to violate schema). Source: [Introducing Claude Opus 4.6](https://www.anthropic.com/news/claude-opus-4-6)

**2026-02 (late)**
**Shipment**: Claude Code hooks become production-ready — 5 hook types (command, HTTP, MCP tool, prompt, agent) trigger at 25+ lifecycle points (PreToolUse, PostToolUse, Stop, UserPromptSubmit, PreCompact, etc.). Shell hooks run in isolated session; MCP tool hooks call already-connected servers; agent hooks spawn subagents for verification. Edge case unlocked: Linters, approval gates, and cost-tracking code now run deterministically outside the model's control flow; pre-commit and pre-tool-call workflows become first-class. Source: [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)

**2026-01 (late)**
**Shipment**: Claude Code Plan Mode — /plan slash command. Hard read-only sandbox where Claude analyzes codebase, proposes changes, waits for approval before touching files. Three permission modes: Default (prompt per tool), Auto-Accept (edits proceed, other tools prompt), Plan (read-only, no edits). Shift+Tab cycles modes. Edge case unlocked: Complex refactors and multi-file migrations now separate analysis from execution, cutting approval time and enabling collaborative planning. Source: [Claude Code Plan Mode 2026](https://www.getaiperks.com/en/ai/claude-code-plan-mode)

**2026-01 (early)**
**Shipment**: Prompt caching moves from organization-level to workspace-level isolation on Anthropic API. Caches now scoped per workspace; data separation guaranteed across workspaces within same organization. Edge case unlocked: Multi-tenant SaaS can now cache per-customer context without cross-tenant leakage; shared billing no longer forces shared cache isolation. Source: [Anthropic API Pricing in 2026](https://www.finout.io/blog/anthropic-api-pricing)

---

## Q4 2025 (October–December)

**2025-12-18**
**Shipment**: Agent Skills specification published as open standard at agentskills.io. Anthropic contributes as founding member. Skills formatted as SKILL.md markdown with trigger conditions, edge cases, and tool allowlists. Edge case unlocked: Portable agent skill ecosystem emerges (like npm, but for workflows); skills become interoperable across Claude, third-party agents, and enterprise orchestrators. Source: [Claude Skills: Launch Timeline & Technical Overview](https://www.verdent.ai/guides/claude-skills-announcement-news)

**2025-12-17**
**Shipment**: Message Batches API becomes Generally Available. 50% cost reduction vs standard API (batch write tokens cost standard rate; processed within 24h). Supports all Claude 3.5+ models. Edge case unlocked: Cost-sensitive workloads (data labeling, bulk inference, document processing) can now defer latency tolerance for 50% savings; batch processing shifts from bespoke to standard. Source: [Introducing the Message Batches API](https://www.anthropic.com/news/message-batches-api)

**2025-12-04**
**Shipment**: Structured Output (JSON schema enforcement) extends to Claude Haiku 4.5 in public beta. Compiles schema into grammar; impossible to generate invalid JSON. Schema-aware tool definitions (strict: true) available. Edge case unlocked: Cost-optimized agents can now guarantee output validity at Haiku price point; cheap agents stop leaking cost to downstream parsing/retry. Source: [Structured outputs - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

**2025-11-24**
**Shipment**: Claude Opus 4.5 — flagship model; 200k context window, 128k output, extended thinking (fixed budget_tokens), vision, tool use. Pricing: $15 input / $75 output per million tokens. Edge case unlocked: Sustained reasoning on long-horizon tasks now happens at Opus quality; extended thinking enables first-principles problem solving without intermediate API calls. Source: [Claude Opus 4.5 Released](https://medium.com/@ZombieCodeKill/claude-opus-4-5-released-9e9bd9a32ad9)

**2025-11-14**
**Shipment**: Structured Output (JSON schema enforcement) launches public beta on Claude Sonnet 4.5 + Opus 4.1 via Claude Developer Platform. Pydantic + Zod schema support. Beta header: structured-outputs-2025-11-13. Edge case unlocked: Production LLM systems can now guarantee valid schema on every response; downstream parsing becomes stateless. Source: [Structured outputs on the Claude Developer Platform](https://claude.com/blog/structured-outputs-on-the-claude-developer-platform)

**2025-10-22**
**Shipment**: Claude Code on the web — IDE becomes available at claude.com (not just desktop). Features: skills, hooks, plan mode, slash commands, MCP integration. Edge case unlocked: Browser-native agentic workflows become first-class; Claude Code now competes with GitHub Copilot Chat on every surface, not just desktop. Source: [Anthropic Launches Claude Code on the Web](https://mlq.ai/news/anthropic-launches-claude-code-on-the-web/)

**2025-10-16**
**Shipment**: Claude Code Skills — custom markdown workflows (.claude/skills/<name>/SKILL.md) with explicit triggers, examples, and tool allowlists. Paired with subagents (.claude/agents/<name>.md) for restricted experts. Available on Claude.ai, Claude Code, and API. Anthropic ships pre-built skills (PPTX, XLSX, DOCX, PDF generation). Code Execution required. Edge case unlocked: Prompt engineering becomes declarative; non-engineers can now define workflows without writing Python; skills become composable across teams. Source: [Claude Skills are awesome, maybe a bigger deal than MCP](https://simonwillison.net/2025/Oct/16/claude-skills/)

**2025-10-15**
**Shipment**: Claude Haiku 4.5 — lightweight model; 200k context, 73.3% on SWE-bench, multimodal (text+image). Pricing: $1 input / $5 output per million tokens. Edge case unlocked: One-third the cost of Sonnet 4.5; agentic loops for high-volume classification, summarization, and light coding now run at true marginal cost (<$0.001 per task). Source: [Claude Haiku 4.5 Review](https://medium.com/@leucopsis/claude-haiku-4-5-review-4ac12a103275)

**2025-09-29**
**Shipment**: Claude Sonnet 4.5 — balanced model; best-in-class coding, agentic reasoning, 200k context. Pricing: $3 input / $15 output per million tokens. Becomes default on Claude.ai and Claude Code. Edge case unlocked: Coding agents shift from Opus-only to Sonnet-affordable; industry-standard benchmarks (SWE-bench Verified) now reachable at half Opus cost. Source: [Claude Sonnet 4.5 Released: New AI Model from Anthropic 2025](https://max-productive.ai/blog/claude-sonnet-4-5-announcement-2025/)

---

## Q3 2025 (July–September)

**2025-06-30**
**Shipment**: Citations API — Claude grounds answers in source documents with verbatim passage references. Generally available on Anthropic API and Google Cloud Vertex AI. Edge case unlocked: Knowledge-worker outputs now include audit trail (which sentences came from which sources); hallucination surface shrinks to within-document fabrication only. Source: [Introducing Citations on the Anthropic API](https://www.anthropic.com/news/introducing-citations-api)

---

## What Shipped in the Last 30 Days (Late April–May 2026)

Four shipments crossed the line between late April and May 2026:

1. **Claude Opus 4.7** (2026-04-16) — The inflection point for agentic vision. High-resolution images + native pixel coordinates unlock computer-use workflows that don't need intermediate coordinate transformation. Task budgets allow self-regulating spend per loop.

2. **MCP ecosystem 800-server milestone** (2026-04-22) — Table-stakes ecosystem size achieved. Gateway and authentication patterns now viable. Middleware vendors can build proxy layers.

3. **Prompt caching TTL tiers** (2026-05-02) — 5-minute and 1-hour caches ship with cost-optimized pricing. Semantic indexing now affordable across longer windows; real-time RAG shifts from latency-critical to batch-opportunistic.

4. **Managed Agents dreaming** (2026-05-06) — Agents review their own session history for patterns. No human annotation required. First step toward autonomous meta-learning in production systems.

The throughline: agentic systems graduate from asking *can Claude do this task?* to *can Claude regulate itself within budget and learn from experience?* Vision at native resolution, memory that self-improves, and spending that self-moderates signal maturity in the frontier.

---

## Key Sources

- [Anthropic News](https://www.anthropic.com/news)
- [Claude API Docs - Release Notes](https://platform.claude.com/docs/en/release-notes/overview)
- [Claude Help Center - Release Notes](https://support.claude.com/en/articles/12138966-release-notes)
- [Claude Code Docs - Changelog](https://code.claude.com/docs/en/changelog)
- [Model Context Protocol - Roadmap](https://modelcontextprotocol.io/development/roadmap)
