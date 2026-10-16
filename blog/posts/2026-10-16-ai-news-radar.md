---
title: AI News Radar, 16 October 2026
date: 2026-10-16
series: AI News Radar
summary: Four new models in three weeks, a round of model retirements that will break pinned configs, and research showing coding-agent benchmark scores are inflated by about a third. Covers 25 September to 16 October 2026.
---
What changed in AI coding tools between 25 September and 16 October 2026. Every item links to the page it comes from. Version numbers, prices and figures are copied from those pages.

## The three things worth knowing

- **Four new models in three weeks.** Claude Sonnet 5.5 (28 September), GPT-6.1 Sol (29 September, now the Codex default), Claude Haiku 5.5 (7 October) and Gemini 4 Argon (13 October, at half price until 30 November).
- **Model retirements will break configs that pin a model name.** GPT-5.5 left Codex for ChatGPT sign-ins on 14 October. GitHub Copilot drops Claude Opus 4.8, Claude Opus 5 and GPT-5.6 Terra on 16 November. Google now automatically routes `gemini-3.7-flash` and `gemini-3.5-flash` to newer models.
- **Benchmark scores for coding agents look inflated.** One audit found that about 34.4% of runs graded correct break the task requirements. Another found that the choice of harness mostly changes the bill, not the success rate.

## New models

