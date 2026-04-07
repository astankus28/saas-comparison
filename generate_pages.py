"""
SaaSScouter · Static page generator
Run from repo root: python generate_pages.py

Reads tools.json → writes all comparison pages, hub pages, index, and sitemap.
Design tokens live in STYLES (single source of truth for CSS).
"""
from __future__ import annotations

import glob
import html
import itertools
import json
import os
from datetime import date

# ── CONFIG ────────────────────────────────────────────────────────────────────
LAST_REVIEWED = "April 2026"
SITE_NAME     = "SaaSScouter"
AUTHOR        = "Andrew Stankus"
BASE_URL      = ""  # filled by main() from env or site.json

CATEGORY_META = {
    "ai-writing": {
        "title": "AI Writing Tools",
        "blurb": "Draft, edit, and scale marketing copy with AI built for marketing teams.",
        "icon": "✍️",
    },
    "design-visual": {
        "title": "Design & AI Imagery",
        "blurb": "Templates, AI generation, and visual assets for any campaign.",
        "icon": "🎨",
    },
    "crm-funnels": {
        "title": "CRM & Funnel Platforms",
        "blurb": "Capture leads, automate follow-up, and close deals faster.",
        "icon": "📊",
    },
    "seo": {
        "title": "SEO Tooling",
        "blurb": "SERP data, content briefs, and on-page scoring that actually ranks.",
        "icon": "🔍",
    },
    "video-audio": {
        "title": "Video & Podcast Editing",
        "blurb": "Edit by transcript, clean audio, and ship episodes faster.",
        "icon": "🎙️",
    },
}

# High-intent cross-category pairs worth covering
BRIDGE_PAIRS = [
    ("surferseo", "writesonic"),
    ("surferseo", "jasper"),
    ("descript", "canva"),
]

# Score dimension labels (must match keys in tools.json "scores" object)
SCORE_DIMS = [
    ("value",       "Value for money"),
    ("ease_of_use", "Ease of use"),
    ("features",    "Feature depth"),
    ("support",     "Support quality"),
]


# ── SHARED CSS ────────────────────────────────────────────────────────────────
SHARED_CSS = """
    :root {
      --ink: #0f0e0d;
      --paper: #faf9f7;
      --accent: #e8521a;
      --accent-muted: #fde8df;
      --muted: #6b6660;
      --border: #e5e2dd;
      --card: #ffffff;
      --green: #1a7a4a;
      --green-bg: #e6f4ed;
      --red: #b91c1c;
      --red-bg: #fee2e2;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 16px; scroll-behavior: smooth; }
    body {
      font-family: 'DM Sans', sans-serif;
      background: var(--paper); color: var(--ink);
      line-height: 1.6; -webkit-font-smoothing: antialiased;
    }
    nav {
      position: sticky; top: 0; z-index: 50;
      background: var(--paper); border-bottom: 1px solid var(--border);
      padding: 0 clamp(1rem,4vw,3rem);
    }
    .nav-inner {
      max-width: 1200px; margin: 0 auto;
      display: flex; align-items: center; justify-content: space-between;
      height: 58px; gap: 2rem;
    }
    .logo {
      font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.1rem;
      color: var(--ink); text-decoration: none; letter-spacing: -0.02em;
    }
    .logo span { color: var(--accent); }
    .nav-links { display: flex; gap: 2rem; list-style: none; }
    .nav-links a {
      font-size: 0.78rem; font-weight: 500; color: var(--muted);
      text-decoration: none; letter-spacing: 0.06em; text-transform: uppercase;
      transition: color 0.15s;
    }
    .nav-links a:hover { color: var(--ink); }
    .breadcrumb { font-size: 0.75rem; color: var(--muted); display: flex; align-items: center; gap: 0.5rem; }
    .breadcrumb a { color: var(--muted); text-decoration: none; }
    .breadcrumb a:hover { color: var(--ink); }
    .disclosure {
      font-size: 0.72rem; color: var(--muted);
      border-top: 1px solid var(--border);
      padding: 0.6rem clamp(1rem,4vw,3rem);
      text-align: center; background: var(--paper);
    }
    .section-label {
      font-size: 0.7rem; font-weight: 500; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--muted); margin-bottom: 1.75rem;
      display: flex; align-items: center; gap: 0.75rem;
    }
    .section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }
    .score-row { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
    .score-label { font-size: 0.72rem; color: var(--muted); flex: 1; }
    .score-bar-wrap { width: 80px; height: 5px; background: var(--border); border-radius: 100px; overflow: hidden; }
    .score-bar-fill { height: 100%; border-radius: 100px; background: var(--accent); }
    .score-num { font-size: 0.72rem; font-weight: 600; color: var(--ink); width: 26px; text-align: right; }
    footer {
      border-top: 1px solid var(--border); padding: 3rem clamp(1rem,4vw,3rem);
      background: var(--ink); color: rgba(255,255,255,0.4);
    }
    .footer-inner {
      max-width: 1200px; margin: 0 auto;
      display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;
    }
    .footer-logo { font-family: 'Syne', sans-serif; font-weight: 800; color: #fff; font-size: 1rem; text-decoration: none; }
    .footer-logo span { color: var(--accent); }
    .footer-text { font-size: 0.72rem; max-width: 520px; line-height: 1.7; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 640px) { .nav-links { display: none; } }
"""


