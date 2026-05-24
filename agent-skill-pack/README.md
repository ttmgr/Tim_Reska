# Agent Skill Pack for One Health Genomics — showcase

Public showcase for the agent skill pack that sits over the GenomicsForOneHealth pipelines. The pack lets LLM-assisted coding agents (Codex, Claude Code, Cursor, Continue) route a sequencing project to a documented workflow, validate inputs, build commands from declared templates, parse outputs, and write audit logs — without inventing commands or parameters.

## Source

Skill pack code (skills, hooks, eval runner) lives upstream in [`ttmgr/GenomicsForOneHealth`](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/agent_skills). This directory only hosts the marketing showcase (`index.html` + `styles.css`).

## Run locally

```bash
python3 -m http.server   # from repo root, then open http://localhost:8000/agent-skill-pack/
```

Works equivalently with `open index.html` — the page is fully self-contained apart from Google Fonts.

## Last refresh

2026-05-23.
