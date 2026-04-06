"""
Generate SaaS Scouter static pages from tools.json.
Run from repo root: python generate_pages.py
"""
from __future__ import annotations

import glob
import html
import itertools
import json
import os
from datetime import date

LAST_REVIEWED = "April 2026"
SITE_NAME = "SaaS Scouter"
AUTHOR = "Andrew Stankus"
# Filled in main() from env (SAAS_SCOUTER_SITE_URL or CI SITE_URL) or site.json.
BASE_URL = ""

# Extra high-intent pairs that span categories (not random cross-sells).
BRIDGE_PAIRS = [
    ("surferseo", "writesonic"),
    ("surferseo", "jasper"),
    ("descript", "canva"),
]

CATEGORY_META = {
    "ai-writing": {
        "title": "AI writing tools",
        "blurb": "Draft, edit, and scale marketing copy with models and workflows built for teams.",
    },
    "design-visual": {
        "title": "Design & AI imagery",
        "blurb": "Templates and AI generation for visuals, social assets, and campaign art.",
    },
    "crm-funnels": {
        "title": "CRM & funnel platforms",
        "blurb": "Capture leads, automate follow-up, and run funnels without duct-taping five tools.",
    },
    "seo": {
        "title": "SEO tooling",
        "blurb": "Research, briefs, and on-page optimization grounded in SERP data.",
    },
    "video-audio": {
        "title": "Video & podcast editing",
        "blurb": "Edit by transcript, clean audio, and ship episodes and clips faster.",
    },
}


def resolve_base_url(repo_root: str) -> str:
    """Absolute site origin for canonicals, Open Graph, and sitemap (no trailing slash)."""
    env = os.environ.get("SAAS_SCOUTER_SITE_URL", "").strip().rstrip("/")
    if env:
        return env
    site_json = os.path.join(repo_root, "site.json")
    if os.path.isfile(site_json):
        with open(site_json, encoding="utf-8") as f:
            data = json.load(f)
        return str(data.get("base_url", "")).strip().rstrip("/")
    return ""


def cta_url(tool: dict) -> str:
    """Outbound CTA: affiliate_link when set, otherwise vendor link."""
    aff = tool.get("affiliate_link")
    if isinstance(aff, str) and aff.strip():
        return aff.strip()
    return tool["link"]


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def feat_list(features: str) -> list[str]:
    parts = [p.strip() for p in features.split(",") if p.strip()]
    return parts[:6]


def canonical_href(path: str) -> str:
    if BASE_URL:
        return f"{BASE_URL}/{path}"
    return path


def head_common(
    *,
    title: str,
    description: str,
    path: str,
) -> str:
    canon = canonical_href(path)
    og_url = esc(canon)
    return f"""    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{esc(description)}">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{og_url}">
    <link rel="canonical" href="{og_url}">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>{esc(title)}</title>"""


def nav_fragment() -> str:
    return f"""
    <nav class="border-b border-slate-100 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-20">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap gap-4 justify-between items-center">
        <a href="index.html" class="text-lg font-bold tracking-tight text-slate-900 uppercase">SaaS<span class="text-blue-600">Scouter</span></a>
        <div class="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-500">
          <a href="index.html#categories" class="hover:text-slate-900">Categories</a>
          <a href="index.html#comparisons" class="hover:text-slate-900">All comparisons</a>
        </div>
      </div>
    </nav>"""


def footer_fragment() -> str:
    return f"""
    <footer class="mt-24 border-t border-slate-100 bg-slate-50">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-12 text-center text-sm text-slate-500 space-y-3">
        <p><strong class="text-slate-700">Disclosure:</strong> {SITE_NAME} earns commissions on some links at no extra cost to you. Prices and features change—confirm on the vendor site before buying.</p>
        <p class="text-xs text-slate-400">Last reviewed {LAST_REVIEWED}. Methodology: we summarize publicly listed positioning and common user tradeoffs—always try free trials when available.</p>
        <p class="text-xs text-slate-300">© {date.today().year} {SITE_NAME} · {esc(AUTHOR)}</p>
      </div>
    </footer>"""


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


def comparison_filename(a: str, b: str) -> str:
    x, y = sorted((a, b))
    return f"{x}-vs-{y}.html"