- **Claude Sonnet 5.5** (28 September). `claude-sonnet-5-5`, $2 input and $10 output per million tokens, the same price as Sonnet 5. Anthropic reports 70.6% on Terminal-Bench 4.0, against 66.4% for Opus 5.5. If you run Sonnet with thinking off, you need to switch to the new `between_tools` setting. [Anthropic](https://www.anthropic.com/claude-sonnet-5-5)
- **GPT-6.1 Sol** (29 September). `gpt-6.1-sol`, $2 input and $10 output per million tokens for prompts up to 272K tokens. It became the default model in Codex CLI 0.159.1. An "ultrafast" tier followed on 8 October at 6 times the standard price. [OpenAI API changelog](https://developers.openai.com/api/docs/changelog)
- **Claude Haiku 5.5** (7 October). `claude-haiku-5-5`, $0.10 input and $0.50 output per million tokens up to 100K tokens. Anthropic positions it as a helper agent under Opus or Sonnet. It scores 39.2% on Terminal-Bench 4.0, where Haiku 4.5 scored 0.0%. [Anthropic](https://www.anthropic.com/claude-haiku-5-5)
- **Gemini 4 Argon** (13 October). `gemini-4-argon`, generally available on the paid API tier only. Context window of 1,048,576 tokens. $2 input and $10 output per million tokens until 30 November, then $4 and $20. [Gemini API changelog](https://ai.google.dev/gemini-api/docs/changelog)

## Retirements and breaking changes

- **GPT-5.5 is gone from Codex for ChatGPT sign-ins** (14 October). API-key sessions are not affected. OpenAI asks users to update saved settings, custom agents, scheduled tasks and scripts that still select `gpt-5.5`. [Codex changelog](https://learn.chatgpt.com/docs/changelog)
- **GitHub Copilot drops three models on 16 November**: Claude Opus 4.8, Claude Opus 5 and GPT-5.6 Terra. [GitHub changelog](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november)
- **Google reroutes old model names** (8 October). Requests to `gemini-3.7-flash` now go to `gemini-3.8-flash`, and `gemini-3.5-flash` goes to `gemini-3.6-flash`. Pinned names now reach a different model, so evaluation results and costs can shift. The `deep-research-pro-preview-12-2025` agent shuts down on 23 October. [Gemini API changelog](https://ai.google.dev/gemini-api/docs/changelog)
- **OpenAI API shutdowns announced.** `gpt-5.3-codex` and `gpt-5.1` shut down on 1 April 2027. Several GPT-4o and GPT-4.1 snapshots shut down on 14 January 2027. [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)
- **OpenCode removed session sharing** (v1.19.1, 15 October). Existing share links no longer work. Version 1.19.0 added `opencode upgrade --major` for the move to OpenCode 2. The project now lives at `anomalyco/opencode`. [GitHub releases](https://github.com/sst/opencode/releases)

## Claude Code and the Agent SDK

- **Security fixes for hooks and the sandbox.** v2.1.294 fixed hooks written as instructions, such as "Block commands that...", allowing what they should block. v2.1.296 fixed Bash permission checks auto-approving some commands that use `BASH_ARGV0`. v2.1.299 fixed sandboxed commands being able to write plugin code that then ran outside the sandbox. If you rely on hooks or the sandbox as guardrails, update. [Claude Code releases](https://github.com/anthropics/claude-code/releases)
- **Idle compaction** (v2.1.299, 14 October). A conversation over 200K tokens that sits idle for about 54 minutes is compacted before its one-hour prompt cache expires, so the next message does not reprocess all of it. [Claude Code releases](https://github.com/anthropics/claude-code/releases)
- **Claude Mods** (v2.1.287, 1 October). Plugins can now change deeper Claude Code behaviour, not just add tools. The same release can break some MCP server setups. The fix is to add `"bareElicitationCapability": true` to that server's config. [Claude Code releases](https://github.com/anthropics/claude-code/releases?page=2)
- **A prompt audit for older instructions** (v2.1.283, 25 September). `/doctor prompt-audit` checks CLAUDE.md files, skills, agents and commands for prompting patterns written for older models. [Claude Code releases](https://github.com/anthropics/claude-code/releases?page=2)
- **Agent SDK behaviour changes** (TypeScript v0.3.300, 14 October). Setting thinking to disabled now runs adaptive thinking on models that cannot turn thinking off. Input rewritten by hooks is now validated, and unknown keys are dropped. [Agent SDK releases](https://github.com/anthropics/claude-agent-sdk-typescript/releases)

## Codex and Google

- **Codex CLI 0.163.0** (15 October). You can send a follow-up while Codex is answering to steer it. Read-only tools now run in parallel. 0.162.0 (8 October) added tools for managed Git worktrees. [GitHub release](https://github.com/openai/codex/releases/tag/rust-v0.163.0)
- **Antigravity CLI gets Auto mode** (1.3.5, 14 October). It approves file edits and safe commands, and still asks before irreversible actions. Commands that would leave the sandbox are first checked by a separate agent. 1.3.6 (15 October) can run Claude Opus 5.5 and Sonnet 5.5 through a Google Cloud project. [GitHub release](https://github.com/google-antigravity/antigravity-cli/releases/tag/1.3.5)
- **Google's developer docs as an MCP server** (7 October). Docs for Cloud, Firebase, Android and more can be queried through an MCP server, a gcloud command or an agent skill. [Google Developers Blog](https://developers.googleblog.com/supercharge-your-development-with-the-google-developer-knowledge-api-ecosystem/)

## Other agents, IDEs and MCP

- **GitHub Copilot local sandboxing is generally available** (7 October). It limits file, network and credential access for commands Copilot runs, on Windows, macOS and Linux, at no extra cost. [GitHub changelog](https://github.blog/changelog/2026-10-07-local-sandboxing-for-github-copilot-now-generally-available/)
- **MCP Server Cards are final** (6 October). SEP-2127 defines a file that describes an MCP server before you connect: name, version, endpoints and supported protocol versions. A separate proposal sets two spec releases a year, in March and September, from March 2027. [MCP pull request](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2127)
- **MCP SDK 2.3.0 for Python and TypeScript** (2 October). In TypeScript, `Server.connect()` now rejects an instance that is already connected, so stateless HTTP servers must create one server per request. [TypeScript SDK releases](https://github.com/modelcontextprotocol/typescript-sdk/releases)
- **Pi reaches 1.0** (1 October). The fullscreen interface is now the default, and the system prompt shrank from about 5,300 to 3,300 tokens per request. Later 1.x releases renamed a provider and changed the extension API. [GitHub releases](https://github.com/earendil-works/pi/releases)
- **Cline reworks plugins and reads `.claude/skills`** (13 to 16 October). The SDK no longer runs plugins in-process, and the extension now finds skills in `.claude/skills`. Users who never chose a model will see a different default. [GitHub releases](https://github.com/cline/cline/releases)
- **Goose fixes an SSRF risk and removes MCP sampling** (v1.53.0, 2 October). [GitHub releases](https://github.com/block/goose/releases)

## Research

- **Coding benchmark scores are inflated by about a third.** TestJack writes extra tests for each agent run and keeps only those the reference fix passes. Across 6 model backends and 5 benchmarks, about 34.4% of runs graded correct broke the task requirements, and the solve rate fell from 50.6% to 33.2%. [arXiv 2610.10619](https://arxiv.org/abs/2610.10619)
- **The harness mostly decides the bill.** Five models ran through Claude Code, mini-SWE-agent and OpenCode on SWE-bench Verified. Claude Code and mini-SWE-agent came out equal within five points. Cost per task differed by up to 3 times. On a hard subset, rerunning the same harness changed as many outcomes as switching harness. [arXiv 2610.04433](https://arxiv.org/abs/2610.04433)
- **Auto-approve is the riskiest setting.** Across six harnesses and 2,500 trials, turning on auto-approve raised attack success from 29.2% to 95.6%. Command allowlists and denylists cut attacks at little cost to usefulness. [arXiv 2610.07639](https://arxiv.org/abs/2610.07639)
- **Overlapping skills quietly replace each other.** Nearly one in four installed skills sits next to another that does the same job. In one run in five, the other skill takes over, and the final reply names the skill it used in only 0.9% of those runs. [arXiv 2610.11647](https://arxiv.org/abs/2610.11647)
- **Agent reports leave out a lot.** Readers who saw only an agent's reports recovered 52.0% of the task state, against 92.7% with the full context. Failed attempts and open risks are what goes missing. [arXiv 2610.20003](https://arxiv.org/abs/2610.20003)
- **Turns drive cost, not tool output.** In 600 public agent runs, 98.6% of input tokens came from the prompt cache, and the number of turns explained 84% of the variance in cost. [arXiv 2610.15093](https://arxiv.org/abs/2610.15093)