# ── HELPERS ───────────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    return html.escape(str(s), quote=True)

def cta_url(tool: dict) -> str:
    aff = tool.get("affiliate_link")
    if isinstance(aff, str) and aff.strip():
        return aff.strip()
    return tool["link"]

def canonical_href(path: str) -> str:
    if BASE_URL:
        return f"{BASE_URL}/{path}"
    return path

def comparison_filename(a: str, b: str) -> str:
    x, y = sorted((a, b))
    return f"{x}-vs-{y}.html"

def resolve_base_url(repo_root: str) -> str:
    env = os.environ.get("SAAS_SCOUTER_SITE_URL", "").strip().rstrip("/")
    if env:
        return env
    site_json = os.path.join(repo_root, "site.json")
    if os.path.isfile(site_json):
        with open(site_json, encoding="utf-8") as f:
            data = json.load(f)
        return str(data.get("base_url", "")).strip().rstrip("/")
    return ""

def build_tool_index(tools: list[dict]) -> dict[str, dict]:
    by_id = {t["id"]: t for t in tools}
    for t in tools:
        if "category" not in t:
            raise ValueError(f"Tool {t.get('id')} missing category")
    return by_id

def curated_pairs(by_id: dict[str, dict]) -> list[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    cat_to_ids: dict[str, list[str]] = {}
    for tid, t in by_id.items():
        cat_to_ids.setdefault(t["category"], []).append(tid)
    for ids in cat_to_ids.values():
        for a, b in itertools.combinations(sorted(ids), 2):
            pairs.add((a, b))
    for a, b in BRIDGE_PAIRS:
        if a not in by_id or b not in by_id:
            raise ValueError(f"Bridge pair references unknown id: {a}, {b}")
        pairs.add(tuple(sorted((a, b))))
    return sorted(pairs, key=lambda p: (p[0], p[1]))

def score_bars_html(tool: dict) -> str:
    scores = tool.get("scores", {})
    rows = []
    for key, label in SCORE_DIMS:
        val = scores.get(key)
        if val is None:
            continue
        pct = int(val / 10 * 100)
        rows.append(f"""
        <div class="score-row">
          <span class="score-label">{esc(label)}</span>
          <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{pct}%"></div></div>
          <span class="score-num">{val}</span>
        </div>""")
    return "\n".join(rows)


# ── SHARED FRAGMENTS ──────────────────────────────────────────────────────────

def font_link() -> str:
    return '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;1,9..40,400&display=swap" rel="stylesheet">'

def nav_fragment(right_content: str = "") -> str:
    if not right_content:
        right_content = """<ul class="nav-links">
          <li><a href="index.html#categories">Categories</a></li>
          <li><a href="index.html#comparisons">Comparisons</a></li>
        </ul>"""
    return f"""<nav>
      <div class="nav-inner">
        <a href="index.html" class="logo">SaaS<span>Scouter</span></a>
        {right_content}
      </div>
    </nav>
    <div class="disclosure">
      Some links are affiliate links — we earn a commission at no extra cost to you. Prices verified {esc(LAST_REVIEWED)}; confirm on vendor site before buying.
    </div>"""

def footer_fragment() -> str:
    return f"""<footer>
      <div class="footer-inner">
        <a href="index.html" class="footer-logo">SaaS<span>Scouter</span></a>
        <p class="footer-text">
          Some links are affiliate links — we earn a commission if you purchase, at no extra cost to you.
          Prices and features change; always confirm on the vendor's site before buying. Last reviewed {esc(LAST_REVIEWED)}.
          <br>© {date.today().year} {esc(SITE_NAME)} · {esc(AUTHOR)}
        </p>
      </div>
    </footer>"""

def head_block(*, title: str, description: str, path: str, extra_css: str = "") -> str:
    canon = canonical_href(path)
    return f"""  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{esc(description)}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canon)}">
  <link rel="canonical" href="{esc(canon)}">
  {font_link()}
  <title>{esc(title)}</title>
  <style>{SHARED_CSS}{extra_css}</style>"""


# ── COMPARISON PAGE ───────────────────────────────────────────────────────────

COMP_CSS = """
    .page { max-width: 1100px; margin: 0 auto; padding: 0 clamp(1rem,4vw,3rem); }
    .comp-hero { padding: clamp(3rem,7vw,5rem) 0 clamp(2rem,4vw,3rem); border-bottom: 1px solid var(--border); animation: fadeUp 0.4s ease both; }
    .category-tag {
      display: inline-flex; align-items: center; gap: 0.5rem;
      background: var(--accent-muted); color: var(--accent);
      font-size: 0.7rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase;
      padding: 0.3rem 0.75rem; border-radius: 100px; text-decoration: none; margin-bottom: 1.25rem;
    }
    .comp-title {
      font-family: 'Syne', sans-serif; font-weight: 800;
      font-size: clamp(2rem,5vw,3.5rem); line-height: 1.05; letter-spacing: -0.03em;
    }
    .comp-title .vs { color: var(--muted); font-weight: 700; font-size: 0.6em; vertical-align: middle; margin: 0 0.25em; }
    .comp-intro { margin-top: 1rem; font-size: 1.05rem; color: var(--muted); max-width: 620px; line-height: 1.65; }
    .comp-meta { margin-top: 0.75rem; font-size: 0.75rem; color: var(--muted); }
    .two-up {
      display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;
      padding: clamp(2rem,5vw,3.5rem) 0; border-bottom: 1px solid var(--border);
    }
    .tool-card {
      background: var(--card); border: 1px solid var(--border); border-radius: 16px;
      padding: 1.75rem; display: flex; flex-direction: column; gap: 1rem;
    }
    .tool-card.winner { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), 0 4px 24px rgba(232,82,26,0.08); }
    .winner-badge {
      display: inline-flex; align-items: center; gap: 0.35rem;
      background: var(--accent); color: #fff; font-size: 0.65rem; font-weight: 600;
      letter-spacing: 0.08em; text-transform: uppercase; padding: 0.25rem 0.65rem; border-radius: 100px; width: fit-content;
    }
    .tool-name { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.5rem; color: var(--ink); }
    .tool-tagline { font-size: 0.82rem; color: var(--muted); }
    .tool-price {
      font-size: 0.85rem; color: var(--muted);
      padding: 0.5rem 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
    }
    .tool-price strong { color: var(--ink); font-size: 1rem; }
    .tool-summary { font-size: 0.875rem; color: var(--ink); line-height: 1.65; }
    .tool-cta {
      display: inline-flex; align-items: center; gap: 0.5rem;
      background: var(--ink); color: var(--paper); font-size: 0.82rem; font-weight: 500;
      padding: 0.7rem 1.25rem; border-radius: 10px; text-decoration: none;
      transition: background 0.15s; width: fit-content; margin-top: auto;
    }
    .tool-cta:hover { background: var(--accent); }
    .tool-cta.secondary { background: transparent; color: var(--ink); border: 1.5px solid var(--border); }
    .tool-cta.secondary:hover { border-color: var(--ink); background: transparent; }
    .section-wrap { padding: clamp(2rem,4vw,3rem) 0; border-bottom: 1px solid var(--border); }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    thead { background: #f5f3f0; }
    thead th { padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--muted); }
    thead th:first-child { color: var(--ink); }
    tbody tr { border-top: 1px solid var(--border); }
    tbody tr:hover { background: #f9f8f6; }
    td { padding: 0.85rem 1rem; color: var(--ink); vertical-align: top; }
    td:first-child { color: var(--muted); font-size: 0.8rem; font-weight: 500; white-space: nowrap; }
    .check { color: var(--green); font-weight: 600; }
    .cross { color: var(--red); }
    .partial { color: #b45309; }
    .pros-cons-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
    .pc-block h4 { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.95rem; margin-bottom: 1rem; }
    .pc-list { list-style: none; display: flex; flex-direction: column; gap: 0.6rem; }
    .pc-list li { display: flex; gap: 0.6rem; font-size: 0.85rem; color: var(--ink); align-items: flex-start; }
    .pc-list li::before { content: attr(data-icon); flex-shrink: 0; margin-top: 0.1rem; font-size: 0.75rem; }
    .verdict-section { background: var(--ink); border-radius: 20px; padding: clamp(2rem,5vw,3.5rem); margin: clamp(2rem,4vw,3rem) 0; }
    .verdict-label { font-size: 0.65rem; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: rgba(255,255,255,0.35); margin-bottom: 1rem; }
    .verdict-split { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
    .verdict-pick { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 800; color: var(--accent); margin-bottom: 0.5rem; }
    .verdict-if { font-size: 0.68rem; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(255,255,255,0.35); margin-bottom: 0.4rem; }
    .verdict-text { font-size: 0.875rem; color: rgba(255,255,255,0.7); line-height: 1.65; }
    .verdict-divider { width: 1px; background: rgba(255,255,255,0.08); }
    .related-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.75rem; }
    .related-card {
      background: var(--card); border: 1px solid var(--border); border-radius: 12px;
      padding: 1rem 1.25rem; text-decoration: none; color: inherit;
      display: flex; align-items: center; justify-content: space-between;
      gap: 1rem; font-size: 0.875rem; font-weight: 500; transition: border-color 0.15s;
    }
    .related-card:hover { border-color: var(--accent); }
    .related-card span { color: var(--accent); }
    @media (max-width: 600px) {
      .two-up { grid-template-columns: 1fr; }
      .pros-cons-grid { grid-template-columns: 1fr; }
      .verdict-split { grid-template-columns: 1fr; }
      .verdict-divider { width: 100%; height: 1px; }
    }
"""

def render_comparison_page(
    t1: dict,
    t2: dict,
    *,
    all_pairs: list[tuple[str, str]],
    by_id: dict[str, dict],
) -> tuple[str, str]:
    a, b = sorted((t1["id"], t2["id"]))
    fname = comparison_filename(a, b)
    name1, name2 = t1["name"], t2["name"]

    cat1 = t1["category"]
    cat2 = t2["category"]
    cat_meta1 = CATEGORY_META[cat1]
    cat_meta2 = CATEGORY_META[cat2]

    # pick primary category for the breadcrumb tag
    primary_cat = cat1
    primary_meta = cat_meta1

    title = f"{name1} vs {name2} ({LAST_REVIEWED}) — Which is Better? | {SITE_NAME}"
    description = (
        f"{name1} vs {name2}: real pricing, feature breakdown, pros & cons, and a clear winner. "
        f"Updated {LAST_REVIEWED}."
    )

    # Determine "winner" (tool with higher average score, fallback to t1)
    def avg_score(t: dict) -> float:
        s = t.get("scores", {})
        vals = [v for v in s.values() if isinstance(v, (int, float))]
        return sum(vals) / len(vals) if vals else 0.0

    winner_id = a if avg_score(t1) >= avg_score(t2) else b
    # tool cards — winner gets the highlighted card
    ta_winner = t1 if t1["id"] == winner_id else t2
    ta_other  = t2 if t1["id"] == winner_id else t1

    def tool_card_html(t: dict, is_winner: bool) -> str:
        badge = '<span class="winner-badge">★ Editor\'s pick</span>' if is_winner else ""
        cta_class = "tool-cta" if is_winner else "tool-cta secondary"
        winner_class = " winner" if is_winner else ""
        price_display = t["price"].replace("(verify on site)", "").replace("(starter; verify on site)", "").strip().rstrip(";").strip()
        return f"""<div class="tool-card{winner_class}">
          {badge}
          <div class="tool-name">{esc(t['name'])}</div>
          <div class="tool-tagline">{esc(t['bestFor'])}</div>
          <div class="tool-price">Starts at <strong>{esc(price_display)}</strong></div>
          <div style="display:flex;flex-direction:column;gap:0.5rem;">
            {score_bars_html(t)}
          </div>
          <p class="tool-summary">{esc(t.get('verdict','').capitalize())}</p>
          <a href="{esc(cta_url(t))}" class="{cta_class}" target="_blank" rel="noopener sponsored">
            Try {esc(t['name'])} →
          </a>
        </div>"""

    card1 = tool_card_html(t1, t1["id"] == winner_id)
    card2 = tool_card_html(t2, t2["id"] == winner_id)

    # Feature rows from features string
    def feat_list(features: str) -> list[str]:
        return [p.strip() for p in features.split(",") if p.strip()][:6]

    f1 = feat_list(t1["features"])
    f2 = feat_list(t2["features"])
    row_count = max(len(f1), len(f2), 1)
    feature_rows = []
    for i in range(row_count):
        c1 = f1[i] if i < len(f1) else "—"
        c2 = f2[i] if i < len(f2) else "—"
        feature_rows.append(
            f"<tr><td>{esc(c1)}</td><td>{esc(c2)}</td></tr>"
        )

    # Pros bullets
    def pro_bullets(pros_str: str, color: str) -> str:
        items = [p.strip() for p in pros_str.split(";") if p.strip()]
        if not items:
            items = [pros_str]
        return "\n".join(f'<li data-icon="✓" style="color:{color}">{esc(item)}</li>' for item in items)

    def con_bullets(cons_str: str) -> str:
        items = [p.strip() for p in cons_str.split(";") if p.strip()]
        if not items:
            items = [cons_str]
        return "\n".join(f'<li data-icon="✗" style="color:var(--red)">{esc(item)}</li>' for item in items)

    # Verdict pick/avoid text
    pick1  = t1.get("pick_if", f"Your primary need is {t1['bestFor']}.")
    avoid1 = t1.get("avoid_if", t1.get("cons", ""))
    pick2  = t2.get("pick_if", f"Your primary need is {t2['bestFor']}.")
    avoid2 = t2.get("avoid_if", t2.get("cons", ""))

    # Related comparisons
    related_links = []
    for x, y in all_pairs:
        if x == a and y == b:
            continue
        if a in (x, y) or b in (x, y):
            ox, oy = by_id[x]["name"], by_id[y]["name"]
            fn = comparison_filename(x, y)
            related_links.append(
                f'<a href="{esc(fn)}" class="related-card">{esc(ox)} vs {esc(oy)} <span>→</span></a>'
            )
    related_links = related_links[:8]

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_block(title=title, description=description, path=fname, extra_css=COMP_CSS)}
</head>
<body>
{nav_fragment(f'<div class="breadcrumb"><a href="index.html">Home</a> › <a href="hub-{esc(primary_cat)}.html">{esc(primary_meta["title"])}</a> › {esc(name1)} vs {esc(name2)}</div>')}

  <div class="page">

    <div class="comp-hero">
      <a href="hub-{esc(primary_cat)}.html" class="category-tag">{esc(primary_meta["icon"])} {esc(primary_meta["title"])}</a>
      <h1 class="comp-title">
        {esc(name1)} <span class="vs">vs</span> {esc(name2)}
      </h1>
      <p class="comp-intro">
        Both {esc(name1)} and {esc(name2)} solve real problems — but for very different buyers.
        Here's a no-fluff breakdown so you can decide in under 5 minutes.
      </p>
      <p class="comp-meta">Last reviewed {esc(LAST_REVIEWED)} · Prices verified on vendor sites</p>
    </div>

    <div class="two-up">
      {card1}
      {card2}
    </div>

    <div class="section-wrap">
      <p class="section-label">Feature comparison</p>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th style="width:30%">Feature</th>
              <th>{esc(name1)}</th>
              <th>{esc(name2)}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Best for</td>
              <td class="check">{esc(t1['bestFor'])}</td>
              <td class="check">{esc(t2['bestFor'])}</td>
            </tr>
            <tr>
              <td>Starting price</td>
              <td>{esc(t1['price'].replace('(verify on site)','').strip().rstrip(';').strip())}</td>
              <td>{esc(t2['price'].replace('(verify on site)','').strip().rstrip(';').strip())}</td>
            </tr>
            {"".join(feature_rows)}
          </tbody>
        </table>
      </div>
    </div>

    <div class="section-wrap">
      <p class="section-label">Pros & cons</p>
      <div class="pros-cons-grid">
        <div class="pc-block">
          <h4>{esc(name1)}</h4>
          <ul class="pc-list">
            {pro_bullets(t1['pros'], 'var(--green)')}
            {con_bullets(t1['cons'])}
          </ul>
        </div>
        <div class="pc-block">
          <h4>{esc(name2)}</h4>
          <ul class="pc-list">
            {pro_bullets(t2['pros'], 'var(--green)')}
            {con_bullets(t2['cons'])}
          </ul>
        </div>
      </div>
    </div>

    <div class="verdict-section">
      <p class="verdict-label">The verdict</p>
      <div class="verdict-split">
        <div>
          <p class="verdict-if">Pick {esc(name1)} if…</p>
          <p class="verdict-pick">{esc(t1['bestFor'])}</p>
          <p class="verdict-text">{esc(pick1)}</p>
        </div>
        <div class="verdict-divider"></div>
        <div>
          <p class="verdict-if">Pick {esc(name2)} if…</p>
          <p class="verdict-pick">{esc(t2['bestFor'])}</p>
          <p class="verdict-text">{esc(pick2)}</p>
        </div>
      </div>
    </div>

    <div class="section-wrap" style="border-bottom:none;">
      <p class="section-label">Related comparisons</p>
      <div class="related-grid">
        {"".join(related_links) if related_links else "<p style='font-size:.875rem;color:var(--muted)'>More comparisons coming soon.</p>"}
      </div>
    </div>

  </div>

