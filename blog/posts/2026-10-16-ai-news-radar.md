---
title: AI News Radar, 16 October 2026
date: 2026-10-16
series: AI News Radar
summary: Four models were released within three weeks, several model retirements affect configurations that pin a model name, and an audit indicates that coding-agent benchmark scores are inflated by about a third. Covers 25 September to 16 October 2026.
---
This edition summarizes changes to AI coding tools between 25 September and 16 October 2026. Each item links to its primary source, and version numbers, prices and figures are reproduced from those sources.

## Summary

Three developments characterize this period. First, four models were released within three weeks: Claude Sonnet 5.5 (28 September), GPT-6.1 Sol (29 September, now the default model in Codex), Claude Haiku 5.5 (7 October) and Gemini 4 Argon (13 October, offered at half price until 30 November). Second, several model retirements will break configurations that pin a model name. GPT-5.5 was withdrawn from Codex for ChatGPT sign-ins on 14 October, GitHub Copilot will remove Claude Opus 4.8, Claude Opus 5 and GPT-5.6 Terra on 16 November, and Google now automatically routes `gemini-3.7-flash` and `gemini-3.5-flash` to newer models. Third, recent studies question the reliability of coding-agent benchmarks. One audit found that about 34.4% of runs graded as correct violate the task requirements, while another found that the choice of harness mainly affects cost rather than success rate.

## New models

