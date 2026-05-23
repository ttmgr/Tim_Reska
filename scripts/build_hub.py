#!/usr/bin/env python3
"""Generate docs/HUB.html — auto-derived project dashboard.

A *narrative* layer for the repo: project status, what's currently canonical,
what's superseded, the temporal waves of work, the named concepts, the runnable
scripts, who's contributed. Distinct from INDEX.html (structural file graph) —
HUB.html answers "what's the state of this project?", INDEX.html answers "where
in the code is X?".

Designed to be **project-agnostic** so it can run unchanged in any repo. All
signals are inferred from git + filesystem + a few well-known files (README,
CONTEXT.md, CLAUDE.md). For things no scanner can know (which pitch deck counts
as "canonical" vs an older draft, what the project's headline status pill
should say), an optional docs/hub.yaml provides overrides — absent it,
sensible heuristics fill in.

Usage:
    python3 scripts/build_hub.py            # write docs/HUB.html
    python3 scripts/build_hub.py --check    # exit 1 if stale
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # used only if docs/hub.yaml present
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "HUB.html"
OVERRIDES = ROOT / "docs" / "hub.yaml"
README = ROOT / "README.md"
CONTEXT = ROOT / "CONTEXT.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
INDEX_HTML = ROOT / "docs" / "INDEX.html"
ADR_DIR = ROOT / "docs" / "adr"
PLANS_DIR = ROOT / "docs" / "plans"
SCRIPTS_DIR = ROOT / "scripts"

# Project-specific palette: mirrors assets/css/tokens.css so the HUB sits
# visually alongside academy/, ebola/, hanta/, etc. (warm-terracotta on warm
# off-white). The skill's authoritative copy in ~/.claude/skills/79-project-hub/
# stays vanilla Earth+Sky; only this project's copy is tuned.
# Green is preserved for "ok / current / latest-wave" semantics — universal
# enough to read correctly even on a terracotta-heavy page.
PALETTE = {
    "air":      "#9A5A2E",  # --accent-text — primary link / nav hue (darker terracotta)
    "water":    "#2D8659",  # forest green — "latest wave" + ok semantics (kept non-terracotta on purpose)
    "thesis":   "#C4794A",  # --accent — earlier-wave terracotta dots, .card .id.sc
    "ink":      "#1A1A2E",  # --text
    "muted":    "#6B6A73",  # --text-secondary
    "bg":       "#FAF9F7",  # --bg (warm off-white)
    "bg_soft":  "#F0EDEA",  # --tag-bg (warmer pale for surfaces)
    "border":   "#E8E6E1",  # --border
    "border_2": "#D0CEC8",  # --border-strong
    "ok":       "#2D8659",  # ACTIVE status pill
    "warn":     "#C4794A",  # IN PROGRESS / warning — site accent
    "dim":      "#B0AFA8",  # warm grey for DORMANT
}


# --- generic helpers ------------------------------------------------------

def git(*args: str, default: str = "") -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return default


def load_overrides() -> dict:
    if not (OVERRIDES.exists() and HAS_YAML):
        return {}
    try:
        return yaml.safe_load(OVERRIDES.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


# --- section derivers -----------------------------------------------------

def derive_project_name(o: dict) -> str:
    if o.get("name"):
        return o["name"]
    if README.exists():
        for line in README.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^#\s+(.+)$", line.strip())
            if m:
                return m.group(1).strip()
    return ROOT.name


def derive_tagline(o: dict) -> str:
    if o.get("tagline"):
        return o["tagline"]
    if not README.exists():
        return ""
    text = README.read_text(encoding="utf-8")
    # Prefer the first non-heading paragraph after a "Status" / "About" / etc heading.
    paras = re.split(r"\n\s*\n", text)
    for p in paras:
        p = p.strip()
        if not p or p.startswith("#") or p.startswith("```") or p.startswith("|"):
            continue
        # strip markdown emphasis
        return re.sub(r"[*_`]", "", p.split("\n")[0]).strip()
    return ""


def derive_status(o: dict) -> dict:
    """{pill, reason, color}. Override via hub.yaml: status / status_reason."""
    if o.get("status"):
        return {
            "pill": o["status"],
            "reason": o.get("status_reason", ""),
            "color": o.get("status_color", PALETTE["ok"]),
        }
    last_commit_ts = git("log", "-1", "--format=%ct")
    uncommitted = len([ln for ln in git("status", "-s").splitlines() if ln.strip()])
    if not last_commit_ts:
        return {"pill": "EMPTY", "reason": "no commits", "color": PALETTE["dim"]}
    age_h = (datetime.now(timezone.utc).timestamp() - int(last_commit_ts)) / 3600
    if uncommitted > 30 or age_h < 24:
        pill, color = "ACTIVE", PALETTE["ok"]
    elif age_h < 24 * 7:
        pill, color = "IN PROGRESS", PALETTE["air"]
    elif age_h < 24 * 30:
        pill, color = "IDLE", PALETTE["warn"]
    else:
        pill, color = "DORMANT", PALETTE["dim"]
    reason_bits = [f"last commit {fmt_age(age_h)}"]
    if uncommitted:
        reason_bits.append(f"{uncommitted} uncommitted")
    return {"pill": pill, "reason": " · ".join(reason_bits), "color": color}


def fmt_age(hours: float) -> str:
    if hours < 1:   return f"{int(hours * 60)} min ago"
    if hours < 48:  return f"{int(hours)} h ago"
    if hours < 24 * 60: return f"{int(hours / 24)} d ago"
    return f"{int(hours / 24 / 30)} mo ago"


def derive_waves(o: dict) -> list[dict]:
    """List of {label, sub, count, color}. Override via hub.yaml: waves: [...]."""
    if o.get("waves"):
        return o["waves"]
    # Heuristic 1: commit-message prefixes like "#3 Split ..." → one wave per prefix.
    log = git("log", "--format=%s", "--reverse")
    prefix_re = re.compile(r"^(#\d+)\s+(.{0,40})")
    by_prefix: dict[str, dict] = {}
    for line in log.splitlines():
        m = prefix_re.match(line.strip())
        if not m:
            continue
        key = m.group(1)
        by_prefix.setdefault(key, {"label": key, "sub": m.group(2).strip(), "count": 0})
        by_prefix[key]["count"] += 1
    if len(by_prefix) >= 3:
        waves = list(by_prefix.values())
        for i, w in enumerate(waves):
            w["color"] = PALETTE["ok"] if i == len(waves) - 1 else PALETTE["thesis"]
        return waves
    # Heuristic 2: cluster by year-month, label "Mon YYYY".
    months = Counter()
    for ts in git("log", "--format=%ct").splitlines():
        try:
            d = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            months[d.strftime("%Y-%m")] += 1
        except ValueError:
            continue
    waves = []
    for i, (m, c) in enumerate(sorted(months.items())):
        waves.append({
            "label": f"W{i+1}",
            "sub": datetime.strptime(m, "%Y-%m").strftime("%b %Y").lower(),
            "count": c,
            "color": PALETTE["ok"] if i == len(months) - 1 else PALETTE["thesis"],
        })
    return waves[-9:]  # cap at 9, matches foodsafety layout


def derive_concepts(o: dict) -> list[dict]:
    """Parse `- **Name** — description` bullets out of CONTEXT.md (or override)."""
    if o.get("concepts"):
        return o["concepts"]
    if not CONTEXT.exists():
        return []
    text = CONTEXT.read_text(encoding="utf-8")
    concepts = []
    pat = re.compile(r"^- \*\*(.+?)\*\*\s*[—\-]\s*(.+)$", re.MULTILINE)
    for m in pat.finditer(text):
        name = m.group(1).strip()
        # bullet can wrap onto continuation lines; grab them until the next "- " or blank
        start = m.end()
        rest = text[start:].split("\n- ", 1)[0].strip()
        full_desc = (m.group(2).strip() + " " + rest).strip()
        # keep it tight
        full_desc = re.sub(r"\s+", " ", full_desc).strip()
        if len(full_desc) > 220:
            full_desc = full_desc[:217].rsplit(" ", 1)[0] + "…"
        concepts.append({"name": name, "desc": full_desc})
    return concepts


def derive_scripts(o: dict) -> list[dict]:
    """Runnable entry points: scripts/, package.json `scripts:`, Makefile targets."""
    if o.get("scripts"):
        return o["scripts"]
    items: list[dict] = []
    if SCRIPTS_DIR.is_dir():
        for p in sorted(SCRIPTS_DIR.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                rel = p.relative_to(ROOT).as_posix()
                items.append({"name": p.name, "path": rel, "kind": "script"})
    pkg = ROOT / "website" / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            for k, v in (data.get("scripts") or {}).items():
                items.append({"name": f"npm run {k}", "path": f"website/ · {v}",
                              "kind": "npm"})
        except Exception:
            pass
    mf = ROOT / "Makefile"
    if mf.exists():
        for m in re.finditer(r"^([A-Za-z0-9_\-]+):", mf.read_text(encoding="utf-8"), re.M):
            items.append({"name": f"make {m.group(1)}", "path": "Makefile",
                          "kind": "make"})
    return items


def derive_canonical(o: dict) -> list[dict]:
    """What's authoritative right now. Without overrides, picks newest of each
    common artifact type. Override via hub.yaml: canonical_refs: [{name, path, desc}]."""
    if o.get("canonical_refs"):
        return o["canonical_refs"]
    items: list[dict] = []
    if README.exists():
        items.append({"name": "README", "path": "README.md",
                      "desc": "Project README — first-read entry point."})
    if CLAUDE_MD.exists():
        items.append({"name": "CLAUDE.md", "path": "CLAUDE.md",
                      "desc": "Agent rules + project conventions (NEVER / IMMER)."})
    if CONTEXT.exists():
        items.append({"name": "CONTEXT.md", "path": "CONTEXT.md",
                      "desc": "Domain vocabulary — the words this project uses."})
    if (ROOT / "docs" / "INDEX.md").exists():
        items.append({"name": "INDEX.md", "path": "docs/INDEX.md",
                      "desc": "Repo node map — code structure by area."})
    # Newest PDF / DOCX / HTML in each first-level docs/ subdir
    docs = ROOT / "docs"
    if docs.is_dir():
        for sub in sorted(docs.iterdir()):
            if not sub.is_dir() or sub.name in {"adr", "plans"}:
                continue
            candidates = [p for p in sub.rglob("*")
                          if p.is_file() and p.suffix in {".pdf", ".html", ".md", ".docx"}
                          and "_orig" not in p.parts and "_old" not in p.parts]
            if not candidates:
                continue
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            items.append({
                "name": sub.name,
                "path": newest.relative_to(ROOT).as_posix(),
                "desc": f"Most-recent {newest.suffix.lstrip('.').upper()} in docs/{sub.name}/",
            })
    return items


def derive_collaborators(o: dict) -> list[dict]:
    """`git shortlog -sn` → contributors. Override via hub.yaml: collaborators."""
    if o.get("collaborators"):
        return o["collaborators"]
    raw = git("shortlog", "-sn", "HEAD")
    out = []
    for line in raw.splitlines():
        m = re.match(r"\s*(\d+)\s+(.+)$", line)
        if not m:
            continue
        out.append({"name": m.group(2).strip(), "count": int(m.group(1))})
    return out


def derive_superseded() -> list[dict]:
    """Folders matching common 'kept for provenance' patterns."""
    patterns = [
        re.compile(r"(^|/)_orig($|/)"),
        re.compile(r"(^|/)_old($|/)"),
        re.compile(r"(^|/)_v\d+($|/)"),
        re.compile(r"(^|/).*backup.*", re.IGNORECASE),
        re.compile(r"(^|/).*\.archived[-_].*"),
    ]
    seen: set[str] = set()
    items: list[dict] = []
    for root, _, files in [(str(p), [], []) for p in ROOT.rglob("*") if p.is_dir()]:
        rel = Path(root).relative_to(ROOT).as_posix()
        if any(seg in rel for seg in (".git", "node_modules", "DerivedData")):
            continue
        for rx in patterns:
            if rx.search(rel):
                parent = Path(rel).parent.as_posix() or "(root)"
                if rel not in seen:
                    items.append({"path": rel, "parent": parent})
                    seen.add(rel)
                break
    return sorted(items, key=lambda x: x["path"])


def derive_decisions() -> list[dict]:
    if not ADR_DIR.is_dir():
        return []
    out = []
    for p in sorted(ADR_DIR.glob("*.md")):
        title = first_heading(p) or p.stem
        out.append({"path": p.relative_to(ROOT).as_posix(), "title": title})
    return out


def derive_plans() -> list[dict]:
    if not PLANS_DIR.is_dir():
        return []
    out = []
    for p in sorted(PLANS_DIR.glob("*.md")):
        title = first_heading(p) or p.stem
        out.append({"path": p.relative_to(ROOT).as_posix(), "title": title})
    return out


def derive_recent_activity() -> list[dict]:
    raw = git("log", "-8", "--format=%h\t%s\t%ar")
    out = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            out.append({"hash": parts[0], "subject": parts[1], "when": parts[2]})
    return out


def first_heading(p: Path) -> str:
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^#+\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return ""


# --- HTML rendering -------------------------------------------------------

def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def vscode_link(rel: str) -> str:
    return f"vscode://file/{ROOT.as_posix()}/{rel}"


def render_waves_svg(waves: list[dict]) -> str:
    if not waves:
        return '<p style="color:var(--muted);font-family:monospace;font-size:11px">no waves detected</p>'
    n = len(waves)
    width = 1040
    margin = 60
    spacing = (width - 2 * margin) / max(1, n - 1) if n > 1 else 0
    parts = [
        f'<svg viewBox="0 0 {width} 140" xmlns="http://www.w3.org/2000/svg" '
        f'preserveAspectRatio="xMinYMin meet" '
        f'style="font-family:\'JetBrains Mono\',\'SF Mono\',Menlo,monospace;">',
        f'<line x1="40" y1="60" x2="{width-40}" y2="60" stroke="#D5D5D5" stroke-width="1"/>',
    ]
    for i, w in enumerate(waves):
        x = margin + spacing * i if n > 1 else width / 2
        color = w.get("color", PALETTE["thesis"])
        r = 22 if i == n - 1 else 18
        parts.append(f'<text x="{x:.0f}" y="32" text-anchor="middle" font-size="10" '
                     f'fill="#6B6B6B">{esc(w.get("sub", ""))[:22]}</text>')
        parts.append(f'<circle cx="{x:.0f}" cy="60" r="{r}" fill="{color}"/>')
        parts.append(f'<text x="{x:.0f}" y="65" text-anchor="middle" fill="white" '
                     f'font-size="11" font-weight="700">{esc(w["label"])}</text>')
        if w.get("count"):
            parts.append(f'<text x="{x:.0f}" y="104" text-anchor="middle" '
                         f'font-size="9.5" fill="#6B6B6B">{w["count"]} commits</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def render(data: dict) -> str:
    p = PALETTE
    waves_svg = render_waves_svg(data["waves"])

    def card_grid(items: list[str]) -> str:
        return '<div class="grid">' + "".join(items) + '</div>'

    canonical_cards = "".join(
        f'<div class="card"><div class="id">:{esc(c["name"])}</div>'
        f'<div class="path"><a href="{esc(vscode_link(c["path"]))}">{esc(c["path"])}</a></div>'
        f'<div class="desc">{esc(c.get("desc", ""))}</div></div>'
        for c in data["canonical"]
    ) or '<p class="empty">No canonical artifacts inferred. Add docs/hub.yaml → canonical_refs:.</p>'

    concept_cards = "".join(
        f'<div class="card"><div class="id cn">:{esc(c["name"])}</div>'
        f'<div class="desc">{esc(c["desc"])}</div></div>'
        for c in data["concepts"]
    ) or '<p class="empty">No concepts detected (expected `- **Name** — description` bullets in CONTEXT.md).</p>'

    script_cards = "".join(
        f'<div class="card"><div class="id sc">:{esc(s["name"])}</div>'
        f'<div class="path">{esc(s["path"])}</div></div>'
        for s in data["scripts"]
    ) or '<p class="empty">No runnable entry points found.</p>'

    collab_cards = "".join(
        f'<div class="card"><div class="id pp">:{esc(c["name"])}</div>'
        f'<div class="desc">{c.get("count", 0)} commits</div></div>'
        for c in data["collaborators"]
    ) or '<p class="empty">No contributors.</p>'

    decision_list = "".join(
        f'<li><a href="{esc(vscode_link(d["path"]))}"><code>{esc(d["path"])}</code></a> '
        f'<span class="note">— {esc(d["title"])}</span></li>'
        for d in data["decisions"]
    ) or '<li class="empty">No ADRs in docs/adr/.</li>'

    plan_list = "".join(
        f'<li><a href="{esc(vscode_link(d["path"]))}"><code>{esc(d["path"])}</code></a> '
        f'<span class="note">— {esc(d["title"])}</span></li>'
        for d in data["plans"]
    ) or '<li class="empty">No plans in docs/plans/.</li>'

    superseded_list = "".join(
        f'<li><code>{esc(s["path"])}/</code> <span class="note">— in <code>{esc(s["parent"])}/</code></span></li>'
        for s in data["superseded"]
    ) or '<li class="empty">Nothing matched common superseded patterns (_orig, _old, _v*, *backup*, *.archived-*).</li>'

    activity_list = "".join(
        f'<li><code>{esc(a["hash"])}</code> {esc(a["subject"])} '
        f'<span class="note">({esc(a["when"])})</span></li>'
        for a in data["recent_activity"]
    )

    index_link = ('<a href="#graph" class="cta">jump to code graph ↓</a>'
                  if INDEX_HTML.exists() else "")

    graph_section = ("" if not INDEX_HTML.exists() else f"""
  <section id="graph">
    <h2 class="section">/// <span class="id">:graph</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— live force-directed view of the code nodes · drag · zoom · click to inspect</span></h2>
    <div class="graph-embed">
      <a href="INDEX.html" target="_blank" class="open-full">open full ↗</a>
      <iframe src="INDEX.html" title="Repo node graph"
              loading="lazy" referrerpolicy="no-referrer"></iframe>
    </div>
  </section>