{footer_fragment()}
</body>
</html>"""

    return fname, page


# ── HUB PAGE ─────────────────────────────────────────────────────────────────

HUB_CSS = """
    .hub-page { max-width: 1100px; margin: 0 auto; padding: 0 clamp(1rem,4vw,3rem); }
    .hub-hero { padding: clamp(3rem,6vw,4.5rem) 0 clamp(2rem,4vw,3rem); border-bottom: 1px solid var(--border); animation: fadeUp 0.4s ease both; }
    .hub-title { font-family: 'Syne', sans-serif; font-weight: 800; font-size: clamp(2rem,5vw,3rem); letter-spacing:-0.03em; }
    .hub-blurb { margin-top: .75rem; font-size: 1.05rem; color: var(--muted); max-width: 560px; line-height:1.65; }
    .tools-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(260px,1fr)); gap: 1rem; }
    .tool-hub-card {
      background: var(--card); border: 1px solid var(--border); border-radius: 16px;
      padding: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem;
    }
    .tool-hub-name { font-family:'Syne',sans-serif; font-weight:700; font-size:1.1rem; color:var(--ink); }
    .tool-hub-use  { font-size:.78rem; color:var(--muted); }
    .tool-hub-price { font-size:.82rem; color:var(--muted); border-top:1px solid var(--border); padding-top:.65rem; }
    .tool-hub-price strong { color:var(--ink); }
    .tool-hub-cta {
      display:inline-flex; align-items:center; gap:.4rem;
      background:var(--ink); color:var(--paper); font-size:.78rem; font-weight:500;
      padding:.55rem 1rem; border-radius:8px; text-decoration:none;
      transition:background .15s; width:fit-content; margin-top:auto;
    }
    .tool-hub-cta:hover { background:var(--accent); }
    .comp-list { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:.65rem; }
    .comp-list-item {
      background:var(--card); border:1px solid var(--border); border-radius:10px;
      padding:.85rem 1.1rem; text-decoration:none; color:inherit;
      display:flex; align-items:center; justify-content:space-between;
      font-size:.875rem; font-weight:500; transition:border-color .15s;
    }
    .comp-list-item:hover { border-color:var(--accent); }
    .comp-list-item span { color:var(--accent); }
    .hub-section { padding:clamp(2rem,4vw,3rem) 0; border-bottom:1px solid var(--border); }
    .hub-section:last-child { border-bottom:none; }