Anthropic released Claude Sonnet 5.5 (`claude-sonnet-5-5`) on 28 September at $2 input and $10 output per million tokens, unchanged from Sonnet 5 ([Anthropic](https://www.anthropic.com/claude-sonnet-5-5)). Anthropic reports a score of 70.6% on Terminal-Bench 4.0, compared with 66.4% for Opus 5.5. Deployments that run Sonnet with thinking disabled need to switch to the new `between_tools` setting. OpenAI released GPT-6.1 Sol (`gpt-6.1-sol`) on 29 September, priced at $2 input and $10 output per million tokens for prompts up to 272K tokens, and it became the default model in Codex CLI 0.159.1 ([OpenAI API changelog](https://developers.openai.com/api/docs/changelog)). An "ultrafast" tier followed on 8 October at six times the standard price.

Claude Haiku 5.5 (`claude-haiku-5-5`, 7 October) costs $0.10 input and $0.50 output per million tokens up to 100K tokens and is positioned by Anthropic as a helper agent under Opus or Sonnet ([Anthropic](https://www.anthropic.com/claude-haiku-5-5)). It scores 39.2% on Terminal-Bench 4.0, whereas Haiku 4.5 scored 0.0%. Google released Gemini 4 Argon (`gemini-4-argon`) on 13 October, generally available on the paid API tier only, with a context window of 1,048,576 tokens ([Gemini API changelog](https://ai.google.dev/gemini-api/docs/changelog)). Pricing is $2 input and $10 output per million tokens until 30 November, and $4 and $20 thereafter.

![**Figure 1:** *Terminal-Bench 4.0 scores of four Claude models as reported by Anthropic on the release pages of Claude Sonnet 5.5 and Claude Haiku 5.5. The scores have not been independently verified.*](figures/2026-10-16-ai-fig1.svg)

## Retirements and breaking changes

Since 14 October, GPT-5.5 is no longer available in Codex for ChatGPT sign-ins, while API-key sessions are unaffected ([Codex changelog](https://learn.chatgpt.com/docs/changelog)). OpenAI asks users to update saved settings, custom agents, scheduled tasks and scripts that still select `gpt-5.5`. GitHub Copilot will remove Claude Opus 4.8, Claude Opus 5 and GPT-5.6 Terra on 16 November ([GitHub changelog](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november)).

Since 8 October, Google routes requests for `gemini-3.7-flash` to `gemini-3.8-flash` and requests for `gemini-3.5-flash` to `gemini-3.6-flash` ([Gemini API changelog](https://ai.google.dev/gemini-api/docs/changelog)). Because pinned names now reach a different model, evaluation results and costs may shift. The `deep-research-pro-preview-12-2025` agent will shut down on 23 October. OpenAI has further announced that `gpt-5.3-codex` and `gpt-5.1` will shut down on 1 April 2027, and several GPT-4o and GPT-4.1 snapshots on 14 January 2027 ([OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)).

OpenCode removed session sharing in v1.19.1 (15 October), so existing share links no longer work ([GitHub releases](https://github.com/sst/opencode/releases)). The preceding version 1.19.0 added `opencode upgrade --major` for the migration to OpenCode 2, and the project now resides at `anomalyco/opencode`.

## Claude Code and the Agent SDK

Three Claude Code releases addressed security issues in hooks and the sandbox ([Claude Code releases](https://github.com/anthropics/claude-code/releases)). Version 2.1.294 fixed hooks written as instructions, such as "Block commands that...", which permitted the actions they were meant to block. Version 2.1.296 fixed Bash permission checks that auto-approved some commands using `BASH_ARGV0`, and v2.1.299 fixed sandboxed commands being able to write plugin code that subsequently ran outside the sandbox. Installations that rely on hooks or the sandbox as safeguards should therefore be updated.

Version 2.1.299 (14 October) also introduced idle compaction. A conversation exceeding 200K tokens that remains idle for about 54 minutes is compacted before its one-hour prompt cache expires, so that the next message does not reprocess the full context. Claude Mods (v2.1.287, 1 October) allow plugins to modify deeper Claude Code behavior rather than only adding tools ([Claude Code releases](https://github.com/anthropics/claude-code/releases?page=2)). The same release can break some Model Context Protocol (MCP) server setups, which is resolved by adding `"bareElicitationCapability": true` to the affected server's configuration. Version 2.1.283 (25 September) added `/doctor prompt-audit`, which checks CLAUDE.md files, skills, agents and commands for prompting patterns written for older models ([Claude Code releases](https://github.com/anthropics/claude-code/releases?page=2)).

In the TypeScript Agent SDK (v0.3.300, 14 October), disabling thinking now runs adaptive thinking on models that cannot turn thinking off, and input rewritten by hooks is now validated, with unknown keys dropped ([Agent SDK releases](https://github.com/anthropics/claude-agent-sdk-typescript/releases)).

## Codex and Google

Codex CLI 0.163.0 (15 October) accepts follow-up messages while Codex is responding, which allows users to steer it, and runs read-only tools in parallel ([GitHub release](https://github.com/openai/codex/releases/tag/rust-v0.163.0)). The preceding version 0.162.0 (8 October) added tools for managed Git worktrees. Antigravity CLI 1.3.5 (14 October) introduced an Auto mode that approves file edits and safe commands but still requests confirmation before irreversible actions, while commands that would leave the sandbox are first checked by a separate agent ([GitHub release](https://github.com/google-antigravity/antigravity-cli/releases/tag/1.3.5)). Version 1.3.6 (15 October) can run Claude Opus 5.5 and Sonnet 5.5 through a Google Cloud project. Since 7 October, documentation for Google Cloud, Firebase, Android and further products can be queried through an MCP server, a gcloud command or an agent skill ([Google Developers Blog](https://developers.googleblog.com/supercharge-your-development-with-the-google-developer-knowledge-api-ecosystem/)).

## Other agents, IDEs and MCP

Local sandboxing for GitHub Copilot became generally available on 7 October. It restricts file, network and credential access for commands executed by Copilot on Windows, macOS and Linux, at no additional cost ([GitHub changelog](https://github.blog/changelog/2026-10-07-local-sandboxing-for-github-copilot-now-generally-available/)). In the MCP ecosystem, Server Cards were finalized on 6 October. SEP-2127 defines a file that describes an MCP server before a client connects, including its name, version, endpoints and supported protocol versions ([MCP pull request](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2127)). A separate proposal schedules two specification releases per year, in March and September, from March 2027. MCP SDK 2.3.0 for Python and TypeScript (2 October) changes `Server.connect()` in TypeScript to reject an instance that is already connected, so stateless HTTP servers must create one server per request ([TypeScript SDK releases](https://github.com/modelcontextprotocol/typescript-sdk/releases)).

Among other agents, Pi reached version 1.0 on 1 October, with the fullscreen interface as the default and a system prompt reduced from about 5,300 to 3,300 tokens per request ([GitHub releases](https://github.com/earendil-works/pi/releases)). Subsequent 1.x releases renamed a provider and changed the extension API. Between 13 and 16 October, Cline reworked its plugin system so that the SDK no longer runs plugins in-process, and the extension now discovers skills in `.claude/skills` ([GitHub releases](https://github.com/cline/cline/releases)). Users who never selected a model will encounter a different default. Goose v1.53.0 (2 October) fixed a server-side request forgery (SSRF) risk and removed MCP sampling ([GitHub releases](https://github.com/block/goose/releases)).

## Research

Several preprints question how coding agents are evaluated. TestJack generates additional tests for each agent run and retains only those that the reference fix passes. Across 6 model backends and 5 benchmarks, about 34.4% of runs graded as correct violated the task requirements, and the solve rate decreased from 50.6% to 33.2% (Yao et al. 2026; [arXiv 2610.10619](https://arxiv.org/abs/2610.10619)). A second study ran five models through Claude Code, mini-SWE-agent and OpenCode on SWE-bench Verified (Liu and Han 2026; [arXiv 2610.04433](https://arxiv.org/abs/2610.04433)). Claude Code and mini-SWE-agent performed equally within five points, whereas cost per task differed by up to threefold. On a hard subset, rerunning the same harness changed as many outcomes as switching harness.

Two studies address safety. Across six harnesses and 2,500 trials, enabling auto-approve raised attack success from 29.2% to 95.6%, whereas command allowlists and denylists reduced attacks at little cost to usefulness (Zhu et al. 2026; [arXiv 2610.07639](https://arxiv.org/abs/2610.07639)). Overlapping skills can also replace each other without notice. Nearly one in four installed skills coexists with another that serves the same function, the other skill takes over in one run in five, and the final response names the skill actually used in only 0.9% of those runs (Yan et al. 2026; [arXiv 2610.11647](https://arxiv.org/abs/2610.11647)).

Two further studies address reporting and cost. Readers with access only to an agent's reports recovered 52.0% of the task state, compared with 92.7% with the full context, and the missing information concerned failed attempts and open risks (Xu et al. 2026; [arXiv 2610.20003](https://arxiv.org/abs/2610.20003)). In 600 public agent runs, 98.6% of input tokens were served from the prompt cache, and the number of turns explained 84% of the variance in cost (Kumar and Pandey 2026; [arXiv 2610.15093](https://arxiv.org/abs/2610.15093)).

![**Figure 2:** *Effects reported in three studies of coding agents. Solve rate across coding benchmarks under the original grading and with additional tests generated by TestJack (Yao et al. 2026); attack success with auto-approve disabled and enabled (Zhu et al. 2026); share of task state recovered by readers given only the agent's reports or the full context (Xu et al. 2026). In each row, grey marks the first named condition and green the second.*](figures/2026-10-16-ai-fig2.svg)

## References

- Kumar, Pramod, and Raj Kumar Pandey. 2026. 'TurnCost: Turns, Not Observations: Cache-Aware Loop Engineering for Coding Agents'. *arXiv* (preprint) 2610.15093. https://arxiv.org/abs/2610.15093.
- Liu, Yangze, and Zhongyi Han. 2026. 'What Does a Harness Buy? Tokens, Mostly'. *arXiv* (preprint) 2610.04433. https://arxiv.org/abs/2610.04433.
- Xu, Guoyang, Rui Zhang, Xiuyu Wu, and Hao Chen. 2026. 'What Coding Agents Leave Unsaid: Measuring Task-State Gaps Between Execution and Reports'. *arXiv* (preprint) 2610.20003. https://arxiv.org/abs/2610.20003.
- Yan, Chaoliang, Zihao Xu, Yuekang Li, Shangzhi Xu, Yi Liu, Gelei Deng, and Siqi Ma. 2026. 'One Skill Too Many: How Co-Installed Skills Conflict in Coding Agents'. *arXiv* (preprint) 2610.11647. https://arxiv.org/abs/2610.11647.
- Yao, Shuangjie, Hao Wang, Koushik Sen, Simin Chen, Baishakhi Ray, and Dawn Song. 2026. 'TestJack: Should you trust the results in coding benchmarks? Agentic Coding Benchmarks Auditing via Evaluator Evolution'. *arXiv* (preprint) 2610.10619. https://arxiv.org/abs/2610.10619.
- Zhu, Zhengyang, Liming Huang, Runmin Ji, Mingxi Ye, Zihan Zhou, Hanyang Guo, Jingwen Wu, et al. 2026. 'HarnessSecurity-Bench: Do Security Mechanisms Really Protect Coding Agent Harnesses?' *arXiv* (preprint) 2610.07639. https://arxiv.org/abs/2610.07639.

### Software, models and release notes

- Anthropic. 2026. Claude Agent SDK for TypeScript, release notes. https://github.com/anthropics/claude-agent-sdk-typescript/releases. Accessed 16 October 2026.
- Anthropic. 2026. Claude Code release notes. https://github.com/anthropics/claude-code/releases. Accessed 16 October 2026.
- Anthropic. 2026. Claude Haiku 5.5. https://www.anthropic.com/claude-haiku-5-5. Accessed 16 October 2026.
- Anthropic. 2026. Claude Sonnet 5.5. https://www.anthropic.com/claude-sonnet-5-5. Accessed 16 October 2026.
- Block. 2026. Goose release notes. https://github.com/block/goose/releases. Accessed 16 October 2026.
- Cline. 2026. Release notes. https://github.com/cline/cline/releases. Accessed 16 October 2026.
- Earendil. 2026. Pi release notes. https://github.com/earendil-works/pi/releases. Accessed 16 October 2026.
- GitHub. 2026. Local sandboxing for GitHub Copilot now generally available. https://github.blog/changelog/2026-10-07-local-sandboxing-for-github-copilot-now-generally-available/. Accessed 16 October 2026.
- GitHub. 2026. Upcoming deprecation of selected GitHub Copilot models. https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november. Accessed 16 October 2026.
- Google. 2026. Antigravity CLI release 1.3.5. https://github.com/google-antigravity/antigravity-cli/releases/tag/1.3.5. Accessed 16 October 2026.
- Google. 2026. Gemini API changelog. https://ai.google.dev/gemini-api/docs/changelog. Accessed 16 October 2026.
- Google. 2026. Google Developer Knowledge API ecosystem, Google Developers Blog. https://developers.googleblog.com/supercharge-your-development-with-the-google-developer-knowledge-api-ecosystem/. Accessed 16 October 2026.
- Model Context Protocol. 2026. SEP-2127, MCP Server Cards. https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2127. Accessed 16 October 2026.
- Model Context Protocol. 2026. TypeScript SDK release notes. https://github.com/modelcontextprotocol/typescript-sdk/releases. Accessed 16 October 2026.
- OpenAI. 2026. API changelog. https://developers.openai.com/api/docs/changelog. Accessed 16 October 2026.
- OpenAI. 2026. API deprecations. https://developers.openai.com/api/docs/deprecations. Accessed 16 October 2026.
- OpenAI. 2026. Codex changelog. https://learn.chatgpt.com/docs/changelog. Accessed 16 October 2026.
- OpenAI. 2026. Codex CLI release 0.163.0. https://github.com/openai/codex/releases/tag/rust-v0.163.0. Accessed 16 October 2026.
- OpenCode. 2026. Release notes. https://github.com/sst/opencode/releases. Accessed 16 October 2026.
