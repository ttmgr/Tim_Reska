#!/usr/bin/env python3
"""Generate docs/INDEX.html — an interactive visualisation of the repo node map.

Sibling to scripts/build_index.py. Reads the same docs/index_nodes.yaml and runs
the same file scan, so the visualisation can never disagree with INDEX.md about
which file belongs to which node.

The output is a single self-contained HTML file (no CDN, no external assets) —
open it directly in a browser (`open docs/INDEX.html` on macOS). Layout is a
force-directed SVG graph; clicking a node opens a side panel with its files,
each a `vscode://file/...` link that opens in VS Code / Cursor / Windsurf.

Usage:
    python3 scripts/build_visualization.py            # write docs/INDEX.html
    python3 scripts/build_visualization.py --check    # exit 1 if stale
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "docs" / "index_nodes.yaml"
OUT = ROOT / "docs" / "INDEX.html"

# Project-specific group palette — mirrors the warm-terracotta family of
# assets/css/tokens.css plus a green (for the outbreak/health semantic) and
# slate (for infrastructure). Skill's authoritative copy stays vanilla;
# only this project's copy is tuned to .nav/INDEX.md's 7 groups + Meta.
GROUP_COLOR = {
    "Applied ML · healthcare":         "#9A5A2E",  # deep terracotta — clinical
    "LLM evaluation":                  "#C4794A",  # signature terracotta — academic showcase
    "AI deployment strategy":          "#D29066",  # lighter terracotta — business/strategy
    "Outbreak dashboards":             "#2D8659",  # forest green — epidemic/dashboard semantic
    "Other showcases":                 "#B5651D",  # burnt orange — mixed bag
    "Infrastructure · non-published":  "#6B7280",  # slate — infra
    "Local-only / private":            "#B0AFA8",  # warm grey — dim/private
    "Meta & tooling":                  "#1F8A70",  # teal — tool/system
}
FALLBACK_COLOR = "#94A3B8"


# --- file-scan (matches build_index.py; small enough to duplicate over coupling)

def universe() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return sorted({p for p in out if p.strip()})


def glob_to_re(g: str) -> re.Pattern:
    i, out = 0, ["^"]
    while i < len(g):
        if g[i:i + 3] == "**/":
            out.append("(?:.*/)?"); i += 3
        elif g[i:i + 2] == "**":
            out.append(".*"); i += 2
        elif g[i] == "*":
            out.append("[^/]*"); i += 1
        elif g[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(g[i])); i += 1
    out.append("$")
    return re.compile("".join(out))


def specificity(g: str) -> int:
    return len(g) - g.count("*") - g.count("?")


def assign_files(cfg: dict) -> tuple[dict[str, list[str]], list[str]]:
    """Return (node_id → sorted file list, unmapped files)."""
    ignore = [glob_to_re(g) for g in cfg.get("ignore", [])]
    nodes = cfg["nodes"]
    files = [f for f in universe() if not any(rx.match(f) for rx in ignore)]
    compiled = {n["id"]: [(g, glob_to_re(g)) for g in n.get("globs", [])] for n in nodes}

    assigned: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    unmapped: list[str] = []
    for f in files:
        best = None
        for n in nodes:
            for g, rx in compiled[n["id"]]:
                if rx.match(f):
                    cand = (specificity(g), n["id"])
                    if best is None or cand[0] > best[0]:
                        best = cand
        if best is None:
            unmapped.append(f)
        else:
            assigned[best[1]].append(f)
    for nid in assigned:
        assigned[nid].sort()
    return assigned, unmapped


# --- HTML / JS rendering --------------------------------------------------

def render(cfg: dict, assigned: dict[str, list[str]]) -> str:
    nodes_data = []
    for n in cfg["nodes"]:
        nid = n["id"]
        files = assigned.get(nid, [])
        nodes_data.append({
            "id": nid,
            "title": n["title"],
            "group": n.get("group", "Other"),
            "summary": (n.get("summary") or "").strip(),
            "reads_for": n.get("reads_for") or "",
            "files": files,
            "edges": n.get("edges", []),
            "note": (n.get("note") or "").strip(),
            "color": GROUP_COLOR.get(n.get("group", ""), FALLBACK_COLOR),
        })

    payload = {
        "title": cfg.get("title", "Repo Node Map"),
        "root_abs": str(ROOT),
        "groups": cfg.get("groups", []),
        "group_color": GROUP_COLOR,
        "fallback_color": FALLBACK_COLOR,
        "nodes": nodes_data,
    }

    # The JSON is embedded as a JS const; safe since we control the input
    # (curated YAML + repo paths). We still escape </script> as a precaution.
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{payload['title']}</title>
<style>
  :root {{
    --bg: #FAF9F7;
    --panel: #FFFFFF;
    --ink: #1A1A2E;
    --muted: #6B6A73;
    --border: rgba(26,26,46,0.10);
    --edge: rgba(26,26,46,0.22);
    --edge-hi: #C4794A;
    --selected: #9A5A2E;
  }}
  html, body {{ margin: 0; height: 100%; background: var(--bg); color: var(--ink);
    font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif; }}
  #app {{ display: grid; grid-template-columns: 1fr 380px; height: 100vh; }}
  #graph {{ position: relative; overflow: hidden; background:
    radial-gradient(ellipse at center, #fff 0%, var(--bg) 70%); }}
  #controls {{ position: absolute; top: 14px; left: 14px; z-index: 5;
    display: flex; gap: 8px; align-items: center; }}
  #controls input, #controls select {{
    font: inherit; padding: 7px 10px; border: 1px solid var(--border);
    border-radius: 8px; background: var(--panel); color: var(--ink);
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }}
  #controls input {{ width: 220px; }}
  #controls label {{ display: flex; gap: 6px; align-items: center; padding: 4px 8px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    color: var(--muted); }}
  #meta {{ position: absolute; bottom: 12px; left: 14px; z-index: 5;
    color: var(--muted); font-size: 12px; }}
  #legend {{ position: absolute; top: 14px; right: 14px; z-index: 5;
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    padding: 8px 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); font-size: 12px; }}
  #legend .row {{ display: flex; align-items: center; gap: 8px; padding: 2px 0; }}
  #legend .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
  svg {{ width: 100%; height: 100%; cursor: grab; user-select: none; }}
  svg.dragging {{ cursor: grabbing; }}
  .edge {{ stroke: var(--edge); stroke-width: 1; fill: none; }}
  .edge.hi {{ stroke: var(--edge-hi); stroke-width: 2; }}
  .node circle {{ stroke: white; stroke-width: 2; cursor: pointer; }}
  .node.selected circle {{ stroke: var(--selected); stroke-width: 3; }}
  .node.dim {{ opacity: 0.18; }}
  .node text {{ font-size: 11px; pointer-events: none; fill: var(--ink);
    text-anchor: middle; dominant-baseline: hanging; paint-order: stroke;
    stroke: white; stroke-width: 3; }}
  #panel {{ border-left: 1px solid var(--border); background: var(--panel);
    overflow-y: auto; padding: 22px 22px 32px; }}
  #panel h1 {{ margin: 0 0 4px; font-size: 18px; }}
  #panel .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px;
    font-size: 11px; color: white; margin-bottom: 12px; }}
  #panel .read {{ color: var(--muted); font-style: italic; margin: 4px 0 12px; }}
  #panel .summary {{ margin: 0 0 16px; }}
  #panel h2 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--muted); margin: 18px 0 6px; }}
  #panel ul {{ margin: 0; padding: 0; list-style: none; }}
  #panel li {{ padding: 3px 0; }}
  #panel a {{ color: #9A5A2E; text-decoration: none; word-break: break-all; }}
  #panel a:hover {{ text-decoration: underline; }}
  #panel .edges a {{ display: inline-block; padding: 3px 8px; margin: 2px 4px 2px 0;
    background: rgba(196,121,74,0.10); border-radius: 6px; cursor: pointer; }}
  #panel .empty {{ color: var(--muted); }}
  .nofile {{ color: var(--muted); }}
</style>
</head>
<body>
<div id="app">
  <div id="graph">
    <div id="controls">
      <input id="search" type="search" placeholder="search nodes / files…" />
      <select id="hub"><option value="">all hubs</option></select>
    </div>
    <div id="legend"></div>
    <div id="meta"></div>
    <svg id="svg"></svg>
  </div>
  <aside id="panel">
    <p class="empty">Click a node to inspect.</p>
  </aside>
</div>
<script>
const DATA = {payload_json};
const SVG = document.getElementById('svg');
const PANEL = document.getElementById('panel');
const LEGEND = document.getElementById('legend');
const META = document.getElementById('meta');
const HUB_SEL = document.getElementById('hub');
const SEARCH = document.getElementById('search');

// --- file-count summary ---------------------------------------------------
const totalFiles = DATA.nodes.reduce((s,n) => s + n.files.length, 0);
META.textContent =
  `${{DATA.nodes.length}} nodes · ${{totalFiles}} files · ` +
  `drag node = reposition · wheel = zoom · drag canvas = pan`;

// --- legend + hub filter --------------------------------------------------
for (const g of DATA.groups) {{
  const row = document.createElement('div');
  row.className = 'row';
  row.innerHTML = `<span class="dot" style="background:${{DATA.group_color[g] || DATA.fallback_color}}"></span>${{g}}`;
  LEGEND.appendChild(row);
  const opt = document.createElement('option');
  opt.value = g; opt.textContent = g;
  HUB_SEL.appendChild(opt);
}}

// --- force-directed layout (vanilla JS, ~O(n^2) is fine for ~43 nodes) ----
const W = () => SVG.clientWidth, H = () => SVG.clientHeight;
const groupCentroids = {{}};
DATA.groups.forEach((g, i) => {{
  const angle = (i / Math.max(1, DATA.groups.length)) * Math.PI * 2;
  groupCentroids[g] = {{
    x: Math.cos(angle) * 0.35,   // unit-circle offsets, scaled at render
    y: Math.sin(angle) * 0.35,
  }};
}});

const nodes = DATA.nodes.map((n, i) => {{
  const c = groupCentroids[n.group] || {{x: 0, y: 0}};
  return {{
    ...n,
    radius: 9 + Math.sqrt(n.files.length) * 3.2,
    // initial position: jittered around the group centroid (in [-0.5, 0.5] units)
    x: c.x + (Math.random() - 0.5) * 0.15,
    y: c.y + (Math.random() - 0.5) * 0.15,
    vx: 0, vy: 0,
    fx: null, fy: null,  // pinned position when dragging
  }};
}});
const nodeIndex = Object.fromEntries(nodes.map((n, i) => [n.id, i]));

// edges (undirected — dedup symmetric pairs)
const edgeSet = new Set();
const edges = [];
for (const n of DATA.nodes) {{
  for (const e of n.edges) {{
    if (!(e in nodeIndex)) continue;
    const a = n.id, b = e;
    const key = a < b ? `${{a}}\\u0001${{b}}` : `${{b}}\\u0001${{a}}`;
    if (edgeSet.has(key)) continue;
    edgeSet.add(key);
    edges.push({{ source: nodeIndex[a], target: nodeIndex[b] }});
  }}
}}

// physics tunables — in "unit" coordinates (centred at 0,0, scaled by world size)
const REPULSION   = 0.00040;   // pairwise repulsion strength
const SPRING_K    = 0.018;     // edge spring
const SPRING_LEN  = 0.20;
const GRAVITY     = 0.012;     // pulls to (0,0)
const GROUP_PULL  = 0.022;     // pulls to group centroid
const DAMPING     = 0.86;

function tick() {{
  for (const n of nodes) {{
    if (n.fx !== null) {{ n.x = n.fx; n.y = n.fy; n.vx = 0; n.vy = 0; continue; }}
    let ax = 0, ay = 0;
    // repulsion (O(n^2), fine here)
    for (const m of nodes) {{
      if (m === n) continue;
      const dx = n.x - m.x, dy = n.y - m.y;
      const d2 = dx*dx + dy*dy + 0.0001;
      const f = REPULSION / d2;
      ax += dx * f;
      ay += dy * f;
    }}
    // gravity to center
    ax += -n.x * GRAVITY;
    ay += -n.y * GRAVITY;
    // group attraction
    const c = groupCentroids[n.group];
    if (c) {{
      ax += (c.x - n.x) * GROUP_PULL;
      ay += (c.y - n.y) * GROUP_PULL;
    }}
    n.vx = (n.vx + ax) * DAMPING;
    n.vy = (n.vy + ay) * DAMPING;
    n.x += n.vx;
    n.y += n.vy;
  }}
  // edge springs (after repulsion so applied to current frame)
  for (const e of edges) {{
    const a = nodes[e.source], b = nodes[e.target];
    const dx = b.x - a.x, dy = b.y - a.y;
    const dist = Math.sqrt(dx*dx + dy*dy) + 0.0001;
    const delta = (dist - SPRING_LEN) * SPRING_K;
    const fx = (dx / dist) * delta;
    const fy = (dy / dist) * delta;
    if (a.fx === null) {{ a.vx += fx; a.vy += fy; a.x += fx; a.y += fy; }}
    if (b.fx === null) {{ b.vx -= fx; b.vy -= fy; b.x -= fx; b.y -= fy; }}
  }}
}}

// settle the layout before first render
for (let i = 0; i < 400; i++) tick();

// --- rendering ------------------------------------------------------------
const ns = "http://www.w3.org/2000/svg";
let viewScale = 1.0, viewX = 0, viewY = 0;   // pan/zoom
const gRoot = document.createElementNS(ns, "g");
const gEdges = document.createElementNS(ns, "g");
const gNodes = document.createElementNS(ns, "g");
gRoot.appendChild(gEdges);
gRoot.appendChild(gNodes);
SVG.appendChild(gRoot);

const edgeEls = edges.map(e => {{
  const ln = document.createElementNS(ns, "line");
  ln.setAttribute("class", "edge");
  gEdges.appendChild(ln);
  return ln;
}});

const nodeEls = nodes.map(n => {{
  const g = document.createElementNS(ns, "g");
  g.setAttribute("class", "node");
  const c = document.createElementNS(ns, "circle");
  c.setAttribute("r", n.radius);
  c.setAttribute("fill", n.color);
  const t = document.createElementNS(ns, "text");
  t.setAttribute("y", n.radius + 4);
  t.textContent = n.title;
  g.appendChild(c);
  g.appendChild(t);
  gNodes.appendChild(g);
  g.addEventListener("click", (ev) => {{ ev.stopPropagation(); select(n.id); }});
  // drag a node
  g.addEventListener("pointerdown", (ev) => {{
    ev.stopPropagation();
    const pt = toWorld(ev.clientX, ev.clientY);
    n.fx = pt.x; n.fy = pt.y;
    g.setPointerCapture(ev.pointerId);
    const move = (mv) => {{
      const p = toWorld(mv.clientX, mv.clientY);
      n.fx = p.x; n.fy = p.y;
    }};
    const up = () => {{
      g.releasePointerCapture(ev.pointerId);
      g.removeEventListener("pointermove", move);
      g.removeEventListener("pointerup", up);
      // hold the position for a beat, then release back to the simulation
      setTimeout(() => {{ n.fx = null; n.fy = null; }}, 600);
    }};
    g.addEventListener("pointermove", move);
    g.addEventListener("pointerup", up);
  }});
  return g;
}});

function worldToScreen() {{
  const w = W(), h = H();
  // unit coords (-0.5..0.5 typical) → screen; viewScale + viewX/viewY centre + zoom
  const scale = Math.min(w, h) * 0.9 * viewScale;
  const cx = w / 2 + viewX, cy = h / 2 + viewY;
  return {{ scale, cx, cy }};
}}
function toWorld(sx, sy) {{
  const r = SVG.getBoundingClientRect();
  const {{ scale, cx, cy }} = worldToScreen();
  return {{ x: (sx - r.left - cx) / scale, y: (sy - r.top - cy) / scale }};
}}

function render() {{
  const {{ scale, cx, cy }} = worldToScreen();
  for (let i = 0; i < edges.length; i++) {{
    const e = edges[i];
    const a = nodes[e.source], b = nodes[e.target];
    const ln = edgeEls[i];
    ln.setAttribute("x1", cx + a.x * scale);
    ln.setAttribute("y1", cy + a.y * scale);
    ln.setAttribute("x2", cx + b.x * scale);
    ln.setAttribute("y2", cy + b.y * scale);
  }}
  for (let i = 0; i < nodes.length; i++) {{
    const n = nodes[i];
    nodeEls[i].setAttribute("transform", `translate(${{cx + n.x * scale}}, ${{cy + n.y * scale}})`);
  }}
}}

function loop() {{
  tick();
  render();
  requestAnimationFrame(loop);
}}
loop();

// --- pan / zoom -----------------------------------------------------------
let panning = false, panStart = null;
SVG.addEventListener("pointerdown", (ev) => {{
  if (ev.target.closest(".node")) return;  // node drag handles itself
  panning = true; panStart = {{ x: ev.clientX, y: ev.clientY, vx: viewX, vy: viewY }};
  SVG.classList.add("dragging");
  SVG.setPointerCapture(ev.pointerId);
}});
SVG.addEventListener("pointermove", (ev) => {{
  if (!panning) return;
  viewX = panStart.vx + (ev.clientX - panStart.x);
  viewY = panStart.vy + (ev.clientY - panStart.y);
}});
SVG.addEventListener("pointerup", (ev) => {{
  panning = false;
  SVG.classList.remove("dragging");
  try {{ SVG.releasePointerCapture(ev.pointerId); }} catch (e) {{}}
}});
SVG.addEventListener("wheel", (ev) => {{
  ev.preventDefault();
  const factor = Math.exp(-ev.deltaY * 0.001);
  viewScale = Math.max(0.3, Math.min(4, viewScale * factor));
}}, {{ passive: false }});
SVG.addEventListener("click", () => {{ /* canvas click — clear handled by node click stopProp */ }});

// --- selection / panel ----------------------------------------------------
let selected = null;
function fileLink(rel) {{
  // vscode://file/<abs-path> — opens in VS Code / Cursor / Windsurf
  const abs = `${{DATA.root_abs}}/${{rel}}`;
  return `<a href="vscode://file/${{encodeURI(abs)}}" title="open in editor">${{rel}}</a>`;
}}
function select(id) {{
  selected = id;
  for (let i = 0; i < nodes.length; i++) {{
    nodeEls[i].classList.toggle("selected", nodes[i].id === id);
  }}
  const neighbours = new Set([id]);
  for (const e of edges) {{
    if (nodes[e.source].id === id) neighbours.add(nodes[e.target].id);
    if (nodes[e.target].id === id) neighbours.add(nodes[e.source].id);
  }}
  for (let i = 0; i < edges.length; i++) {{
    const e = edges[i];
    const hot = nodes[e.source].id === id || nodes[e.target].id === id;
    edgeEls[i].classList.toggle("hi", hot);
  }}
  // dim non-neighbours
  applyFilter();
  for (let i = 0; i < nodes.length; i++) {{
    if (!nodeEls[i].classList.contains("dim")) {{
      nodeEls[i].classList.toggle("dim", !neighbours.has(nodes[i].id));
    }}
  }}
  // panel
  const n = nodes[nodeIndex[id]];
  const fileHtml = n.files.length
    ? `<ul>${{n.files.map(f => `<li>${{fileLink(f)}}</li>`).join("")}}</ul>`
    : `<p class="nofile">No files in this node (e.g. external reference).</p>`;
  const edgeHtml = n.edges.length
    ? `<div class="edges">${{n.edges.map(e =>
        `<a data-jump="${{e}}">${{e}}</a>`).join("")}}</div>`
    : `<p class="empty">No links.</p>`;
  const noteHtml = n.note
    ? `<h2>Where</h2><p>${{escapeHtml(n.note)}}</p>` : "";
  PANEL.innerHTML = `
    <h1>${{escapeHtml(n.title)}}</h1>
    <span class="badge" style="background:${{n.color}}">${{escapeHtml(n.group)}}</span>
    ${{n.reads_for ? `<p class="read">Read when ${{escapeHtml(n.reads_for)}}.</p>` : ""}}
    ${{n.summary ? `<p class="summary">${{escapeHtml(n.summary)}}</p>` : ""}}
    <h2>id</h2><code>${{n.id}}</code>
    <h2>Files (${{n.files.length}})</h2>
    ${{fileHtml}}
    ${{noteHtml}}
    <h2>Linked nodes</h2>
    ${{edgeHtml}}
  `;
  PANEL.querySelectorAll("a[data-jump]").forEach(a =>
    a.addEventListener("click", (ev) => {{ ev.preventDefault(); select(a.dataset.jump); }}));
}}
function escapeHtml(s) {{
  return String(s).replace(/[&<>"']/g, c =>
    ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }}[c]));
}}

// --- search / hub filter --------------------------------------------------
function matchesSearch(n, q) {{
  if (!q) return true;
  const hay = (n.id + " " + n.title + " " + n.reads_for + " " + n.files.join(" ")).toLowerCase();
  return hay.includes(q);
}}
function applyFilter() {{
  const q = SEARCH.value.trim().toLowerCase();
  const hub = HUB_SEL.value;
  for (let i = 0; i < nodes.length; i++) {{
    const n = nodes[i];
    const hide = (hub && n.group !== hub) || !matchesSearch(n, q);
    nodeEls[i].classList.toggle("dim", hide);
  }}
}}
SEARCH.addEventListener("input", applyFilter);
HUB_SEL.addEventListener("change", applyFilter);
</script>
</body>
</html>
"""


def main() -> int:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assigned, unmapped = assign_files(cfg)
    html = render(cfg, assigned)

    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != html:
            print("❌ docs/INDEX.html is stale.")
            print("→ Run: python3 scripts/build_visualization.py && git add docs/INDEX.html")
            return 1
        print("✓ docs/INDEX.html up to date.")
        return 0

    OUT.write_text(html, encoding="utf-8")
    n_nodes = len(cfg["nodes"])
    n_files = sum(len(v) for v in assigned.values())
    print(f"wrote {OUT.relative_to(ROOT)}  ({n_nodes} nodes, {n_files} files"
          + (f", ⚠ {len(unmapped)} unmapped" if unmapped else "") + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