"""

def render_hub(
    category: str,
    tools_in_cat: list[dict],
    pairs_in_cat: list[tuple[str, str]],
    by_id: dict[str, dict],
    all_pairs: list[tuple[str, str]],
) -> tuple[str, str]:
    meta = CATEGORY_META[category]
    fname = f"hub-{category}.html"
    title = f"{meta['title']} — Best Tools & Comparisons ({LAST_REVIEWED}) | {SITE_NAME}"
    description = f"{meta['blurb']} Curated comparisons with pricing and clear verdicts. Updated {LAST_REVIEWED}."

    tool_cards = []
    for t in sorted(tools_in_cat, key=lambda x: x["name"]):
        price_display = t["price"].replace("(verify on site)", "").replace("(starter; verify on site)", "").strip().rstrip(";").strip()
        tool_cards.append(f"""<div class="tool-hub-card">
          <div class="tool-hub-name">{esc(t['name'])}</div>
          <div class="tool-hub-use">{esc(t['bestFor'])}</div>
          <div style="display:flex;flex-direction:column;gap:.4rem;">{score_bars_html(t)}</div>
          <div class="tool-hub-price">Starts at <strong>{esc(price_display)}</strong></div>
          <a href="{esc(cta_url(t))}" class="tool-hub-cta" target="_blank" rel="noopener sponsored">
            Try {esc(t['name'])} →
          </a>
        </div>""")

    compare_items = []
    for x, y in pairs_in_cat:
        ta, tb = by_id[x], by_id[y]
        fn = comparison_filename(x, y)
        compare_items.append(
            f'<a href="{esc(fn)}" class="comp-list-item">{esc(ta["name"])} vs {esc(tb["name"])} <span>→</span></a>'
        )

    t_ids = {t["id"] for t in tools_in_cat}
    cross_items = []
    for x, y in all_pairs:
        if by_id[x]["category"] == by_id[y]["category"]:
            continue
        if x in t_ids or y in t_ids:
            ta, tb = by_id[x], by_id[y]
            fn = comparison_filename(x, y)
            cross_items.append(
                f'<a href="{esc(fn)}" class="comp-list-item">{esc(ta["name"])} vs {esc(tb["name"])} <span>→</span></a>'
            )

    cross_section = ""
    if cross_items:
        cross_section = f"""<div class="hub-section">
          <p class="section-label">Crossover comparisons</p>
          <div class="comp-list">{"".join(cross_items)}</div>
        </div>"""

    breadcrumb = f'<div class="breadcrumb"><a href="index.html">Home</a> › {esc(meta["title"])}</div>'

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_block(title=title, description=description, path=fname, extra_css=HUB_CSS)}
</head>
<body>
{nav_fragment(breadcrumb)}

  <div class="hub-page">
    <div class="hub-hero">
      <h1 class="hub-title">{esc(meta['icon'])} {esc(meta['title'])}</h1>
      <p class="hub-blurb">{esc(meta['blurb'])}</p>
    </div>

    <div class="hub-section">
      <p class="section-label">Tools in this category</p>
      <div class="tools-grid">{"".join(tool_cards)}</div>
    </div>

    <div class="hub-section">
      <p class="section-label">Head-to-head comparisons</p>
      <div class="comp-list">
        {"".join(compare_items) if compare_items else '<p style="font-size:.875rem;color:var(--muted)">Only one tool in this category — check crossover comparisons below.</p>'}
      </div>
    </div>

    {cross_section}

    <div style="padding:2rem 0;">
      <a href="index.html" style="font-size:.875rem;color:var(--accent);text-decoration:none;">← Back to all categories</a>
    </div>
  </div>

{footer_fragment()}
</body>
</html>"""

    return fname, page