def render_comparison_page(
    t1: dict,
    t2: dict,
    *,
    all_pairs: list[tuple[str, str]],
    by_id: dict[str, dict],
) -> str:
    a, b = sorted((t1["id"], t2["id"]))
    fname = comparison_filename(a, b)
    name1, name2 = t1["name"], t2["name"]

    title = f"{name1} vs {name2} ({LAST_REVIEWED}) | {SITE_NAME}"
    description = (
        f"Compare {name1} and {name2}: pricing, pros & cons, and who to pick for "
        f"{t1['bestFor'].lower()} versus {t2['bestFor'].lower()}."
    )

    f1, f2 = feat_list(t1["features"]), feat_list(t2["features"])
    row_count = max(len(f1), len(f2), 1)
    rows = []
    for i in range(row_count):
        c1 = f1[i] if i < len(f1) else "—"
        c2 = f2[i] if i < len(f2) else "—"
        rows.append(
            f"<tr><td class='px-4 py-3 text-slate-700'>{esc(c1)}</td>"
            f"<td class='px-4 py-3 text-slate-700'>{esc(c2)}</td></tr>"
        )

    related: list[str] = []
    for x, y in all_pairs:
        if x == a and y == b:
            continue
        if a in (x, y) or b in (x, y):
            ox, oy = by_id[x]["name"], by_id[y]["name"]
            related.append(
                f'<li><a class="text-blue-600 hover:underline" href="{esc(comparison_filename(x, y))}">{esc(ox)} vs {esc(oy)}</a></li>'
            )
    related = related[:10]

    cat_links: list[str] = []
    c1, c2 = t1["category"], t2["category"]
    if c1 == c2:
        cat_links.append(
            f'<a class="text-blue-600 hover:underline" href="hub-{esc(c1)}.html">{esc(CATEGORY_META[c1]["title"])}</a>'
        )
    else:
        cat_links.append(
            f'<a class="text-blue-600 hover:underline" href="hub-{esc(c1)}.html">{esc(CATEGORY_META[c1]["title"])}</a>'
        )
        cat_links.append(
            f'<a class="text-blue-600 hover:underline" href="hub-{esc(c2)}.html">{esc(CATEGORY_META[c2]["title"])}</a>'
        )
    cat_breadcrumb = " · ".join(cat_links)

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_common(title=title, description=description, path=fname)}
</head>
<body class="bg-white text-slate-800 font-sans antialiased">
{nav_fragment()}
  <main class="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
    <p class="text-xs font-semibold uppercase tracking-widest text-blue-600 mb-4">{SITE_NAME}</p>
    <h1 class="text-3xl sm:text-4xl font-semibold tracking-tight text-slate-900 mb-4">{esc(name1)} <span class="text-slate-300 font-light">vs</span> {esc(name2)}</h1>
    <p class="text-slate-600 leading-relaxed max-w-2xl mb-2">
      Choosing between <strong>{esc(name1)}</strong> and <strong>{esc(name2)}</strong> usually comes down to
      <strong>{esc(t1["bestFor"])}</strong> versus <strong>{esc(t2["bestFor"])}</strong>—not which logo looks nicer.
    </p>
    <p class="text-xs text-slate-400 mb-10">Last reviewed {esc(LAST_REVIEWED)} · {cat_breadcrumb} · <a class="text-blue-600 hover:underline" href="index.html#categories">All categories</a></p>

    <section class="grid sm:grid-cols-2 gap-6 mb-12">
      <div class="rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h2 class="text-lg font-semibold text-slate-900 mb-1">{esc(name1)}</h2>
        <p class="text-sm text-slate-500 mb-4">{esc("Starts around " + t1["price"])}</p>
        <p class="text-slate-600 text-sm leading-relaxed mb-6">{esc(t1["verdict"].capitalize())}</p>
        <a href="{esc(cta_url(t1))}" target="_blank" rel="noopener sponsored" class="inline-flex items-center gap-2 text-blue-600 font-semibold hover:gap-3 transition-all">Visit {esc(name1)} <span aria-hidden="true">→</span></a>
      </div>
      <div class="rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h2 class="text-lg font-semibold text-slate-900 mb-1">{esc(name2)}</h2>
        <p class="text-sm text-slate-500 mb-4">{esc("Starts around " + t2["price"])}</p>
        <p class="text-slate-600 text-sm leading-relaxed mb-6">{esc(t2["verdict"].capitalize())}</p>
        <a href="{esc(cta_url(t2))}" target="_blank" rel="noopener sponsored" class="inline-flex items-center gap-2 text-blue-600 font-semibold hover:gap-3 transition-all">Visit {esc(name2)} <span aria-hidden="true">→</span></a>
      </div>
    </section>

    <section class="mb-12 overflow-x-auto">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">At a glance</h3>
      <table class="min-w-full text-sm border border-slate-200 rounded-xl overflow-hidden">
        <thead class="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-4 py-3 w-1/2">{esc(name1)}</th>
            <th class="px-4 py-3 w-1/2">{esc(name2)}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr><td class="px-4 py-3 font-medium text-slate-900">{esc(t1["bestFor"])}</td><td class="px-4 py-3 font-medium text-slate-900">{esc(t2["bestFor"])}</td></tr>
          {"".join(rows)}
        </tbody>
      </table>
    </section>

    <section class="grid sm:grid-cols-2 gap-8 mb-12">
      <div>
        <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-3">Pros · {esc(name1)}</h3>
        <p class="text-slate-700 leading-relaxed">{esc(t1["pros"])}</p>
        <h4 class="text-xs font-semibold text-slate-500 uppercase mt-4 mb-2">Cons</h4>
        <p class="text-slate-600 leading-relaxed">{esc(t1["cons"])}</p>
      </div>
      <div>
        <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-3">Pros · {esc(name2)}</h3>
        <p class="text-slate-700 leading-relaxed">{esc(t2["pros"])}</p>
        <h4 class="text-xs font-semibold text-slate-500 uppercase mt-4 mb-2">Cons</h4>
        <p class="text-slate-600 leading-relaxed">{esc(t2["cons"])}</p>
      </div>
    </section>

    <section class="rounded-2xl bg-slate-900 text-white p-8 sm:p-10">
      <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">Who should pick which?</h3>
      <p class="text-lg leading-snug font-medium">
        Choose <span class="text-blue-300">{esc(name1)}</span> if your primary job is <span class="text-slate-300">{esc(t1["bestFor"])}</span>.
        Choose <span class="text-blue-300">{esc(name2)}</span> if you are optimizing for <span class="text-slate-300">{esc(t2["bestFor"])}</span>.
      </p>
    </section>

    <section class="mt-12">
      <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-3">Related comparisons</h3>
      <ul class="text-sm text-slate-600 space-y-2 list-disc list-inside">{"".join(related) if related else "<li>No related pages in this slice yet.</li>"}</ul>
    </section>
  </main>
{footer_fragment()}
</body>
</html>"""

    return fname, body


def cross_category_pairs_for_tools(
    tool_ids: set[str], all_pairs: list[tuple[str, str]], by_id: dict[str, dict]
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for x, y in all_pairs:
        if by_id[x]["category"] == by_id[y]["category"]:
            continue
        if x in tool_ids or y in tool_ids:
            out.append((x, y))
    return out


def render_hub(
    category: str,
    tools_in_cat: list[dict],
    pairs_in_cat: list[tuple[str, str]],
    by_id: dict[str, dict],
    all_pairs: list[tuple[str, str]],
) -> str:
    meta = CATEGORY_META[category]
    fname = f"hub-{category}.html"
    title = f"{meta['title']} · Guides | {SITE_NAME}"
    description = f"{meta['blurb']} Browse tools and comparisons on {SITE_NAME}."
    tool_cards = []
    for t in sorted(tools_in_cat, key=lambda x: x["name"]):
        tool_cards.append(
            f"""<li class="rounded-xl border border-slate-200 p-5">
             <h3 class="font-semibold text-slate-900">{esc(t["name"])}</h3>
             <p class="text-sm text-slate-500 mt-1">{esc(t["bestFor"])}</p>
             <p class="text-sm text-slate-600 mt-3">{esc(t["price"])}</p>
             <a class="mt-4 inline-flex text-blue-600 text-sm font-semibold hover:underline" href="{esc(cta_url(t))}" target="_blank" rel="noopener sponsored">Visit site →</a>
           </li>"""
        )
    compare_links = []
    for a, b in pairs_in_cat:
        ta, tb = by_id[a], by_id[b]
        fn = comparison_filename(a, b)
        compare_links.append(
            f'<li><a class="text-blue-600 hover:underline" href="{esc(fn)}">{esc(ta["name"])} vs {esc(tb["name"])}</a></li>'
        )

    t_ids = {t["id"] for t in tools_in_cat}
    cross = cross_category_pairs_for_tools(t_ids, all_pairs, by_id)
    cross_links = []
    for a, b in cross:
        ta, tb = by_id[a], by_id[b]
        fn = comparison_filename(a, b)
        cross_links.append(
            f'<li><a class="text-blue-600 hover:underline" href="{esc(fn)}">{esc(ta["name"])} vs {esc(tb["name"])}</a></li>'
        )

    compare_block = (
        "".join(compare_links)
        if compare_links
        else "<li>No head-to-heads solely inside this category yet—see crossover guides below.</li>"
    )
    cross_block = (
        f"""
    <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4 mt-12">Stack & crossover comparisons</h2>
    <p class="text-sm text-slate-600 mb-3">Tools in this category are sometimes compared against adjacent products (e.g. SEO platform vs AI writer).</p>
    <ul class="text-sm text-slate-600 space-y-2 list-disc list-inside mb-6">{"".join(cross_links)}</ul>"""
        if cross_links
        else ""
    )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_common(title=title, description=description, path=fname)}
</head>
<body class="bg-white text-slate-800 font-sans antialiased">
{nav_fragment()}
  <main class="max-w-6xl mx-auto px-4 sm:px-6 py-12 sm:py-16">
    <p class="text-xs font-semibold uppercase tracking-widest text-blue-600 mb-3">{SITE_NAME}</p>
    <h1 class="text-3xl sm:text-4xl font-semibold tracking-tight text-slate-900 mb-4">{esc(meta["title"])}</h1>
    <p class="text-lg text-slate-600 max-w-2xl leading-relaxed mb-10">{esc(meta["blurb"])}</p>

    <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Tools in this category</h2>
    <ul class="grid sm:grid-cols-2 gap-4 mb-14">
      {"".join(tool_cards)}
    </ul>

    <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Head-to-head in this category</h2>
    <ul class="text-sm text-slate-600 space-y-2 list-disc list-inside mb-6">{compare_block}</ul>
    {cross_block}
    <p class="text-sm text-slate-500"><a href="index.html" class="text-blue-600 hover:underline">← Back to home</a></p>
  </main>
{footer_fragment()}
</body>
</html>"""
    return fname, body


