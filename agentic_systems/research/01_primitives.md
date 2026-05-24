# Agentic Frontier Primitives: Complete Inventory

A frontier primer documenting every Claude Code and Claude agentic primitive currently available, keyed to the edge case each one unlocks.

## Composition Primitives

**Skills**
- What it is: Reusable agent instructions and commands packaged with YAML frontmatter that Claude can invoke on demand or load automatically based on heuristics.
- Edge case it unlocks: Run domain-specific pipelines without reproducing custom logic in every session—clinicians invoke `/15-clinical-evidence-research` to validate ICD-10 codes and fetch biomarker ranges without hand-crafting the query each time.
- Source: [Extend Claude with skills](https://docs.anthropic.com/en/docs/claude-code/slash-commands)

**Subagents (TaskCreate + Parallel Execution)**
- What it is: Spawn isolated child agents with custom system prompts, independent tool access, and separate permission scopes; run them sequentially or in parallel and collect results back to the parent context.
- Edge case it unlocks: Investigate 3 loosely-coupled modules (auth, DB, API) in parallel with separate subagents while the parent orchestrates results—critical for scaling research beyond a single context window and hitting code coverage you'd miss in serial.
- Source: [Create custom subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)

**Model Context Protocol (MCP)**
- What it is: Open-source standard for AI tools to connect to external systems (issue trackers, monitoring dashboards, databases, APIs) through a standardized interface, with lazy tool loading via tool search.
- Edge case it unlocks: Connect Claude directly to a Jira instance or your Prometheus dashboard without copy-paste—Claude discovers and calls tools on the fly; tool search defers schema loading until needed, keeping context small even with 100+ tools available.
- Source: [What is the Model Context Protocol (MCP)?](https://docs.anthropic.com/en/docs/build-with-claude/mcp)

**Hooks (19 lifecycle points)**
- What it is: Deterministic shell/HTTP/MCP/prompt-based handlers that fire at session-level, turn-level, tool-level, and file-change events; can block actions, inject context, or return structured decisions.
- Edge case it unlocks: Enforce project rules without AI judgment: auto-deny `rm -rf /`, validate every Edit against a linter before it touches disk (PreToolUse), send Slack notifications when subagents fail (SubagentStop), or auto-compact context when approaching limits (PreCompact).
- Source: [Automate workflows with hooks](https://code.claude.com/docs/en/hooks-guide), [Hooks reference](https://code.claude.com/docs/en/hooks)

**Plugins**
- What it is: Packaged extensions (skills, agents, hooks, MCP servers) installable from marketplaces and configurable per-user or per-project via settings.
- Edge case it unlocks: Ship a team's domain-specific logic (e.g., compliance checklist, build pipeline) once; all teammates install the plugin and get the same behavior without duplicating setup.
- Source: [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings)

## Cost and Context Primitives

**Prompt Caching**
- What it is: Cache portions of your prompt (with a 5-minute or 1-hour TTL) so repeated API calls reuse the cached prefix at 10% input cost; automatic caching on the last block or manual per-block placement.
- Edge case it unlocks: Run 50 document reviews with a shared 50KB system prompt + codebase context—after the first call, the next 49 cost 10% input on the shared prefix, paying for itself after just one cache read at 1-hour TTL (2x write cost).
- Source: [Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

**Message Batches API**
- What it is: Queue up to hundreds of independent API calls, submit once, get 50% cost discount on all of them; results available within 1 hour and accessible for 29 days.
- Edge case it unlocks: Process 1000 patient risk assessments overnight—batch them all at 50% cost, let Anthropic infrastructure parallelize the work, and fetch results in the morning without running your own queue.
- Source: [Batch processing](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing)

**Context Compaction**
- What it is: Server-side summarization that automatically condenses conversation history when approaching context limits, preserving CLAUDE.md and auto-memory across the boundary.
- Edge case it unlocks: Run week-long coding marathons on a single session without context window cliffs—at 95% capacity, Anthropic's servers summarize old turns and re-inject your CLAUDE.md, letting you continue indefinitely.
- Source: [How Claude remembers your project](https://docs.anthropic.com/en/docs/claude-code/memory)

**Files API (Beta)**
- What it is: Upload and store documents (PDFs, CSVs, spreadsheets) once, reuse across multiple API calls without re-uploading; PDFs auto-convert to text + image dual representation for table/chart understanding.
- Edge case it unlocks: Hand off a 500-page regulatory document once; Claude can cite exact page numbers and table locations across 20 separate analysis requests without you re-uploading the PDF each time.
- Source: [Files API](https://docs.anthropic.com/en/docs/build-with-claude/files), [PDF support](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)

**Session Memory (Auto-Memory + CLAUDE.md)**
- What it is: CLAUDE.md files (human-written persistent instructions) + auto-memory (Claude's self-written notes on build commands, architecture, style preferences) both survive context compaction.
- Edge case it unlocks: Hand off a project to a teammate; their session reads your CLAUDE.md and auto-memory notes, recovering architecture insights and debugging tricks from 5 sessions ago without asking you to recap.
- Source: [How Claude remembers your project](https://docs.anthropic.com/en/docs/claude-code/memory)

## Execution and Isolation Primitives

**Git Worktrees**
- What it is: Create isolated working directories with separate branch and file state but shared repository history; each worktree gets its own Claude session context.
- Edge case it unlocks: Work on 3 feature branches in parallel without Claude accidentally mixing file edits—each worktree is a clean filesystem sandbox that auto-cleanup on exit unless you saved changes.
- Source: [Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows)

**Background Tasks (Ctrl+B + SubagentStop Hooks)**
- What it is: Move a running subagent to the background; it continues autonomously with pre-granted permissions, auto-denying any new permission requests, while you continue foreground work.
- Edge case it unlocks: Start a 30-minute integration test suite in the background; keep coding in the foreground; when tests complete, a SubagentStop hook notification alerts you without blocking.
- Source: [Create custom subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)

**Worktree Hooks (WorktreeCreate + WorktreeRemove)**
- What it is: Custom handlers that fire when a worktree is created or removed; support non-git VCS (Perforce, SVN, Mercurial) via hook commands.
- Edge case it unlocks: Enforce company policy: on WorktreeCreate, automatically provision cloud credentials scoped to that branch; on WorktreeRemove, revoke access and archive logs.
- Source: [Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows)

**Sandboxed Bash (--sandbox flag)**
- What it is: Execute shell commands in a filesystem and network-isolated container with granular permission controls; Claude Code runs safely on untrusted code without human approval for every tool call.
- Edge case it unlocks: Let Claude run arbitrary bash in untrusted repos without permission prompts—the sandbox prevents access to your SSH keys or network; use `permissionMode: "dontAsk"` for unattended CI.
- Source: [Security](https://docs.anthropic.com/en/docs/claude-code/security)

**Permissions and Deny Rules (permissions.deny)**
- What it is: Granular file/tool deny lists in settings.json that prevent Claude from discovering or reading sensitive files (`.env`, `*.pem`, `credentials.json`); patterns use glob/regex matchers.
- Edge case it unlocks: Safely run Claude Code on repos with secrets; deny `.env*` and `*secrets*` to prevent accidental credential leakage into chat or tool arguments.
- Source: [Configure permissions](https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-permissions)

## Reasoning and Output Primitives

**Extended Thinking**
- What it is: Claude's internal reasoning step before responding; models like Opus 4.6 use adaptive thinking, deciding dynamically when and how much to think based on the effort parameter and task complexity.
- Edge case it unlocks: For complex medical underwriting decisions, enable extended thinking so Claude reasons through differential diagnoses and risk factors privately before writing the assessment—no training wheels, pure structured thinking.
- Source: [Building with extended thinking](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)

**Structured Output (JSON Schema Validation)**
- What it is: Guarantee that Claude's response conforms to a JSON schema; the model commits to the schema at request time, so outputs are always parseable without fallback regex.
- Edge case it unlocks: Build a reliable data ingestion pipeline that deserializes Claude output directly into a database table—no "if parsing fails then retry" logic; the API promises valid JSON.
- Source: [Increase output consistency](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/increase-consistency)

**Citations (Per-Block Attribution)**
- What it is: Each text block can include citations anchored to source document locations (page ranges for PDFs, character ranges for text, block indices for custom content).
- Edge case it unlocks: Build a medical evidence system where every clinical claim is automatically backed by a clickable citation to the source—no human fact-checking needed if you enforce citations on all model output.
- Source: [Citations](https://docs.anthropic.com/en/docs/build-with-claude/citations)

**Prefill and Response Control**
- What it is: Pre-populate part of Claude's response and control the output format (JSON object, code block, XML) before the model starts generating.
- Edge case it unlocks: Force Claude to output valid JSON by prefilling the opening brace; or start a code block to steer the model toward code-first answers.
- Source: [Prefill Claude's response](https://docs.anthropic.com/en/docs/prefill-claudes-response)

## Capability Primitives

**Vision (High-Resolution Images)**
- What it is: Claude Opus 4.7 supports up to 2576px on the long edge; vision is built into the Messages API, supports screenshots, diagrams, and any standard image format.
- Edge case it unlocks: Have Claude debug a UI bug by analyzing a screenshot of your design system violation; or extract tables from a scanned PDF without OCR—the vision understands layout and visual hierarchy.
- Source: [Vision](https://docs.anthropic.com/en/docs/build-with-claude/vision)

**Computer Use Tool (Beta)**
- What it is: Claude controls your desktop—mouse, keyboard, screenshots, scroll—as a tool in the tool_use loop; works with vision to understand what's on screen before acting.
- Edge case it unlocks: Automate a manual SaaS workflow (e.g., bulk upload to Salesforce) by having Claude click buttons and fill forms instead of writing a Selenium script.
- Source: [Computer use tool](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)

**Tool Use with Interleaved Thinking**
- What it is: Claude can think between tool calls—request a tool, you return the result, Claude reflects before deciding the next action.
- Edge case it unlocks: Debugging becomes interactive reasoning: Claude reads a stack trace, thinks about it, requests the full function, thinks about that result, then pinpoints the bug instead of guessing on the first try.
- Source: [Tool use with Claude](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview)

## Session-Layer Primitives

**Plan Mode (Shift+Tab)**
- What it is: Toggle into read-only mode where Claude describes changes but does not touch disk until you approve; VS Code renders the plan as markdown for inline feedback before committing.
- Edge case it unlocks: For high-stakes refactors, review Claude's 10-file change in plan mode, add inline comments ("keep this comment"), then have Claude execute the refined plan.
- Source: [Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows)

**Tool Search (Deferred MCP Loading)**
- What it is: Tool names load at session start; full schemas are deferred and fetched only when Claude searches for a tool or when `alwaysLoad: true` is set in config.
- Edge case it unlocks: Connect 200+ MCP tools without blowing up context—only the tools Claude actually needs are hydrated; you stay at 80% context utilization instead of maxing out on schema overhead.
- Source: [Connect Claude Code to tools via MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)

**SessionStart, Stop, StopFailure Hooks**
- What it is: Fire at session lifecycle boundaries (start, stop on success, stop on API error); can be used for cleanup, logging, or status aggregation.
- Edge case it unlocks: On Stop, emit a summary of all commits made in the session and auto-push to origin; or on StopFailure with `authentication_failed` matcher, auto-rotate credentials.
- Source: [Hooks reference](https://code.claude.com/docs/en/hooks)

**Markdown Notation File (.claude/settings.json, .claude/settings.local.json, ~/.claude/settings.json)**
- What it is: Three-tier configuration (user-global, project-global, project-local-gitignored) for hooks, permissions, MCP servers, plugins, and Claude Code behavior.
- Edge case it unlocks: Ship a project with `.claude/settings.json` defining project-specific hooks and MCP servers; teammates clone the repo and auto-get the same agent setup without manual installation.
- Source: [Claude Code settings](https://docs.anthropic.com/en/docs/claude-code/settings)

**Token Counting API**
- What it is: Synchronous API call to count tokens in a message before sending, for cost estimation and context window planning.
- Edge case it unlocks: Build a guardrail: before processing a 500MB dataset, ask the API "how many tokens for this?" and bail if it exceeds your budget instead of discovering the cost after the fact.
- Source: [API overview](https://docs.anthropic.com/en/api/getting-started)

---

## Primitives Tim's Existing Skills Do Not Yet Use

The following primitives are mature but not yet integrated into the five orchestrator skills (49-multi-agent-science, 42-askeras-ai-enablement, 48-dd-multi-agent, 46-slides-consulting, 61-report):

1. **Computer Use** — No skill automates desktop workflows; could unlock SaaS bulk-upload or UI test automation in a future orchestrator.

2. **Extended Thinking (Explicitly Tuned)** — Skills use the model's default thinking; none explicitly set `budget_tokens` or `type: "native"` to customize thinking depth per domain.

3. **Tool Search (Deferred MCP)** — All 5 skills pre-load their MCP servers; none rely on tool search to keep context tight across 50+ available tools.

4. **Sessions API (Managed Agents)** — Skills run in-process; none deploy as stateful Managed Agents on anthropic-managed infrastructure for persistence across Tim's workstation restarts.

5. **Scheduled Routines (Cron)** — No skill configures recurring agent execution (e.g., "run the clinical-evidence-research validator every Monday 6am").

6. **Permission Hooks (Granular Denial)** — Skills trust their parent context; none define deny rules to prevent accidental credential leakage from sub-agent tool calls.

7. **Citations + Structured Output** — 19-paper uses plain text bibliography; could emit JSON citations keyed to Files API references for downstream rendering.

8. **Batch Processing + Caching Stacking** — No skill combines Message Batches API (50% discount) with prompt caching (10% on cache hit) for multi-hundred-request workflows.

9. **Compaction Hooks (PreCompact + PostCompact)** — Skills assume unbounded context; could inject checkpoints before compaction fires to preserve intermediate results (e.g., cached regression models).

10. **Computer Use + MCP** — No skill coordinates desktop automation (e.g., clicking through a compliance form) with live data sources (Jira, Slack) fetched via MCP.