# ── INDEX PAGE ───────────────────────────────────────────────────────────────

INDEX_CSS = """
    .hero {
      padding: clamp(4rem,10vw,7rem) clamp(1rem,4vw,3rem) clamp(3rem,6vw,4.5rem);
      border-bottom: 1px solid var(--border); position: relative; overflow: hidden;
    }
    .hero::before {
      content: ''; position: absolute; top: -80px; right: -100px;
      width: 600px; height: 600px;
      background: radial-gradient(circle, #fde8df 0%, transparent 65%);
      pointer-events: none;
    }
    .hero-inner { max-width: 1200px; margin: 0 auto; position: relative; }
    .eyebrow {
      display: inline-flex; align-items: center; gap: .5rem;
      background: var(--accent-muted); color: var(--accent);
      font-size: .7rem; font-weight: 500; letter-spacing: .1em; text-transform: uppercase;
      padding: .3rem .85rem; border-radius: 100px; margin-bottom: 1.5rem;
    }
    .eyebrow::before { content: ''; width: 6px; height: 6px; background: var(--accent); border-radius: 50%; }
    h1 {
      font-family: 'Syne', sans-serif; font-weight: 800;
      font-size: clamp(2.4rem,6vw,4.5rem); line-height: 1.05; letter-spacing: -.03em;
      max-width: 820px;
    }
    h1 em { color: var(--accent); font-style: normal; }
    .hero-sub { margin-top: 1.5rem; font-size: 1.1rem; color: var(--muted); max-width: 560px; line-height: 1.65; }
    .hero-meta { margin-top: .75rem; font-size: .78rem; color: var(--muted); }
    .hero-meta strong { color: var(--ink); }
    .hero-inner > * { animation: fadeUp .5s ease both; }
    .hero-inner > *:nth-child(1) { animation-delay:.05s; }
    .hero-inner > *:nth-child(2) { animation-delay:.12s; }
    .hero-inner > *:nth-child(3) { animation-delay:.18s; }
    .hero-inner > *:nth-child(4) { animation-delay:.24s; }
    .idx-section { padding: clamp(3rem,6vw,4.5rem) clamp(1rem,4vw,3rem); border-bottom: 1px solid var(--border); }
    .idx-section:last-of-type { border-bottom: none; }
    .idx-inner { max-width: 1200px; margin: 0 auto; }
    .categories-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1px; background: var(--border); border: 1px solid var(--border);
      border-radius: 16px; overflow: hidden;
    }
    .cat-card {
      background: var(--card); padding: 1.75rem 1.5rem; text-decoration: none; color: inherit;
      transition: background .15s; display: flex; flex-direction: column; gap: .5rem;
    }
    .cat-card:hover { background: #f5f3f0; }
    .cat-icon { font-size: 1.5rem; margin-bottom: .25rem; display: block; }
    .cat-card h3 { font-family: 'Syne', sans-serif; font-weight: 700; font-size: .95rem; line-height: 1.25; }
    .cat-card p { font-size: .78rem; color: var(--muted); line-height: 1.5; flex: 1; }
    .cat-meta { font-size: .7rem; color: var(--accent); font-weight: 500; margin-top: .5rem; }
    .picks-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px,1fr)); gap: 1.5rem; }
    .pick-card {
      background: #1a1917; border: 1px solid #2a2825; border-radius: 16px;
      padding: 1.75rem; display: flex; flex-direction: column; gap: 1rem;
    }
    .pick-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .pick-name { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.1rem; color: #fff; }
    .pick-use { font-size: .75rem; color: rgba(255,255,255,.4); margin-top: .15rem; }
    .pick-score { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2rem; color: var(--accent); line-height: 1; flex-shrink: 0; }
    .pick-score span { font-size: .72rem; font-weight: 400; color: rgba(255,255,255,.35); }
    .pick-verdict { font-size: .85rem; color: rgba(255,255,255,.75); line-height: 1.6; border-left: 3px solid var(--accent); padding-left: .85rem; }
    .pick-price { font-size: .78rem; color: rgba(255,255,255,.4); }
    .pick-price strong { color: rgba(255,255,255,.7); }
    .pick-cta {
      display: inline-flex; align-items: center; gap: .5rem;
      background: var(--accent); color: #fff; font-size: .8rem; font-weight: 500;
      padding: .6rem 1.1rem; border-radius: 8px; text-decoration: none;
      transition: opacity .15s; width: fit-content; margin-top: auto;
    }
    .pick-cta:hover { opacity: .85; }
    .comps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: .75rem; }
    .comp-card {
      background: var(--card); border: 1px solid var(--border); border-radius: 12px;
      padding: 1.1rem 1.4rem; text-decoration: none; color: inherit;
      display: flex; align-items: center; justify-content: space-between; gap: 1rem;
      transition: border-color .15s, box-shadow .15s;
    }
    .comp-card:hover { border-color: var(--accent); box-shadow: 0 2px 12px rgba(232,82,26,.08); }
    .comp-names { font-weight: 500; font-size: .9rem; }
    .comp-tag { font-size: .68rem; color: var(--muted); margin-top: .2rem; }
    .comp-arrow { color: var(--accent); font-size: 1rem; flex-shrink: 0; opacity: 0; transform: translateX(-4px); transition: opacity .15s, transform .15s; }
    .comp-card:hover .comp-arrow { opacity: 1; transform: translateX(0); }
    @media (max-width: 640px) { .categories-grid { grid-template-columns: 1fr 1fr; } }
"""