def render_index(
    *,
    by_id: dict[str, dict],
    pairs: list[tuple[str, str]],
    cat_to_tools: dict[str, list[dict]],
) -> str:
    fname = "index.html"
    title = f"{SITE_NAME} · Honest SaaS comparisons ({LAST_REVIEWED})"
    description = (
        "Curated software comparisons for AI writing, CRM & funnels, SEO, design, and creator tools. "
        "Fewer pages, more detail—prices checked against vendor sites as of "
        f"{LAST_REVIEWED}."
    )

    # Category cards
    cat_cards = []
    for cat in sorted(cat_to_tools.keys()):
        meta = CATEGORY_META[cat]
        hub = f"hub-{cat}.html"
        n_tools = len(cat_to_tools[cat])
        cat_cards.append(
            f"""<a href="{esc(hub)}" id="cat-{esc(cat)}" class="group rounded-2xl border border-slate-200 p-6 hover:border-blue-200 hover:shadow-md transition">
          <h3 class="font-semibold text-slate-900 group-hover:text-blue-700">{esc(meta["title"])}</h3>
          <p class="text-sm text-slate-600 mt-2 leading-relaxed">{esc(meta["blurb"])}</p>
          <p class="text-xs text-slate-400 mt-4">{n_tools} tools · Open guide →</p>
        </a>"""
        )

    # All comparison links (compact)
    all_links = []
    for a, b in pairs:
        ta, tb = by_id[a], by_id[b]
        fn = comparison_filename(a, b)
        all_links.append(
            f'<li><a class="text-blue-600 hover:underline" href="{esc(fn)}">{esc(ta["name"])} vs {esc(tb["name"])}</a></li>'
        )

    pair_set = {tuple(p) for p in pairs}
    featured = [
        ("writesonic", "jasper"),
        ("hubspot", "gohighlevel"),
        ("surferseo", "writesonic"),
        ("canva", "midjourney"),
        ("copyai", "claude"),
        ("gohighlevel", "systemeio"),
    ]
    feat_items: list[str] = []
    for a, b in featured:
        key = tuple(sorted((a, b)))
        if key not in pair_set:
            continue
        ta, tb = by_id[a], by_id[b]
        fn = comparison_filename(a, b)
        feat_items.append(
            f'<li><a class="font-medium text-slate-800 hover:text-blue-600" href="{esc(fn)}">{esc(ta["name"])} vs {esc(tb["name"])}</a></li>'
        )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_common(title=title, description=description, path=fname)}