""")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data['project'])} · project hub</title>
<style>
  :root {{
    --air: {p['air']}; --water: {p['water']}; --thesis: {p['thesis']};
    --bg: {p['bg']}; --bg-soft: {p['bg_soft']};
    --ink: {p['ink']}; --muted: {p['muted']};
    --border: {p['border']}; --border-2: {p['border_2']};
    --status-ok: {data['status']['color']};
    --dim: {p['dim']};
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--ink);
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    font-size: 14px; line-height: 1.55; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 28px 32px 96px; }}
  .mono, code {{ font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace; }}
  a {{ color: var(--air); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .banner {{ border: 1px solid var(--border); border-left: 4px solid var(--status-ok);
    padding: 18px 22px; background: var(--bg-soft);
    display: grid; grid-template-columns: 1fr auto; gap: 28px; align-items: center; }}
  .banner .eyebrow {{ margin: 0 0 4px; font-family: "JetBrains Mono", monospace;
    font-size: 11.5px; letter-spacing: 0.10em; text-transform: uppercase; color: var(--muted); }}
  .banner h1 {{ font-size: 22px; font-weight: 600; margin: 0; letter-spacing: -0.01em; }}
  .banner .sub {{ font-size: 13px; color: var(--muted); margin: 4px 0 0; }}
  .banner .meta {{ font-family: "JetBrains Mono", monospace; font-size: 11.5px;
    color: var(--muted); text-align: right; line-height: 1.7; }}
  .pill {{ display: inline-block; padding: 2px 9px; background: var(--status-ok);
    color: white; font-family: "JetBrains Mono", monospace;
    font-size: 11px; font-weight: 600; letter-spacing: 0.10em; }}
  .readout {{ font-family: "JetBrains Mono", monospace; font-size: 11px;
    color: var(--muted); padding: 8px 0 0; letter-spacing: 0.02em; }}
  .readout .dot {{ color: var(--status-ok); }}
  nav.strip {{ display: flex; flex-wrap: wrap; gap: 2px; margin: 24px 0 36px;
    padding: 6px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
    font-family: "JetBrains Mono", monospace; font-size: 12px; align-items: center; }}
  nav.strip a {{ color: var(--muted); padding: 6px 12px; }}
  nav.strip a:hover {{ color: var(--air); background: var(--bg-soft); text-decoration: none; }}
  nav.strip a.cta {{ margin-left: auto; color: var(--air); font-weight: 600; }}
  h2.section {{ font-family: "JetBrains Mono", monospace; font-size: 12px;
    font-weight: 600; color: var(--muted); letter-spacing: 0.10em;
    text-transform: uppercase; margin: 56px 0 18px; padding-bottom: 7px;
    border-bottom: 1px solid var(--border); }}
  h2.section .id {{ color: var(--air); }}
  .flow-frame {{ border: 1px solid var(--border);
    background: linear-gradient(var(--bg-soft) 1px, transparent 1px) 0 0 / 100% 14px,
                linear-gradient(90deg, var(--bg-soft) 1px, transparent 1px) 0 0 / 14px 100%,
                var(--bg);
    background-blend-mode: multiply; padding: 22px 12px 18px; overflow-x: auto; }}
  .flow-frame svg {{ display: block; width: 100%; min-width: 940px; height: auto; }}
  .graph-embed {{ position: relative; border: 1px solid var(--border);
    background: var(--bg-soft); }}
  .graph-embed iframe {{ display: block; width: 100%; height: 720px;
    border: 0; background: white; }}
  .graph-embed .open-full {{ position: absolute; top: 10px; right: 14px;
    font-family: "JetBrains Mono", monospace; font-size: 11px; color: var(--air);
    background: white; padding: 4px 9px; border: 1px solid var(--border);
    text-decoration: none; z-index: 2; }}
  .graph-embed .open-full:hover {{ background: var(--bg-soft); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }}
  .card {{ border: 1px solid var(--border); padding: 12px 14px 13px;
    background: white; transition: border-color 0.15s, background 0.15s; }}
  .card:hover {{ border-color: var(--air); background: var(--bg-soft); }}
  .card .id {{ font-family: "JetBrains Mono", monospace; font-size: 12.5px;
    font-weight: 600; color: var(--air); letter-spacing: -0.01em; }}
  .card .id.cn {{ color: var(--water); }}
  .card .id.sc {{ color: var(--thesis); }}
  .card .id.pp {{ color: #5A5A5A; }}
  .card .path {{ font-family: "JetBrains Mono", monospace; font-size: 11.5px;
    color: var(--ink); margin-top: 4px; word-break: break-all; }}
  .card .desc {{ font-size: 12.5px; color: var(--ink); margin-top: 6px; line-height: 1.5; }}
  .touch-list, .doc-list {{ margin: 8px 0 0; padding: 0; list-style: none; }}
  .touch-list li, .doc-list li {{ padding: 5px 0; font-size: 13.5px;
    border-bottom: 1px dashed var(--border); }}
  .touch-list li:last-child, .doc-list li:last-child {{ border-bottom: 0; }}
  .touch-list code, .doc-list code {{ color: var(--air); background: var(--bg-soft);
    padding: 1px 6px; font-size: 12px; }}
  .doc-list .note {{ color: var(--muted); font-family: Inter, sans-serif; font-size: 12px; }}
  #superseded {{ opacity: 0.7; }}
  #superseded:hover {{ opacity: 1; }}
  .empty {{ color: var(--muted); font-style: italic; }}
  footer {{ margin-top: 72px; padding-top: 22px; border-top: 1px solid var(--border);
    font-family: "JetBrains Mono", monospace; font-size: 11.5px; color: var(--muted);
    display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }}
  footer code {{ background: var(--bg-soft); padding: 1px 5px; color: var(--ink); }}
  @media (max-width: 720px) {{
    .banner {{ grid-template-columns: 1fr; }}
    .banner .meta {{ text-align: left; }}
    .wrap {{ padding: 20px 18px 60px; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <header class="banner">
    <div>
      <p class="eyebrow">{esc(data['project'])} // project hub</p>
      <h1>{esc(data['tagline']) or esc(data['project'])}</h1>
      <p class="sub">branch <code>{esc(data['branch'])}</code> · {esc(data['status']['reason'])}</p>
    </div>
    <div class="meta">
      <span class="pill">{esc(data['status']['pill'])}</span><br>
      hub regenerated {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>
      from <code style="background:transparent;padding:0;color:var(--ink)">scripts/build_hub.py</code>
    </div>
  </header>

  <div class="readout">
    <span class="dot">●</span> system online &nbsp;·&nbsp;
    {len(data['waves'])} waves &nbsp;·&nbsp;
    {len(data['canonical'])} canonical &nbsp;·&nbsp;
    {len(data['concepts'])} concepts &nbsp;·&nbsp;
    {len(data['scripts'])} scripts &nbsp;·&nbsp;
    {len(data['collaborators'])} contributors &nbsp;·&nbsp;
    {len(data['superseded'])} superseded
  </div>

  <nav class="strip">
    <a href="#status">:status</a>
    <a href="#waves">:waves</a>
    <a href="#graph">:graph</a>
    <a href="#canonical">:canonical</a>
    <a href="#concepts">:concepts</a>
    <a href="#scripts">:scripts</a>
    <a href="#decisions">:decisions</a>
    <a href="#plans">:plans</a>
    <a href="#collaborators">:collaborators</a>
    <a href="#activity">:activity</a>
    <a href="#superseded">:superseded</a>
    {index_link}
  </nav>

  <section id="status">
    <h2 class="section">/// <span class="id">:status</span></h2>
    <p>Status: <strong>{esc(data['status']['pill'])}</strong> &nbsp;·&nbsp; {esc(data['status']['reason'])}.</p>
    <p>Touch this directory to:</p>
    <ul class="touch-list">
      <li>understand what's authoritative right now &nbsp;→&nbsp; <code><a href="#canonical">:canonical</a></code></li>
      <li>recall the project's vocabulary &nbsp;→&nbsp; <code><a href="#concepts">:concepts</a></code></li>
      <li>regenerate an artifact &nbsp;→&nbsp; <code><a href="#scripts">:scripts</a></code></li>
      <li>see why a decision was made &nbsp;→&nbsp; <code><a href="#decisions">:decisions</a></code></li>
      <li>find what's been retired &nbsp;→&nbsp; <code><a href="#superseded">:superseded</a></code></li>
    </ul>
  </section>

  <section id="waves">
    <h2 class="section">/// <span class="id">:waves</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— phases of work, derived from commit history</span></h2>
    <div class="flow-frame">{waves_svg}</div>
  </section>
{graph_section}
  <section id="canonical">
    <h2 class="section">/// <span class="id">:canonical</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— where current truth lives</span></h2>
    {card_grid([canonical_cards])}
  </section>

  <section id="concepts">
    <h2 class="section">/// <span class="id" style="color:var(--water)">:concepts</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— vocabulary from CONTEXT.md</span></h2>
    {card_grid([concept_cards])}
  </section>

  <section id="scripts">
    <h2 class="section">/// <span class="id" style="color:var(--thesis)">:scripts</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— regeneration entry points</span></h2>
    {card_grid([script_cards])}
  </section>

  <section id="decisions">
    <h2 class="section">/// <span class="id">:decisions</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— ADRs in docs/adr/</span></h2>
    <ul class="doc-list">{decision_list}</ul>
  </section>

  <section id="plans">
    <h2 class="section">/// <span class="id">:plans</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— in-flight work in docs/plans/</span></h2>
    <ul class="doc-list">{plan_list}</ul>
  </section>

  <section id="collaborators">
    <h2 class="section">/// <span class="id" style="color:#5A5A5A">:collaborators</span></h2>
    {card_grid([collab_cards])}
  </section>

  <section id="activity">
    <h2 class="section">/// <span class="id">:activity</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— most-recent commits</span></h2>
    <ul class="doc-list">{activity_list}</ul>
  </section>

  <section id="superseded">
    <h2 class="section">/// <span class="id" style="color:var(--dim)">:superseded</span>
      &nbsp; <span style="color:var(--muted);letter-spacing:0;text-transform:none;font-weight:normal">— kept for provenance, not for daily use (hover to undim)</span></h2>
    <ul class="doc-list">{superseded_list}</ul>
  </section>

  <footer>
    <span>auto-generated from repo state · override curated bits in <code>docs/hub.yaml</code> · never edit this HTML directly</span>
    <span>regenerated {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
  </footer>

</div>
</body>
</html>
"""


# --- main -----------------------------------------------------------------

def collect() -> dict:
    o = load_overrides()
    return {
        "project": derive_project_name(o),
        "tagline": derive_tagline(o),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD") or "(detached)",
        "status": derive_status(o),
        "waves": derive_waves(o),
        "canonical": derive_canonical(o),
        "concepts": derive_concepts(o),
        "scripts": derive_scripts(o),
        "collaborators": derive_collaborators(o),
        "superseded": derive_superseded(),
        "decisions": derive_decisions(),
        "plans": derive_plans(),
        "recent_activity": derive_recent_activity(),
    }


def main() -> int:
    data = collect()
    html = render(data)

    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != html:
            print("❌ docs/HUB.html is stale.  → run: python3 scripts/build_hub.py")
            return 1
        print("✓ docs/HUB.html up to date.")
        return 0

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"(status={data['status']['pill']}, "
          f"{len(data['waves'])} waves, "
          f"{len(data['canonical'])} canonical, "
          f"{len(data['concepts'])} concepts, "
          f"{len(data['scripts'])} scripts, "
          f"{len(data['collaborators'])} contributors, "
          f"{len(data['superseded'])} superseded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