def render_index(
    *,
    by_id: dict[str, dict],
    pairs: list[tuple[str, str]],
    cat_to_tools: dict[str, list[dict]],
) -> tuple[str, str]:
    fname = "index.html"
    title = f"{SITE_NAME} · Find the Right SaaS Tool, Fast"
    description = (
        "Curated SaaS comparisons with clear winners. Real pricing, honest tradeoffs, "
        f"and a verdict on every page. Updated {LAST_REVIEWED}."
    )

    n_tools = len(by_id)
    n_cats  = len(cat_to_tools)
    n_comps = len(pairs)

    # Category cards
    cat_cards = []
    for cat in sorted(cat_to_tools.keys()):
        meta = CATEGORY_META[cat]
        n_t = len(cat_to_tools[cat])
        n_p = sum(1 for x, y in pairs if by_id[x]["category"] == cat or by_id[y]["category"] == cat)
        cat_cards.append(f"""<a href="hub-{esc(cat)}.html" class="cat-card">
          <span class="cat-icon">{esc(meta['icon'])}</span>
          <h3>{esc(meta['title'])}</h3>
          <p>{esc(meta['blurb'])}</p>
          <span class="cat-meta">{n_t} tools · {n_p} comparisons →</span>
        </a>""")

    # Top picks (top 3 by avg score)
    def avg_score(t: dict) -> float:
        s = t.get("scores", {})
        vals = [v for v in s.values() if isinstance(v, (int, float))]
        return sum(vals) / len(vals) if vals else 0.0

    top3 = sorted(by_id.values(), key=avg_score, reverse=True)[:3]

    pick_cards = []
    for t in top3:
        score = round(avg_score(t), 1)
        price_display = t["price"].replace("(verify on site)","").replace("(starter; verify on site)","").strip().rstrip(";").strip()
        pick_cards.append(f"""<div class="pick-card">
          <div class="pick-header">
            <div>
              <div class="pick-name">{esc(t['name'])}</div>
              <div class="pick-use">{esc(t['bestFor'])}</div>
            </div>
            <div class="pick-score">{score}<span>/10</span></div>
          </div>
          <p class="pick-verdict">{esc(t.get('verdict','').capitalize())}</p>
          <div class="pick-price">Starts at <strong>{esc(price_display)}</strong></div>
          <a href="{esc(cta_url(t))}" class="pick-cta" target="_blank" rel="noopener sponsored">
            Try {esc(t['name'])} →
          </a>
        </div>""")

    # All comparison cards
    comp_cards = []
    for x, y in pairs:
        ta, tb = by_id[x], by_id[y]
        fn = comparison_filename(x, y)
        cat_x = CATEGORY_META[ta["category"]]["title"]
        cat_y = CATEGORY_META[tb["category"]]["title"]
        tag = cat_x if cat_x == cat_y else f"{cat_x} + {cat_y}"
        comp_cards.append(f"""<a href="{esc(fn)}" class="comp-card">
          <div>
            <div class="comp-names">{esc(ta['name'])} vs {esc(tb['name'])}</div>
            <div class="comp-tag">{esc(tag)}</div>
          </div>
          <span class="comp-arrow">→</span>
        </a>""")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_block(title=title, description=description, path=fname, extra_css=INDEX_CSS)}