</head>
<body class="bg-white text-slate-900 font-sans antialiased">
{nav_fragment()}
  <header class="bg-gradient-to-b from-slate-50 to-white border-b border-slate-100">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-24">
      <p class="text-xs font-bold tracking-[0.2em] uppercase text-blue-600 mb-6">{SITE_NAME}</p>
      <h1 class="text-3xl sm:text-5xl font-semibold tracking-tight text-slate-900 leading-tight max-w-3xl">
        Software comparisons that respect your time.
      </h1>
      <p class="mt-6 text-lg text-slate-600 max-w-2xl leading-relaxed">
        We publish <strong>curated</strong> head-to-heads—mostly within the same category—so you don’t wade through random “CRM vs image generator” pages. Each guide includes pricing context, pros/cons, and a clear “pick this if…” summary.
      </p>
      <p class="mt-4 text-sm text-slate-500 max-w-2xl">
        Tracking {len(by_id)} products across {len(cat_to_tools)} categories; <strong>{len(pairs)}</strong> active comparisons (last reviewed {esc(LAST_REVIEWED)}).
      </p>
    </div>
  </header>

  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-14 space-y-16">
    <section class="rounded-2xl border border-amber-200 bg-amber-50/60 p-6 sm:p-8">
      <h2 class="text-sm font-bold uppercase tracking-widest text-amber-900/70 mb-2">Affiliate disclosure</h2>
      <p class="text-slate-800 leading-relaxed">
        Links may be affiliate links. We only make money if you choose to buy—our writeups call out tradeoffs either way. Add optional <code class="text-xs bg-white px-1 py-0.5 rounded border">affiliate_link</code> per product in <code class="text-xs bg-white px-1 py-0.5 rounded border">tools.json</code> (CTA buttons use that; <code class="text-xs bg-white px-1 py-0.5 rounded border">link</code> stays the clean homepage when you want separation).
      </p>
    </section>

    <section id="categories">
      <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-6">Browse by category</h2>
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {"".join(cat_cards)}
      </div>
    </section>

    <section>
      <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">Popular comparisons</h2>
      <ul class="grid sm:grid-cols-2 gap-3 text-sm">
        {"".join(feat_items)}
      </ul>
    </section>

    <section id="comparisons">
      <h2 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-4">All comparisons</h2>
      <ul class="columns-1 sm:columns-2 gap-8 text-sm space-y-2">
        {"".join(all_links)}
      </ul>
    </section>
  </div>
{footer_fragment()}
</body>
</html>"""
    return fname, body


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
        lines.append("<!-- Sitemap URLs need an absolute origin. Set env SAAS_SCOUTER_SITE_URL, e.g. https://yoursite.com")
        lines.append("     then re-run: python generate_pages.py")
        lines.append("     Generated paths:")
        for p in sorted(set(paths)):
            lines.append(f"       · {p}")
        lines.append("-->")
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" />')
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def cleanup_old_comparisons(keep: set[str]) -> None:
    for path in glob.glob("*-vs-*.html"):
        if path not in keep:
            os.remove(path)


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

    # Comparison pages
    keep_names: set[str] = set()
    for a, b in pairs:
        t1, t2 = by_id[a], by_id[b]
        fname, html_out = render_comparison_page(
            t1, t2, all_pairs=pairs, by_id=by_id
        )
        outputs[fname] = html_out
        keep_names.add(fname)

    cleanup_old_comparisons(keep_names)

    # Hub pages (only categories with >=1 tool; include SEO single-tool hub)
    for cat, tools_in_cat in cat_to_tools.items():
        pairs_in_cat = [
            (x, y)
            for x, y in pairs
            if by_id[x]["category"] == cat and by_id[y]["category"] == cat
        ]
        fname, html_out = render_hub(
            cat, tools_in_cat, pairs_in_cat, by_id, all_pairs=pairs
        )
        outputs[fname] = html_out

    idx_name, idx_html = render_index(
        by_id=by_id, pairs=pairs, cat_to_tools=cat_to_tools
    )
    outputs[idx_name] = idx_html

    for fname, html_out in outputs.items():
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html_out)

    sitemap_paths = sorted(outputs.keys())
    if os.path.exists("gohighlevel.html"):
        sitemap_paths.append("gohighlevel.html")
    write_sitemap(sorted(set(sitemap_paths)))

    print(f"Wrote {len(outputs)} pages, {len(pairs)} comparisons, cleaned stale *-vs-*.html")


if __name__ == "__main__":
    main()