</head>
<body>
{nav_fragment()}

  <header class="hero">
    <div class="hero-inner">
      <span class="eyebrow">Updated {esc(LAST_REVIEWED)}</span>
      <h1>Find the <em>right</em> SaaS tool.<br>Skip the hype.</h1>
      <p class="hero-sub">Head-to-head comparisons with real pricing, honest tradeoffs, and a clear verdict — so you spend 5 minutes here instead of 5 hours on Reddit.</p>
      <p class="hero-meta">Tracking <strong>{n_tools} tools</strong> across <strong>{n_cats} categories</strong> · <strong>{n_comps} comparisons</strong> · Prices cross-checked against vendor sites</p>
    </div>
  </header>

  <section class="idx-section" id="categories">
    <div class="idx-inner">
      <p class="section-label">Browse by category</p>
      <div class="categories-grid">{"".join(cat_cards)}</div>
    </div>
  </section>

  <section class="idx-section" style="background: var(--ink);">
    <div class="idx-inner">
      <p class="section-label" style="color:rgba(255,255,255,.3);">Editor's top picks</p>
      <div class="picks-grid">{"".join(pick_cards)}</div>
    </div>
  </section>

  <section class="idx-section" id="comparisons">
    <div class="idx-inner">
      <p class="section-label">All comparisons</p>
      <div class="comps-grid">{"".join(comp_cards)}</div>
    </div>
  </section>

{footer_fragment()}
</body>
</html>"""

    return fname, page


# ── SITEMAP ───────────────────────────────────────────────────────────────────

def write_sitemap(paths: list[str]) -> None:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    if BASE_URL:
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        for p in sorted(set(paths)):
            loc = f"{BASE_URL}/{p}".replace("/./", "/")
            lines.append("  <url>")
            lines.append(f"    <loc>{esc(loc)}</loc>")
            lines.append("  </url>")
        lines.append("</urlset>")
    else:
        lines.append("<!-- Set env SAAS_SCOUTER_SITE_URL and re-run to get absolute URLs -->")
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" />')
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def cleanup_old_comparisons(keep: set[str]) -> None:
    for path in glob.glob("*-vs-*.html"):
        if path not in keep:
            os.remove(path)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    global BASE_URL
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    BASE_URL = resolve_base_url(root)

    with open("tools.json", encoding="utf-8") as f:
        tools = json.load(f)

    by_id = build_tool_index(tools)
    pairs = curated_pairs(by_id)

    cat_to_tools: dict[str, list[dict]] = {}
    for t in tools:
        cat_to_tools.setdefault(t["category"], []).append(t)

    outputs: dict[str, str] = {}
    keep_names: set[str] = set()

    # Comparison pages
    for a, b in pairs:
        fname, html_out = render_comparison_page(
            by_id[a], by_id[b], all_pairs=pairs, by_id=by_id
        )
        outputs[fname] = html_out
        keep_names.add(fname)

    cleanup_old_comparisons(keep_names)

    # Hub pages
    for cat, tools_in_cat in cat_to_tools.items():
        pairs_in_cat = [
            (x, y) for x, y in pairs
            if by_id[x]["category"] == cat and by_id[y]["category"] == cat
        ]
        fname, html_out = render_hub(cat, tools_in_cat, pairs_in_cat, by_id, all_pairs=pairs)
        outputs[fname] = html_out

    # Index
    idx_fname, idx_html = render_index(by_id=by_id, pairs=pairs, cat_to_tools=cat_to_tools)
    outputs[idx_fname] = idx_html

    # Write all files
    for fname, html_out in outputs.items():
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html_out)

    # Sitemap
    sitemap_paths = sorted(outputs.keys())
    if os.path.exists("gohighlevel.html"):
        sitemap_paths.append("gohighlevel.html")
    write_sitemap(sorted(set(sitemap_paths)))

    print(f"✓ Wrote {len(outputs)} pages ({len(pairs)} comparisons, {len(cat_to_tools)} hubs, 1 index)")
    print(f"✓ Sitemap updated — {len(sitemap_paths)} URLs")
    if not BASE_URL:
        print("  ⚠ Set SAAS_SCOUTER_SITE_URL env var or site.json base_url for absolute sitemap URLs")


if __name__ == "__main__":
    main()
