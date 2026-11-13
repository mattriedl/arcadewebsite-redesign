#!/usr/bin/env python3
"""Build arcadewebsite.com into the site/ folder.

    python3 build.py          # writes every page into site/
    python3 -m http.server -d site 8000   # then open http://localhost:8000

Everything comes from data/*.json (games, categories, homepage picks, featured rotation),
src/ (styles, scripts, tag manager) and public/ (game files, thumbnails), which is copied as-is.
Page URLs are the same as the live site, so links and search rankings carry over.
"""
import datetime as dt
import html
import json
import random
import re
import hashlib
import shutil
from pathlib import Path
from urllib.parse import unquote

from content import Copy, NOUN, clip

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE = "https://arcadewebsite.com"
BRAND = "ArcadeWebsite"
TODAY = dt.date.today()

e = lambda s: html.escape(str(s), quote=True)
load = lambda name: json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))

games = load("games.json")
cats = load("categories.json")
home_picks = load("home.json")
featured_cfg = load("featured.json")
G = {g["slug"]: g for g in games}
C = {c["slug"]: c for c in cats}
for c in cats:
    # live category order first, then anything else in that category
    seen = [s for s in c["order"] if s in G and G[s]["category"] == c["slug"]]
    rest = [g["slug"] for g in games if g["category"] == c["slug"] and g["slug"] not in seen]
    c["games"] = seen + rest
TOTAL = len(games)
# Real screenshots of the games (tools/capture_screenshots.py) replace the old text thumbnails,
# except ones checked by eye and rejected (data/screenshot-rejects.json).
_shots = load("screenshots.json") if (ROOT / "data/screenshots.json").exists() else {}
_rejected = set(load("screenshot-rejects.json")["rejected"]) if (ROOT / "data/screenshot-rejects.json").exists() else set()
_reviewed = set(load("screenshot-reviewed.json")["reviewed"]) if (ROOT / "data/screenshot-reviewed.json").exists() else set(_shots)
# Screenshots supplied by hand (data/screenshots-manual.json, files in public/screenshots/manual/) win over both.
_manual = load("screenshots-manual.json") if (ROOT / "data/screenshots-manual.json").exists() else {}
for g in games:
    s = g["slug"]
    if s in _manual and (ROOT / "public" / _manual[s].lstrip("/")).exists():
        g["thumbnail"] = _manual[s]
    elif s in _shots and s in _reviewed and s not in _rejected and (ROOT / "public" / _shots[s].lstrip("/")).exists():
        g["thumbnail"] = _shots[s]
COPY = Copy(games, cats, load("descriptions.json"))
# Hand-described (well-known) games first in each category, then the rest in the live site's order
for c in cats:
    c["games"] = [s for s in c["games"] if COPY.has_writeup(s)] + [s for s in c["games"] if not COPY.has_writeup(s)]

# Pages whose game file is byte-for-byte the same as another page's point search engines at one
# main page (rel=canonical), so they don't compete with each other. The main page is the one
# without "(Version N)" in its name, or the first alphabetically.
def _file_hash(g):
    p = ROOT / "public" / unquote(g["src"]).lstrip("/")
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else g["slug"]
_groups = {}
for g in games:
    _groups.setdefault(_file_hash(g), []).append(g["slug"])
CANONICAL = {}
for slugs in _groups.values():
    if len(slugs) > 1:
        main = sorted(slugs, key=lambda s: ("(Version" in G[s]["title"], s))[0]
        for s in slugs:
            if s != main:
                CANONICAL[s] = main
THUMB_W, THUMB_H = 400, 300

GTM_HEAD = (ROOT / "src/tag-manager.html").read_text(encoding="utf-8").strip()
GTM_BODY = (ROOT / "src/tag-manager-body.html").read_text(encoding="utf-8").strip()
# cache-buster for css/js: changes only when those files change
ASSET_V = __import__("hashlib").sha1(b"".join((ROOT / "src/assets" / f).read_bytes()
                                               for f in ("style.css", "app.js", "ads.js"))).hexdigest()[:10]

# ---------------------------------------------------------------------------------------------
# Icons (24x24, stroke). One per category, plus a few UI glyphs.
# ---------------------------------------------------------------------------------------------
def svg(body, fill=False):
    attrs = 'fill="currentColor"' if fill else 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    return f'<svg viewBox="0 0 24 24" {attrs} aria-hidden="true">{body}</svg>'

ICONS = {
    "arcade": svg('<rect x="3" y="13" width="18" height="8" rx="2"/><path d="M12 13V8"/><circle cx="12" cy="6" r="3"/><path d="M7 17h2M16 17h1"/>'),
    "platformer": svg('<path d="M3 20h5v-5h5v-5h5V5h3"/><circle cx="9" cy="8" r="2"/>'),
    "battle": svg('<path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6M16 16l4 4M19 21l2-2"/><path d="M9.5 17.5L21 6V3h-3L6.5 14.5"/><path d="M11 19l-6-6M8 16l-4 4M5 21l-2-2"/>'),
    "shooting": svg('<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>'),
    "racing": svg('<path d="M4 21V4"/><path d="M4 4h14l-2 4 2 4H4"/><path d="M9 4v8M14 4v8M4 8h14"/>'),
    "casual": svg('<circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/>'),
    "strategy": svg('<path d="M8 21h8M9 17h6l1 4H8z"/><path d="M10 17l-1-6h6l-1 6"/><path d="M9 11c-1.5-1-2-2.5-2-4a5 5 0 0 1 10 0c0 1.5-.5 3-2 4"/><path d="M12 2v3"/>'),
    "sports": svg('<circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/><path d="M5.6 5.6c3.5 3.5 3.5 9.3 0 12.8M18.4 5.6c-3.5 3.5-3.5 9.3 0 12.8"/>'),
    "puzzle": svg('<path d="M4 7h3a2 2 0 1 1 4 0h3v3a2 2 0 1 1 0 4v3h-3a2 2 0 1 0-4 0H4v-3a2 2 0 1 0 0-4z"/><path d="M14 10h3a2 2 0 1 1 0 4h-3"/>'),
    "idle-clicker": svg('<path d="M9 9l11 4-5 2-2 5z"/><path d="M5 3v3M3 5h3M9.5 3.5l-1 2M3.5 9.5l2-1"/>'),
    "horror": svg('<path d="M5 21V10a7 7 0 0 1 14 0v11l-2.5-2-2.5 2-2-2-2 2-2.5-2z"/><path d="M9.5 10h.01M14.5 10h.01"/>'),
    "minecraft": svg('<path d="M12 2l9 5v10l-9 5-9-5V7z"/><path d="M12 12l9-5M12 12v10M12 12L3 7"/>'),
}
I_SEARCH = svg('<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>')
I_LEFT = svg('<path d="M15 18l-6-6 6-6"/>')
I_RIGHT = svg('<path d="M9 18l6-6-6-6"/>')
I_PLAY = svg('<path d="M7 4l13 8-13 8z"/>', fill=True)
I_PAUSE = svg('<path d="M6 4h4v16H6zM14 4h4v16h-4z"/>', fill=True)
I_FULL = svg('<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>')
I_RELOAD = svg('<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>')
I_LINK = svg('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>')
LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#ff5c8a"/><stop offset="1" stop-color="#8e7cff"/></linearGradient></defs>'
        '<rect width="40" height="40" rx="11" fill="url(#lg)"/><circle cx="20" cy="20" r="11" fill="#ffc83d"/>'
        '<path d="M15 26l5-13 5 13M16.8 21.5h6.4" fill="none" stroke="#2a1d00" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')

# ---------------------------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------------------------
def head(title, desc, path, image=None, ld=None, robots=None, preload=None, canonical=None, image_alt=None):
    url = SITE + path
    canon = SITE + (canonical or path)
    image = image or "/thumbnails/" + "clslope.png"
    image_alt = image_alt or title
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False).replace("</", "<\\/")}</script>' for x in (ld or []))
    extra = f'<meta name="robots" content="{robots or "index,follow,max-image-preview:large,max-snippet:-1"}">'

    pre = f'<link rel="preload" as="image" href="{e(preload)}">' if preload else ""
    return f"""<!doctype html>
<html lang="en">
<head>
{GTM_HEAD}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{extra}
<link rel="canonical" href="{e(canon)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(SITE + image)}">
<meta property="og:image:width" content="{THUMB_W}">
<meta property="og:image:height" content="{THUMB_H}">
<meta property="og:image:alt" content="{e(image_alt)}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(SITE + image)}">
<meta name="theme-color" content="#12142e">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="New and featured games" href="/feed.xml">
<link rel="alternate" type="application/rss+xml" title="ArcadeWebsite blog" href="/blog/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=Unbounded:wght@500;600;700&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=Unbounded:wght@500;600;700&display=swap"></noscript>
<link rel="stylesheet" href="/assets/style.css?v={ASSET_V}">
{pre}{lds}
<script defer src="/assets/app.js?v={ASSET_V}"></script>
<script defer src="/assets/ads.js?v={ASSET_V}"></script>
</head>
"""


def header(active=None, cat=None):
    nav = [("/", "Home", "home"), ("/all-games/", "All games", "all"), ("/#categories", "Categories", "cats"), ("/blog/", "Blog", "blog")]
    cur = ' aria-current="page"'
    links = "".join('<a href="%s"%s>%s</a>' % (h, cur if k == active else "", t) for h, t, k in nav)
    bar = '<a class="all" href="/all-games/"%s>All %s games</a>' % (cur if active == "all" else "", f"{TOTAL:,}")
    for c in cats:
        cur = ' aria-current="page"' if c["slug"] == cat else ""
        bar += f'<a class="c-{c["slug"]}" href="/category/{c["slug"]}/"{cur}><span class="icon">{ICONS[c["slug"]]}</span>{e(c["name"])}</a>'
    return f"""<body>
{GTM_BODY}
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap topbar">
    <a class="brand" href="/" aria-label="{BRAND} home">{LOGO}<span class="brand-word">Arcade<span>Website</span></span></a>
    <nav class="topnav" aria-label="Main">{links}</nav>
    <form class="search" action="/search/" role="search">
      <label class="sr-only" for="q">Search games</label>
      <input id="q" type="search" name="q" placeholder="Search {TOTAL:,} games" autocomplete="off" required>
      <button aria-label="Search">{I_SEARCH}</button>
    </form>
  </div>
  <nav class="catbar" aria-label="Game categories"><div class="wrap">{bar}</div></nav>
</header>
"""


def footer():
    cl = "".join(f'<li><a href="/category/{c["slug"]}/">{e(c["name"])} games</a></li>' for c in cats)
    return f"""<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <a class="brand" href="/" aria-label="{BRAND} home">{LOGO}<span class="brand-word">Arcade<span>Website</span></span></a>
      <p>{TOTAL:,} free games you can play right in your browser. No downloads, no sign-up.</p>
    </div>
    <nav aria-label="Categories"><h2>Categories</h2><ul>{cl}</ul></nav>
    <nav aria-label="Site"><h2>Explore</h2><ul style="columns:1">
      <li><a href="/all-games/">All games A–Z</a></li><li><a href="/search/">Search games</a></li>
      <li><a href="/#featured">Featured games</a></li><li><a href="/blog/">Blog</a></li><li><a href="/sitemap/">Site map</a></li></ul></nav>
  </div>
  <div class="wrap footer-base">© {TODAY.year} ArcadeWebsite.com. Games and trademarks belong to their respective owners.</div>
</footer>
</body>
</html>
"""


def ad(slot, size, cls=""):
    w, h = size.split("x")
    classes = f"ad ad-{size} {cls}".strip()
    return (f'<aside class="{classes}" data-slot="{slot}" data-size="{size}" aria-label="Advertisement">'
            f'<span>Advertisement</span><small>{w} × {h}</small></aside>')


def ad_banner(slot, big="728x90", small="320x50", tight=False):
    """A wide banner on desktop that becomes a phone-sized banner on small screens."""
    mid = ad(slot + "-tablet", "468x60", "ad-mid") if small == "320x50" else ""   # rows between 468 and 727px wide
    narrow = "ad-narrow after-mid" if mid else "ad-narrow"
    return (f'<div class="ad-row{" tight" if tight else ""}">{ad(slot, big, "ad-wide")}{mid}'
            f'{ad(slot + "-mobile", small, narrow)}</div>')


def ad_tile(slot):
    """A full-width ad row inside a game grid: a leaderboard on desktop, a rectangle on phones."""
    return f'<div class="ad-tile">{ad(slot, "728x90", "ad-wide")}{ad(slot + "-mobile", "300x250", "ad-narrow")}</div>'


def webp(path):
    base, _, query = path.partition("?")
    return base.rsplit(".", 1)[0] + ".webp" + (f"?{query}" if query else "")


def picture(src, alt="", lazy=True, extra=""):
    """A thumbnail as WebP with the original PNG as fallback."""
    la = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return (f'<picture><source type="image/webp" srcset="{e(webp(src))}">'
            f'<img src="{e(src)}" alt="{e(alt)}" width="{THUMB_W}" height="{THUMB_H}"{la}{extra}></picture>')


def card(g, lazy=True):
    c = C[g["category"]]
    return (f'<a class="card c-{c["slug"]}" href="/game/{g["slug"]}/" data-name="{e(g["title"].lower())}">'
            f'<span class="thumb">{picture(g["thumbnail"], lazy=lazy)}</span>'
            f'<span class="name">{e(g["title"])}</span><span class="cat">{e(c["name"])}</span></a>')


SPONSORED_AT = (5, 27, 49)   # positions in a category page's grid where a labeled sponsored tile goes


def sponsored_tile(slot):
    """A clearly labeled ad the size of a game card, sitting in the game grid (native advertising)."""
    return (f'<div class="card sponsored" role="complementary" aria-label="Advertisement">'
            f'<span class="sp-label">Ad</span>'
            f'<aside class="ad ad-250x250 ad-sponsored" data-slot="{slot}" data-size="250x250">'
            f'<span>Advertisement</span></aside></div>')


def grid(slugs, ad_prefix=None, every=0, gid=None, dense=False, eager=0, sponsored=None):
    parts = []
    for i, s in enumerate(slugs):
        if ad_prefix and every and i and i % every == 0:
            parts.append(ad_tile(f"{ad_prefix}-{i // every}"))
        if sponsored and i in SPONSORED_AT:
            parts.append(sponsored_tile(f"{sponsored}-{SPONSORED_AT.index(i) + 1}"))
        parts.append(card(G[s], lazy=i >= eager))
    gid = f' id="{gid}"' if gid else ""
    return f'<div class="grid{" dense" if dense else ""}"{gid}>{"".join(parts)}</div>'


def shelf(sid, title, sub, slugs, more=None, cat=None):
    icon = f'<span class="icon">{ICONS[cat]}</span>' if cat else ""
    more_link = f'<a class="more" href="{more[0]}">{e(more[1])}</a>' if more else ""
    cls = f' class="section c-{cat}"' if cat else ' class="section"'
    sub_html = f"<p>{e(sub)}</p>" if sub else ""
    return f"""<section{cls} aria-labelledby="{sid}-h">
  <div class="section-head">
    <div class="shelf-title">{icon}<div><h2 id="{sid}-h">{e(title)}</h2>{sub_html}</div></div>
    <div class="arrows">{more_link}<button type="button" data-shelf="{sid}" data-dir="-1" aria-label="Scroll {e(title)} left">{I_LEFT}</button><button type="button" data-shelf="{sid}" data-dir="1" aria-label="Scroll {e(title)} right">{I_RIGHT}</button></div>
  </div>
  <div class="shelf" id="{sid}">{"".join(card(G[s]) for s in slugs if s in G)}</div>
</section>"""


def write(path, text):
    out = OUT / path.lstrip("/")
    if path.endswith("/"):
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def breadcrumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
                                for i, (n, u) in enumerate(items)]}


def feat(g):
    c = C[g["category"]]
    return {"title": g["title"], "url": f'/game/{g["slug"]}/', "thumbnail": g["thumbnail"],
            "category": c["slug"], "categoryName": c["name"], "description": COPY.game_summary(g)}

# ---------------------------------------------------------------------------------------------
# Featured rotation: favorites first, then the whole library in a fixed shuffled order.
# The browser picks today's slice (see app.js); the same logic runs here for the first paint.
# ---------------------------------------------------------------------------------------------
def rotation():
    fav = [s for s in featured_cfg["favorites"] if s in G]
    rng = random.Random(1562)
    fav_shuffled = fav[:]
    rng.shuffle(fav_shuffled)
    rest = [g["slug"] for g in games if g["slug"] not in fav] if featured_cfg.get("includeWholeLibrary", True) else []
    rng.shuffle(rest)
    return fav_shuffled + rest


def todays_picks(rot, day=TODAY):
    start = dt.date.fromisoformat(featured_cfg["startDate"])
    period = max(0, (day - start).days) // featured_cfg["daysPerRotation"]
    n = featured_cfg["gamesPerRotation"]
    pinned = [s for s in featured_cfg["pinned"] if s in G][:n]
    picks = pinned[:]
    k = 0
    while len(picks) < n and k < len(rot):
        s = rot[(period * (n - len(pinned)) + k) % len(rot)]
        if s not in picks:
            picks.append(s)
        k += 1
    return picks

# ---------------------------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------------------------
def home_blog():
    if not POSTS:
        return ""
    return (f'<section class="section" aria-labelledby="blog-h"><div class="section-head"><div><h2 id="blog-h">From the blog</h2>'
            f'<p>Guides and top lists for the games on {BRAND}.</p></div><a class="more" href="/blog/">All articles</a></div>'
            f'<div class="post-grid">{"".join(post_card(p) for p in POSTS[:3])}</div></section>')


def page_home(rot):
    picks = [feat(G[s]) for s in todays_picks(rot)]
    g0 = picks[0]
    tiles = "".join(
        f'<a class="cat-tile c-{c["slug"]}" href="/category/{c["slug"]}/"><span class="icon">{ICONS[c["slug"]]}</span>'
        f'<span><strong>{e(c["name"])}</strong><small>{len(c["games"]):,} games</small></span></a>' for c in cats)
    shelves = []
    for i, c in enumerate(cats):
        shelves.append(shelf(f"cat-{c['slug']}", f"{c['name']} games", None, c["games"][:18],
                             more=(f"/category/{c['slug']}/", f"See all {len(c['games']):,}"), cat=c["slug"]))
        if i % 3 == 2 and i < len(cats) - 1:
            shelves.append(ad_banner(f"home-between-{i // 3 + 1}", "728x90", "320x50"))
    desc = f"Play {TOTAL:,} free online games at ArcadeWebsite: arcade, racing, puzzle, platformer, sports and two-player games. No download or sign-up needed."
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE + "/",
           "potentialAction": {"@type": "SearchAction", "target": SITE + "/search/?q={search_term_string}",
                               "query-input": "required name=search_term_string"}}]
    icons_js = json.dumps(ICONS)
    initial_js = json.dumps(picks, ensure_ascii=False).replace("</", "<\\/")
    body = f"""<main id="main">
<div class="wrap">
  {ad_banner("home-top", "728x90", "320x50", tight=True)}
  <div class="home-intro">
    <h1>Free online games</h1>
    <p>Play {TOTAL:,} free games in your browser, from arcade classics and racing games to puzzles, platformers and two-player battles. No downloads, no sign-up.</p>
  </div>
  <section id="featured" class="stage-wrap" aria-roledescription="carousel" aria-label="Featured games">
    <div class="stage c-{g0['category']}" data-seconds="{featured_cfg['secondsPerSlide']}" aria-live="polite">
      <div class="stage-backdrop" style="background-image:url('{e(g0['thumbnail'])}')"></div>
      <div class="stage-art"><a class="stage-link" href="{e(g0['url'])}" tabindex="-1"><img src="{e(g0['thumbnail'])}" alt="{e(g0['title'])}" width="480" height="320" fetchpriority="high"></a></div>
      <div class="stage-copy">
        <span class="kicker">Featured game</span>
        <a class="chip c-{g0['category']}" data-f="chip" href="/category/{g0['category']}/"><span class="icon" data-f="chipicon">{ICONS[g0['category']]}</span><span data-f="chipname">{e(g0['categoryName'])}</span></a>
        <h2 data-f="title">{e(g0['title'])}</h2>
        <p class="desc" data-f="desc">{e(g0['description'])}</p>
        <a class="btn-play stage-link" href="{e(g0['url'])}">{I_PLAY}Play now</a>
      </div>
      <div class="stage-controls"><button type="button" class="stage-pause" aria-label="Pause featured games slideshow">{I_PAUSE}</button><div class="stage-dots"></div></div>
    </div>
    <div class="lineup">
      <div class="lineup-head"><h2>Featured now</h2><span>New picks every {featured_cfg['daysPerRotation']} days</span></div>
      <ol></ol>
    </div>
  </section>
  <script type="application/json" id="stage-initial">{initial_js}</script>
  <script>window.ARCADE_ICONS={icons_js};</script>

  <section class="section" id="categories" aria-labelledby="cats-h">
    <div class="section-head"><div><h2 id="cats-h">Pick a category</h2><p>{TOTAL:,} games across {len(cats)} categories.</p></div></div>
    <div class="tiles-row"><div class="cat-tiles">{tiles}</div>{ad("home-beside-categories", "300x250", "only-desktop")}</div>
  </section>

  {ad_banner("home-after-categories", "728x90", "320x50")}
  {shelf("spotlight", "Spotlight", "Our favorites to start with.", home_picks["spotlight"])}
  {shelf("trending", "Trending picks", "Games players keep coming back to.", home_picks["trending"])}
  {ad_banner("home-after-trending", "728x90", "300x250")}
  {shelf("new", "New to your rotation", "Classics worth another round.", home_picks["new"])}
  {"".join(shelves)}
  {home_blog()}
  {ad_banner("home-bottom", "728x90", "320x50")}
</div>
</main>
"""
    ld[0]["publisher"] = {"@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": SITE + "/favicon.svg"}
    ld.append({"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": SITE + "/favicon.svg"})
    ld.append({"@context": "https://schema.org", "@type": "ItemList", "name": "Game categories",
               "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + f'/category/{c["slug"]}/', "name": f'{c["name"]} games'}
                                   for i, c in enumerate(cats)]})
    write("/", head(f"Free Online Games - Play {TOTAL:,} Games Free | {BRAND}", desc, "/", g0["thumbnail"], ld,
                    preload=g0["thumbnail"]) + header("home") + body + footer())


def faq_html(items, hid):
    qa = "".join(f'<details><summary>{e(q)}</summary><p>{a}</p></details>' for q, a in items)
    return qa


def faq_ld(items):
    import re as _re
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": _re.sub(r"<[^>]+>", "", a)}} for q, a in items]}


def link_name(h, s):
    """Link the first mention of a game's name, as a whole word and never inside an existing link or tag
    (so a game called "1" doesn't turn the "1" in "EaglercraftX 1.8" into a link)."""
    name = e(G[s]["title"])
    pat = re.compile(r"(?<![\w.])" + re.escape(name) + r"(?![\w]|\.\d)")
    parts = re.split(r"(<a\b.*?</a>|<[^>]+>)", h)
    for i in range(0, len(parts), 2):            # even items are plain text
        if pat.search(parts[i]):
            parts[i] = pat.sub(game_link(s), parts[i], count=1)
            return "".join(parts)
    return h


def game_link(s):
    return f'<a href="/game/{s}/">{e(G[s]["title"])}</a>'


def featured_in(g):
    ps = POSTS_BY_GAME.get(g["slug"], [])[:3]
    if not ps:
        return ""
    links = "".join(f'<li><a href="/blog/{p["slug"]}/">{e(p["title"])}</a></li>' for p in ps)
    return f'<h2 id="blog-mentions-h">Featured in</h2><ul class="mentions">{links}</ul>'


def page_game(g):
    c = C[g["category"]]
    path = f'/game/{g["slug"]}/'
    title = COPY.game_title(g)
    meta = COPY.game_meta(g)
    related = [s for s in g["related"] if s in G and s != g["slug"]]
    series = COPY.siblings(g)
    # well-known games from the same category first, then the live site's related list
    # Each page gets its own mix of well-known games from its category (picked by its name),
    # mixed with the live site's related games for that page
    pool = [s for s in c["games"] if COPY.has_writeup(s) and s != g["slug"] and s not in series]
    popular = sorted(pool, key=lambda s: hashlib.md5((g["slug"] + s).encode()).hexdigest())[:6]
    mixed = [x for pair in zip(popular, related) for x in pair] + popular + related
    more = []
    for s in mixed + c["games"]:
        if s != g["slug"] and s not in more and s not in series:
            more.append(s)
    more = more[:24]
    paras = COPY.game_paragraphs(g, [G[s]["title"] for s in more[:3]])
    # link the game names in the "you might also like" sentence
    about = ""
    for p in paras:
        h = e(p)
        for s in sorted(more[:3], key=lambda s: -len(G[s]["title"])):
            h = link_name(h, s)
        h = h.replace(f"{e(c['name'])} collection", f'<a href="/category/{c["slug"]}/">{e(c["name"])} collection</a>', 1)
        about += f"<p>{h}</p>"
    howto = e(COPY.game_howto(g))
    faq = COPY.game_faq(g, [G[s]["title"] for s in more[:4]])
    faq_items = []
    for q, a in faq:
        ah = e(a)
        for s in sorted(more[:4], key=lambda s: -len(G[s]["title"])):
            ah = link_name(ah, s)
        ah = ah.replace(f"{e(c['name'])} collection", f'<a href="/category/{c["slug"]}/">{e(c["name"])} collection</a>', 1)
        faq_items.append((q, ah))
    canon = f'/game/{CANONICAL[g["slug"]]}/' if g["slug"] in CANONICAL else None
    ld = [{"@context": "https://schema.org", "@type": "VideoGame", "name": g["title"], "url": SITE + path,
           "description": COPY.game_summary(g), "genre": c["name"], "gamePlatform": "Web browser",
           "operatingSystem": "Any", "applicationCategory": "GameApplication", "inLanguage": "en",
           "screenshot": SITE + g["thumbnail"], "keywords": f'{g["title"]}, {g["title"]} online, play {g["title"]} free, {g["title"]} unblocked, {g["title"]} Chromebook, {c["name"].lower()} games',
           "isAccessibleForFree": True, "playMode": "SinglePlayer",
           "image": {"@type": "ImageObject", "url": SITE + g["thumbnail"], "width": THUMB_W, "height": THUMB_H},
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD", "availability": "https://schema.org/InStock"},
           "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE + "/"}},
          breadcrumbs_ld([("Home", "/"), (f'{c["name"]} games', f'/category/{c["slug"]}/'), (g["title"], path)]),
          faq_ld(faq_items)]
    share_url = (SITE + path).replace(":", "%3A").replace("/", "%2F")
    series_html = ""
    if series:
        series_html = f"""<section class="section" aria-labelledby="series-h">
    <div class="section-head"><div><h2 id="series-h">More games in this series</h2><p>Keep going with {len(series)} more {'game' if len(series) == 1 else 'games'} related to {e(g['title'])}.</p></div></div>
    {grid(series[:24])}
  </section>"""
    body = f"""<main id="main" class="c-{c['slug']}">
<div class="wrap">
  {ad_banner("game-top", "728x90", "320x50", tight=True)}
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/category/{c['slug']}/">{e(c['name'])} games</a><span aria-hidden="true">/</span><span aria-current="page">{e(g['title'])}</span></nav>
  <div class="game-top">
    <div><a class="chip c-{c['slug']}" href="/category/{c['slug']}/"><span class="icon">{ICONS[c['slug']]}</span>{e(c['name'])}</a><h1>{e(g['title'])}</h1>
    <p class="lede">{e(clip(COPY.game_summary(g), 170))}</p></div>
  </div>
  <div class="play-area">
    <div class="rail rail-left">{ad("game-left", "160x600")}</div>
    <section class="player" aria-label="Play {e(g['title'])}">
      <div class="player-frame">
        <iframe data-src="{e(g['src'])}" title="{e(g['title'])}" allow="fullscreen; gamepad; autoplay" referrerpolicy="strict-origin-when-cross-origin"></iframe>
        <button type="button" class="player-start" aria-label="Play {e(g['title'])}">
          <img src="{e(g['thumbnail'])}" alt="" width="{THUMB_W}" height="{THUMB_H}">
          <span class="start-card">{picture(g['thumbnail'], g['title'] + ' game', lazy=False)}<span class="btn-play">{I_PLAY}Play {e(g['title'])}</span></span>
        </button>
        <noscript><iframe src="{e(g['src'])}" title="{e(g['title'])}" allowfullscreen style="position:absolute;inset:0;width:100%;height:100%;border:0;z-index:3"></iframe></noscript>
      </div>
      <div class="player-bar">
        <p>Click the game to start. Press Esc to leave fullscreen.</p>
        <div class="player-tools">
          <button type="button" class="tool" data-reload>{I_RELOAD}Restart</button>
          <button type="button" class="tool" data-fullscreen>{I_FULL}Fullscreen</button>
        </div>
      </div>
    </section>
    <div class="rail rail-right">{ad("game-right-top", "300x600")}{ad("game-right", "300x250")}</div>
  </div>
  {ad_banner("game-below-player", "728x90", "300x250")}
  <div class="game-info">
    <article class="about" aria-labelledby="about-h">
      <h2 id="about-h">About {e(g['title'])}</h2>
      {about}
      <h2 id="howto-h">How to play {e(g['title'])}: controls and tips</h2>
      <p>{howto}</p>
      <dl class="facts">
        <div><dt>Category</dt><dd><a href="/category/{c['slug']}/">{e(c['name'])}</a></dd></div>
        <div><dt>Price</dt><dd>Free</dd></div>
        <div><dt>Plays on</dt><dd>Web browser</dd></div>
        <div><dt>Download</dt><dd>Not needed</dd></div>
      </dl>
      {featured_in(g)}
      <h2 id="faq-h">{e(g['title'])} FAQ</h2>
      <div class="faq">{faq_html(faq_items, "faq-h")}</div>
      <div class="share">
        <span>Share</span>
        <a class="tool" href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" rel="noopener noreferrer">Facebook</a>
        <a class="tool" href="https://twitter.com/intent/tweet?url={share_url}&amp;text={e(('Play ' + g['title']).replace(' ', '%20'))}" target="_blank" rel="noopener noreferrer">X</a>
        <button type="button" class="tool" data-copy>{I_LINK}Copy link</button>
        <span class="share-status" role="status"></span>
      </div>
    </article>
    <div class="rail">{ad("game-beside-about", "300x250")}</div>
  </div>
  {series_html}
  <section class="section" aria-labelledby="more-h">
    <div class="section-head"><div class="shelf-title"><span class="icon">{ICONS[c['slug']]}</span><div><h2 id="more-h">More {e(c['name'].lower())} games like {e(g['title'])}</h2></div></div>
      <a class="more" href="/category/{c['slug']}/">See all {len(c['games']):,}</a></div>
    {grid(more, "game-related", 8)}
  </section>
  {ad_banner("game-bottom", "728x90", "320x50")}
</div>
</main>
"""
    robots = "noindex,follow" if g.get("index") is False else None   # "index": false in games.json hides it from search
    write(path, head(title, meta, path, g["thumbnail"], ld, canonical=canon, image_alt=f'{g["title"]} game', robots=robots)
          + header(cat=c["slug"]) + body + footer())


PER_PAGE = 60          # games per numbered page on big categories
PAGINATE_OVER = 200    # categories with more games than this are split into numbered pages


def cat_page_path(c, n):
    return f'/category/{c["slug"]}/' if n == 1 else f'/category/{c["slug"]}/page/{n}/'


def pager(pages, current, path_for, label):
    """Previous / 1 2 3 … / Next links."""
    if pages <= 1:
        return ""
    # every page number is linked (up to 25 pages), so each game is at most two clicks from its category
    show = list(range(1, pages + 1)) if pages <= 25 else sorted({1, 2, pages - 1, pages, current - 1, current, current + 1} & set(range(1, pages + 1)))
    parts, last = [], 0
    for n in show:
        if n - last > 1:
            parts.append('<span class="gap" aria-hidden="true">…</span>')
        cur = ' aria-current="page"' if n == current else ""
        parts.append(f'<a href="{path_for(n)}"{cur} aria-label="{label} page {n}">{n}</a>')
        last = n
    prev = f'<a class="step" href="{path_for(current - 1)}" rel="prev">{I_LEFT}Previous</a>' if current > 1 else ""
    nxt = f'<a class="step" href="{path_for(current + 1)}" rel="next">Next{I_RIGHT}</a>' if current < pages else ""
    return f'<nav class="pager" aria-label="{label} pages">{prev}<span class="nums">{"".join(parts)}</span>{nxt}</nav>'


CAT_H1 = {   # headings matched to what people search for (see docs/seo.md)
    "racing": "Car games and racing games", "minecraft": "Eaglercraft and Minecraft games",
    "battle": "Fighting games and 2 player battle games", "shooting": "Shooting games and gun games",
    "strategy": "Strategy and tower defense games", "idle-clicker": "Clicker games and idle games",
    "horror": "Horror games and scary games", "platformer": "Platformer games",
}


def page_category(c):
    n = len(c["games"])
    pages = -(-n // PER_PAGE) if n > PAGINATE_OVER else 1
    per = PER_PAGE if pages > 1 else n
    faq = [(f["q"], e(f["a"])) for f in c["faq"]]
    top = [s for s in c["games"] if COPY.has_writeup(s)][:6]
    top_html = (f'<p>Popular {e(c["name"].lower())} games include ' + ", ".join(game_link(s) for s in top) + ".</p>") if top else ""
    intro = "".join(f"<p>{e(p)}</p>" for p in c["intro"])
    for p in range(1, pages + 1):
        path = cat_page_path(c, p)
        chunk = c["games"][(p - 1) * per: p * per]
        first, last_n = (p - 1) * per + 1, (p - 1) * per + len(chunk)
        if p == 1:
            title, meta = COPY.category_title(c), COPY.category_meta(c)
        else:
            title = f'{c["name"]} Games - Page {p} of {pages} | {BRAND}'
            names = ", ".join(G[s]["title"] for s in chunk[:3])
            meta = clip(f'Free {c["name"].lower()} games {first}–{last_n} of {n:,} on ArcadeWebsite, including {names}. Play online, no download.', 158)
        crumbs = [("Home", "/"), (f'{c["name"]} games', cat_page_path(c, 1))] + ([(f"Page {p}", path)] if p > 1 else [])
        ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f'{c["name"]} Games' + (f" - Page {p}" if p > 1 else ""),
               "description": meta, "url": SITE + path, "inLanguage": "en",
               "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE + "/"},
               "mainEntity": {"@type": "ItemList", "numberOfItems": len(chunk),
                              "itemListElement": [{"@type": "ListItem", "position": first + i, "url": SITE + f"/game/{s}/", "name": G[s]["title"]}
                                                  for i, s in enumerate(chunk)]}},
              breadcrumbs_ld(crumbs)]
        if p == 1:
            ld.append(faq_ld(faq))
        crumb_html = ('<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span>'
                      + (f'<span aria-current="page">{e(c["name"])} games</span>' if p == 1 else
                         f'<a href="{cat_page_path(c, 1)}">{e(c["name"])} games</a><span aria-hidden="true">/</span><span aria-current="page">Page {p}</span>')
                      + "</nav>")
        h1 = e(CAT_H1.get(c["slug"], f'{c["name"]} games')) + (f' <span class="page-no">page {p} of {pages}</span>' if p > 1 else "")
        showing = f"Showing {first}–{last_n} of {n:,} games" if pages > 1 else f"{n:,} games"
        filter_attr = f'data-filter-remote="{c["slug"]}"' if pages > 1 else 'data-filter="cat-grid"'
        about = f"""<section class="section cat-about" aria-labelledby="cat-about-h">
    <article class="about">
      <h2 id="cat-about-h">About our {e(c['name'].lower())} games</h2>
      {intro}{top_html}
      <p>Every game on this page is free and plays in your browser. Can't find what you want? Try the <a href="/all-games/">full A–Z list</a> or <a href="/#categories">another category</a>.</p>
      <h2 id="cat-faq-h">{e(c['name'])} games FAQ</h2>
      <div class="faq">{faq_html(faq, "cat-faq-h")}</div>
    </article>
  </section>""" if p == 1 else f"""<p class="lede">More free {e(c['name'].lower())} games. Start from <a href="{cat_page_path(c, 1)}">page 1</a> for the most popular ones, or use the filter to search all {n:,}.</p>"""
        body = f"""<main id="main" class="c-{c['slug']}">
<div class="wrap">
  {ad_banner("category-top", "728x90", "320x50", tight=True)}
  {crumb_html}
  <header class="cat-hero c-{c['slug']}">
    <span class="big-icon">{ICONS[c['slug']]}</span>
    <h1>{h1}</h1>
    <p>{e(c['intro'][0])}</p>
    <span class="count">{n:,} free games</span>
  </header>
  {ad_banner("category-below-header", "728x90", "320x50")}
  <div class="with-rail">
    <div>
      <div class="filter"><label class="sr-only" for="f">Filter {e(c['name'])} games</label>
        <input id="f" type="search" placeholder="Filter all {n:,} {e(c['name'].lower())} games" {filter_attr} autocomplete="off"><output data-default="{showing}">{showing}</output></div>
      <div id="cat-results">
        {grid(chunk, "category-in-grid", 20, gid="cat-grid", eager=12, sponsored="category-sponsored")}
        {pager(pages, p, lambda k: cat_page_path(c, k), c["name"] + " games")}
      </div>
    </div>
    <aside class="side-rail" aria-label="Advertisements">{ad("category-side-top", "300x600")}{ad("category-side", "300x250")}</aside>
  </div>
  {about}
  {ad_banner("category-bottom", "728x90", "320x50")}
</div>
</main>
"""
        write(path, head(title, meta, path, G[chunk[0]]["thumbnail"], ld, image_alt=f'{c["name"]} games')
              + header(cat=c["slug"]) + body + footer())
    c["pages"] = pages


def letter_of(title):
    k = title[:1].upper()
    return k if "A" <= k <= "Z" else "#"


def all_page_path(k):
    """'#' and 'A' share the first page at /all-games/; every other letter has its own page."""
    return "/all-games/" if k in ("#", "A") else f"/all-games/{k.lower()}/"


def small_letter_extra(idx, count):
    """Letters with only a few games also get popular picks and the categories, so the page isn't thin."""
    if not idx or count >= 24:
        return ""
    cl = ", ".join(f'<a href="/category/{c["slug"]}/">{e(c["name"].lower())} games</a>' for c in cats)
    return (f'<section class="section" aria-labelledby="pop-h"><div class="section-head"><div><h2 id="pop-h">Popular games to try next</h2>'
            f'<p>Only a few games start with this letter, so here are some of the most played games on {BRAND}. '
            f'You can also browse by category: {cl}.</p></div></div>{grid(home_picks["spotlight"][:12], dense=True)}</section>')


def page_all():
    ordered = sorted(games, key=lambda g: g["title"].lower())
    groups = {}
    for g in ordered:
        groups.setdefault(letter_of(g["title"]), []).append(g["slug"])
    keys = sorted(groups, key=lambda k: (k != "#", k))
    pages = []                                       # [(path, [letters])]
    for k in keys:
        p = all_page_path(k)
        if pages and pages[-1][0] == p:
            pages[-1][1].append(k)
        else:
            pages.append((p, [k]))
    for idx, (path, ks) in enumerate(pages):
        count = sum(len(groups[k]) for k in ks)
        label = " and ".join("numbers" if k == "#" else k for k in ks)
        nav = "".join(f'<a href="{all_page_path(k)}#l-{"0" if k == "#" else k}"{" aria-current=page" if k in ks else ""}>{k}</a>' for k in keys)
        sections = []
        for i, k in enumerate(ks):
            if i:
                sections.append(ad_banner(f"all-between-{i}", "728x90", "300x250"))
            sections.append(f'<h2 class="letter-head" id="l-{"0" if k == "#" else k}">{"Games starting with a number or symbol" if k == "#" else "Games starting with " + k}</h2>'
                            + grid(groups[k], "all-in-grid", 60, dense=True, eager=12 if i == 0 else 0))
        prev_p = pages[idx - 1][0] if idx else None
        next_p = pages[idx + 1][0] if idx + 1 < len(pages) else None
        step = (f'<nav class="pager" aria-label="A to Z pages">'
                + (f'<a class="step" href="{prev_p}" rel="prev">{I_LEFT}{" / ".join(pages[idx - 1][1])}</a>' if prev_p else "")
                + '<span class="nums"></span>'
                + (f'<a class="step" href="{next_p}" rel="next">{" / ".join(pages[idx + 1][1])}{I_RIGHT}</a>' if next_p else "") + "</nav>")
        if idx == 0:
            title = f"All {TOTAL:,} Free Online Games A to Z | {BRAND}"
            desc = f"Browse the complete ArcadeWebsite catalog: {TOTAL:,} free browser games across {len(cats)} categories, A to Z. Open any game on its own page."
            h1 = f"All {TOTAL:,} games, A to Z"
        else:
            title = f"Free Online Games Starting with {label} ({count}) | {BRAND}"
            names = ", ".join(G[s]["title"] for s in groups[ks[0]][:3])
            desc = clip(f"{count} free online games starting with {label} on ArcadeWebsite, including {names}. Play in your browser, no download.", 158)
            h1 = f"Games starting with {label}"
        crumbs = [("Home", "/"), ("All games", "/all-games/")] + ([(f"Letter {label}", path)] if idx else [])
        crumb_html = ('<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span>'
                      + ('<span aria-current="page">All games</span>' if idx == 0 else
                         f'<a href="/all-games/">All games</a><span aria-hidden="true">/</span><span aria-current="page">{label}</span>') + "</nav>")
        body = f"""<main id="main">
<div class="wrap">
  {ad_banner("all-top", "728x90", "320x50", tight=True)}
  {crumb_html}
  <h1>{h1}</h1>
  <p class="lede">{"Every game on ArcadeWebsite in alphabetical order, one letter per page. Pick a letter or filter by name." if idx == 0 else f"{count} free games whose names start with {label}. Pick another letter below, or filter all {TOTAL:,} games by name."}</p>
  <div class="filter"><label class="sr-only" for="f">Filter all games</label>
    <input id="f" type="search" placeholder="Filter all {TOTAL:,} games by name" data-filter-remote="all" autocomplete="off"><output data-default="{count} games on this page">{count} games on this page</output></div>
  <nav class="letters" aria-label="Jump to letter">{nav}</nav>
  <div class="with-rail">
    <div id="cat-results">{"".join(sections)}{step}{small_letter_extra(idx, count)}</div>
    <aside class="side-rail" aria-label="Advertisements">{ad("all-side-top", "300x600")}{ad("all-side", "300x250")}</aside>
  </div>
</div>
</main>
"""
        write(path, head(title, desc, path, G[groups[ks[0]][0]]["thumbnail"], ld=[breadcrumbs_ld(crumbs)]) + header("all") + body + footer())
    global ALL_PAGES
    ALL_PAGES = [p for p, _ in pages]


ALL_PAGES = ["/all-games/"]


def page_search():
    path = "/search/"
    body = f"""<main id="main">
<div class="wrap">
  {ad_banner("search-top", "728x90", "320x50", tight=True)}
  <div class="with-rail">
    <div>
      <h1 id="search-heading" style="margin-top:22px">Search games</h1>
      <p id="search-count" class="filter" role="status" style="color:var(--muted)">Loading search…</p>
      <div class="grid" id="search-results"></div>
    </div>
    <aside class="side-rail" aria-label="Advertisements">{ad("search-side-top", "300x600")}{ad("search-side", "300x250")}</aside>
  </div>
  {ad_banner("search-bottom", "728x90", "320x50")}
</div>
</main>
"""
    write(path, head(f"Find a Free Game | {BRAND}", "Search the ArcadeWebsite catalog by title or category. Open matching games on their dedicated player pages.",
                     path, robots="noindex,follow") + header() + body + footer())


def page_404():
    picks = home_picks["spotlight"][:12]
    body = f"""<main id="main">
<div class="wrap">
  <section class="cat-hero c-arcade" style="margin-top:28px">
    <span class="big-icon">{ICONS['arcade']}</span>
    <h1>This page isn't here</h1>
    <p>The link may be old or mistyped. Search for the game you wanted, or pick one of these.</p>
  </section>
  <section class="section"><div class="section-head"><div><h2>Popular games</h2></div><a class="more" href="/all-games/">Browse all games</a></div>{grid(picks)}</section>
  {ad_banner("notfound-bottom", "728x90", "300x250")}
</div>
</main>
"""
    write("/404.html", head(f"Page not found | {BRAND}", "This page could not be found.", "/404.html", robots="noindex") + header() + body + footer())



def page_redirects():
    """Removed games: their old address sends people (and search engines) to the working version."""
    p = ROOT / "data" / "removed-games.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    # Games removed completely: a permanent (301) redirect to the category they were in, so a visitor arriving from
    # an old link, bookmark or search result lands on similar games instead of a dead page. Cloudflare reads _redirects.
    lines = ["# Removed games -> their category (built from data/removed-games.json)"]
    for slug, cat in sorted(d.get("removed_category", {}).items()):
        if slug in G or slug in d["redirects"] or cat not in C:
            continue
        lines += [f"/game/{slug}/ /category/{cat}/ 301", f"/game/{slug} /category/{cat}/ 301"]
    (OUT / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for old, new in d["redirects"].items():
        if new.startswith("/category/"):                      # no working copy: send to the game's category
            c = C.get(new.strip("/").split("/")[-1])
            if not c:
                continue
            to, name = new, f'{c["name"]} games'
            h = head(COPY.category_title(c), COPY.category_meta(c), f"/game/{old}/", G[c["games"][0]]["thumbnail"],
                     robots="noindex,follow", canonical=to)
        elif new in G:
            g, to, name = G[new], f"/game/{new}/", G[new]["title"]
            h = head(f'{g["title"]} - Play Online for Free | {BRAND}', COPY.game_meta(g), f"/game/{old}/", g["thumbnail"],
                     robots="noindex,follow", canonical=to)
        else:
            continue
        h = h.replace("<meta charset=\"utf-8\">", f'<meta charset="utf-8">\n<meta http-equiv="refresh" content="0; url={to}">', 1)
        body = f"""<main id="main"><div class="wrap">
  <h1 style="margin-top:28px">This game has moved</h1>
  <p class="lede">Find it here: <a href="{to}">{e(name)}</a>.</p>
</div></main>
<script>location.replace({json.dumps(to)});</script>
"""
        write(f"/game/{old}/", h + header() + body + footer())

def blog_sitemap_block():
    if not POSTS:
        return ""
    items = "".join(f'<li><a href="/blog/{p["slug"]}/">{e(p["title"])}</a></li>' for p in POSTS)
    return f'<section class="section"><h2><a href="/blog/">Blog</a> <small>({len(POSTS)})</small></h2><ul class="sitemap-list">{items}</ul></section>'


def page_html_sitemap():
    path = "/sitemap/"
    blocks = []
    for c in cats:
        items = "".join(f'<li><a href="/game/{s}/">{e(G[s]["title"])}</a></li>' for s in sorted(c["games"], key=lambda s: G[s]["title"].lower()))
        blocks.append(f'<section class="section"><h2><a href="/category/{c["slug"]}/">{e(c["name"])} games</a> <small>({len(c["games"]):,})</small></h2><ul class="sitemap-list">{items}</ul></section>')
    body = f"""<main id="main">
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><span aria-current="page">Site map</span></nav>
  <h1>Site map</h1>
  <p class="lede">Every page on ArcadeWebsite: the <a href="/">homepage</a>, the <a href="/all-games/">A–Z list of all {TOTAL:,} games</a>, and each category with all of its games.</p>
  {"".join(blocks)}
  {blog_sitemap_block()}
</div>
</main>
"""
    write(path, head(f"Site Map - All Pages and Games | {BRAND}", f"A list of every page on ArcadeWebsite: all {len(cats)} categories and all {TOTAL:,} free games.", path,
                     ld=[breadcrumbs_ld([("Home", "/"), ("Site map", path)])]) + header() + body + footer())


# ---------------------------------------------------------------------------------------------
# Blog: one Markdown file per article in blog/posts/ (see blog/WRITING-GUIDE.md)
# ---------------------------------------------------------------------------------------------
BLOG_DIR = ROOT / "blog" / "posts"
AUTHOR = {"@type": "Organization", "name": f"{BRAND} Team", "url": SITE + "/blog/"}
PUBLISHER = {"@type": "Organization", "name": BRAND, "url": SITE + "/",
             "logo": {"@type": "ImageObject", "url": SITE + "/favicon.svg"}}


def read_post(f):
    """A post is `key: value` front matter between --- lines, then Markdown."""
    raw = f.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        raise SystemExit(f"{f}: missing --- front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for k in ("title", "seo_title", "description", "keyword", "date"):
        if not meta.get(k):
            raise SystemExit(f"{f}: front matter needs '{k}'")
    meta["slug"] = meta.get("slug") or f.stem
    meta["games"] = [s.strip() for s in meta.get("games", "").split(",") if s.strip()]
    missing = [s for s in meta["games"] if s not in G]
    if missing:
        raise SystemExit(f"{f}: games not on the site: {missing}")
    meta["updated"] = meta.get("updated") or meta["date"]
    meta["md"] = m.group(2).strip()
    return meta


def load_posts():
    if not BLOG_DIR.exists():
        return []
    posts = [read_post(f) for f in sorted(BLOG_DIR.glob("*.md"))]
    posts = [p for p in posts if p["date"] <= TODAY.isoformat() and p.get("draft", "").lower() != "true"]
    return sorted(posts, key=lambda p: p["date"], reverse=True)


POSTS = []          # filled in main()
POSTS_BY_GAME = {}  # game slug -> posts that feature it, for links from game pages


def post_image(p):
    """A 1200x630 share image, different for every article: the article's main game large on the left, the next
    two games stacked on the right, and the article title across the bottom."""
    from PIL import Image, ImageDraw, ImageFont
    path = f"/blog/img/{p['slug']}.jpg"
    out = OUT / path.lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    picks = (p["games"] or ["slope"])[:3]
    picks += picks * 3
    canvas = Image.new("RGB", (1200, 630), (18, 20, 46))

    def tile(slug, w, h):
        try:
            im = Image.open(unquote(str(OUT / G[slug]["thumbnail"].lstrip("/")))).convert("RGB")
        except Exception:
            return Image.new("RGB", (w, h), (36, 40, 90))
        r = max(w / im.width, h / im.height)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        l, t = (im.width - w) // 2, (im.height - h) // 2
        return im.crop((l, t, l + w, t + h))

    canvas.paste(tile(picks[0], 780, 630), (0, 0))
    canvas.paste(tile(picks[1], 414, 312), (786, 0))
    canvas.paste(tile(picks[2], 414, 312), (786, 318))
    # dark fade at the bottom so the title is readable on any picture
    fade = Image.new("L", (1, 630))
    for y in range(630):
        fade.putpixel((0, y), 0 if y < 300 else min(235, int((y - 300) / 330 * 300)))
    canvas.paste(Image.new("RGB", (1200, 630), (12, 13, 32)), (0, 0), fade.resize((1200, 630)))
    d = ImageDraw.Draw(canvas)
    font_path = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
    title = p.get("image_title") or p["title"]
    lines, size = [title], 60
    for size in range(60, 30, -2):
        try:
            font = ImageFont.truetype(font_path, size)
        except OSError:
            font = ImageFont.load_default()
            break
        words, lines, cur = title.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textlength(test, font=font) <= 1100:
                cur = test
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= 3:
            break
    lh = int(size * 1.18)
    y = 630 - 42 - lh * len(lines)
    for line in lines:
        d.text((50, y), line, font=font, fill=(255, 255, 255))
        y += lh
    try:
        small = ImageFont.truetype(font_path, 26)
    except OSError:
        small = ImageFont.load_default()
    d.text((50, 630 - 40 - lh * len(lines) - 40), "ARCADEWEBSITE.COM", font=small, fill=(255, 196, 61))
    canvas.save(out, quality=86, optimize=True, progressive=True)
    canvas.save(out.with_suffix(".webp"), quality=82)
    return path + "?v=" + hashlib.sha1(out.read_bytes()).hexdigest()[:8]   # new picture, new address: no stale caches


def render_post_body(p):
    """Markdown to HTML, with [[games: a, b]] lines turned into game cards and the FAQ split out."""
    import markdown
    md = p["md"]
    faq, faq_items = None, []
    m = re.search(r"^## (Frequently asked questions|FAQ)[^\n]*\n(.*?)(?=^## |\Z)", md, re.S | re.M | re.I)
    if m:
        faq = m.group(0)
        for q, a in re.findall(r"^### (.+?)\n(.*?)(?=^### |\Z)", m.group(2), re.S | re.M):
            a_html = markdown.markdown(a.strip())
            faq_items.append((q.strip(), re.sub(r"^<p>|</p>$", "", a_html.strip())))
        md = md.replace(faq, "")
    grids = []

    def grid_token(mm):
        slugs = [s.strip() for s in mm.group(1).split(",") if s.strip() in G]
        grids.append(grid(slugs, dense=True))
        return f"\n\nGAMEGRID{len(grids) - 1}\n\n"
    md = re.sub(r"^\[\[games:(.+?)\]\]\s*$", grid_token, md, flags=re.M)
    conv = markdown.Markdown(extensions=["tables", "toc", "attr_list", "sane_lists"],
                             extension_configs={"toc": {"toc_depth": "2"}})
    body = conv.convert(md)
    toc = [(t["id"], t["name"]) for t in conv.toc_tokens]
    for i, gh in enumerate(grids):
        body = body.replace(f"<p>GAMEGRID{i}</p>", gh)
    body = re.sub(r'<table>', '<div class="table-wrap"><table>', body).replace("</table>", "</table></div>")
    # outside links open in a new tab; links to our pages stay as they are
    body = re.sub(r'<a href="(https?://(?!arcadewebsite\.com)[^"]+)"', r'<a href="\1" target="_blank" rel="noopener">', body)
    # ad after the introduction and in the middle of the article
    parts = re.split(r"(?=<h2)", body)
    if len(parts) > 2:
        mid = len(parts) // 2 + 1
        parts.insert(mid, ad_banner(f"blog-mid", "728x90", "300x250"))
        parts.insert(1, ad_banner(f"blog-after-intro", "728x90", "320x50"))
    body = "".join(parts)
    words = len(re.sub(r"<[^>]+>", " ", body + " ".join(q + " " + a for q, a in faq_items)).split())
    return body, toc, faq_items, words


def fmt_date(d):
    x = dt.date.fromisoformat(d)
    return f"{x:%B} {x.day}, {x.year}"


def post_card(p):
    img = p["image"]
    return (f'<a class="post-card" href="/blog/{p["slug"]}/">'
            f'<span class="thumb"><picture><source type="image/webp" srcset="{e(webp(img))}">'
            f'<img src="{e(img)}" alt="" width="1200" height="630" loading="lazy" decoding="async"></picture></span>'
            f'<span class="post-meta"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time></span>'
            f'<span class="name">{e(p["title"])}</span><span class="excerpt">{e(p["description"])}</span></a>')


def page_post(p):
    path = f"/blog/{p['slug']}/"
    body_html, toc, faq_items, words = render_post_body(p)
    minutes = max(1, round(words / 230))
    c = C[G[p["games"][0]]["category"]] if p["games"] else cats[0]
    toc_html = ('<details class="toc"><summary>In this article</summary><nav aria-label="In this article"><ul>'
                + "".join(f'<li><a href="#{i}">{e(n)}</a></li>' for i, n in toc) + "</ul></nav></details>") if len(toc) > 2 else ""
    # the contents list goes after the opening answer, so the answer is the first thing readers and search engines see
    k = body_html.find("<div class=\"ad-row")
    k = k if k >= 0 else body_html.find("<h2")
    if toc_html and k >= 0:
        body_html, toc_html = body_html[:k] + toc_html + body_html[k:], ""
    faq_block = (f'<h2 id="faq-h">Frequently asked questions</h2><div class="faq">{faq_html(faq_items, "faq-h")}</div>'
                 if faq_items else "")
    others = [q for q in POSTS if q["slug"] != p["slug"]][:3]
    more_posts = (f'<section class="section" aria-labelledby="more-posts-h"><div class="section-head"><div><h2 id="more-posts-h">More from the blog</h2></div>'
                  f'<a class="more" href="/blog/">All articles</a></div><div class="post-grid">{"".join(post_card(q) for q in others)}</div></section>') if others else ""
    games_block = (f'<section class="section" aria-labelledby="games-h"><div class="section-head"><div><h2 id="games-h">Play the games from this article</h2>'
                   f'<p>Every game here plays free in your browser.</p></div></div>{grid(p["games"])}</section>') if p["games"] else ""
    updated = (f' · Updated <time datetime="{p["updated"]}">{fmt_date(p["updated"])}</time>'
               if p["updated"] != p["date"] else "")
    body = f"""<main id="main" class="c-{c['slug']}">
<div class="wrap">
  {ad_banner("blog-top", "728x90", "320x50", tight=True)}
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/blog/">Blog</a><span aria-hidden="true">/</span><span aria-current="page">{e(p['title'])}</span></nav>
  <div class="with-rail">
    <article class="about post" aria-labelledby="post-h">
      <header class="post-head">
        <h1 id="post-h">{e(p['title'])}</h1>
        <p class="byline">By <a href="/blog/">{BRAND} Team</a> · <time datetime="{p['date']}">{fmt_date(p['date'])}</time>{updated} · {minutes} min read</p>
        <picture><source type="image/webp" srcset="{e(webp(p['image']))}"><img class="post-hero" src="{e(p['image'])}" alt="{e(p.get('image_alt') or p['title'])}" width="1200" height="630" fetchpriority="high"></picture>
      </header>
      {toc_html}
      <div class="post-body">{body_html}</div>
      {faq_block}
    </article>
    <aside class="side-rail" aria-label="Advertisements">{ad("blog-side-top", "300x600")}{ad("blog-side", "300x250")}</aside>
  </div>
  {games_block}
  {ad_banner("blog-before-more", "728x90", "300x250")}
  {more_posts}
  {ad_banner("blog-bottom", "728x90", "320x50")}
</div>
</main>
"""
    ld = [{"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"][:110],
           "description": p["description"], "image": [SITE + p["image"]],
           "datePublished": p["date"], "dateModified": p["updated"], "author": AUTHOR, "publisher": PUBLISHER,
           "mainEntityOfPage": {"@type": "WebPage", "@id": SITE + path}, "url": SITE + path,
           "keywords": ", ".join([p["keyword"]] + [k.strip() for k in p.get("keywords", "").split(",") if k.strip()]),
           "wordCount": words, "inLanguage": "en-US",
           "about": [{"@type": "VideoGame", "name": G[s]["title"], "url": f"{SITE}/game/{s}/"} for s in p["games"][:12]]},
          breadcrumbs_ld([("Home", "/"), ("Blog", "/blog/"), (p["title"], path)])]
    if faq_items:
        ld.append(faq_ld(faq_items))
    h = head(p["seo_title"], p["description"], path, p["image"], ld, image_alt=p.get("image_alt") or p["title"])
    h = h.replace('<meta property="og:type" content="website">',
                  f'<meta property="og:type" content="article">\n<meta property="article:published_time" content="{p["date"]}">'
                  f'\n<meta property="article:modified_time" content="{p["updated"]}">', 1)
    h = (h.replace(f'og:image:width" content="{THUMB_W}"', 'og:image:width" content="1200"', 1)
          .replace(f'og:image:height" content="{THUMB_H}"', 'og:image:height" content="630"', 1))
    write(path, h + header("blog") + body + footer())


def page_blog():
    path = "/blog/"
    if not POSTS:
        return
    cards = "".join(post_card(p) for p in POSTS)
    body = f"""<main id="main">
<div class="wrap">
  {ad_banner("blog-index-top", "728x90", "320x50", tight=True)}
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><span aria-current="page">Blog</span></nav>
  <div class="with-rail">
    <div>
      <h1>ArcadeWebsite blog: game guides, lists and tips</h1>
      <p class="lede">Picks of the best free browser games, how-to-play guides and tips for getting more out of the {TOTAL:,} games on {BRAND}. New articles every few days.</p>
      <div class="post-grid">{cards}</div>
    </div>
    <aside class="side-rail" aria-label="Advertisements">{ad("blog-index-side-top", "300x600")}{ad("blog-index-side", "300x250")}</aside>
  </div>
  {ad_banner("blog-index-bottom", "728x90", "320x50")}
</div>
</main>
"""
    ld = [{"@context": "https://schema.org", "@type": "Blog", "name": f"{BRAND} Blog", "url": SITE + path,
           "publisher": PUBLISHER, "blogPost": [{"@type": "BlogPosting", "headline": p["title"][:110], "url": f"{SITE}/blog/{p['slug']}/",
                                                  "datePublished": p["date"], "image": SITE + p["image"]} for p in POSTS[:30]]},
          breadcrumbs_ld([("Home", "/"), ("Blog", path)])]
    write(path, head(f"Gaming Blog - Free Game Guides & Lists | {BRAND}",
                     f"Guides, top lists and tips for free online games you can play in your browser, from the {BRAND} team. New articles every few days.",
                     path, POSTS[0]["image"], ld) + header("blog") + body + footer())
    # RSS feed for the blog
    items = "".join(f"<item><title>{e(p['title'])}</title><link>{SITE}/blog/{p['slug']}/</link><guid>{SITE}/blog/{p['slug']}/</guid>"
                    f"<pubDate>{dt.datetime.fromisoformat(p['date']).strftime('%a, %d %b %Y 12:00:00 +0000')}</pubDate>"
                    f"<description>{e(p['description'])}</description></item>" for p in POSTS[:30])
    write("/blog/feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{BRAND} Blog</title>'
          f'<link>{SITE}/blog/</link><description>Guides and lists for free online games.</description>{items}</channel></rss>\n')


def build_blog():
    POSTS[:] = load_posts()
    for p in POSTS:
        p["image"] = post_image(p)
        for s in p["games"]:
            POSTS_BY_GAME.setdefault(s, []).append(p)


def indexable_urls():
    """Every page that should be in the sitemap (search and duplicate pages are left out)."""
    urls = ["/", "/sitemap/"] + ALL_PAGES
    if POSTS:
        urls += ["/blog/"] + [f"/blog/{p['slug']}/" for p in POSTS]
    urls += [cat_page_path(c, n) for c in cats for n in range(1, c.get("pages", 1) + 1)]
    urls += [f'/game/{g["slug"]}/' for g in games if g["slug"] not in CANONICAL and g.get("index") is not False]
    return urls


def lastmod_dates(urls):
    """A page's date changes only when its content changes, so search engines can trust it."""
    store_path = ROOT / "data" / "lastmod.json"
    store = json.loads(store_path.read_text()) if store_path.exists() else {}
    out = {}
    for u in urls:
        f = OUT / u.lstrip("/") / "index.html"
        text = f.read_text(encoding="utf-8")
        text = re.sub(r"\?v=[0-9a-f]+", "", text)                      # cache-busters
        text = re.sub(r'<script type="application/json" id="stage-initial">.*?</script>', "", text, flags=re.S)
        text = re.sub(r'<div class="stage .*?</section>', "", text, flags=re.S)   # today's featured games
        text = re.sub(r"© \d{4}", "", text)
        h = hashlib.sha1(text.encode()).hexdigest()[:16]
        old = store.get(u)
        out[u] = old if old and old[0] == h else [h, TODAY.isoformat()]
    store_path.write_text(json.dumps(out, indent=0, sort_keys=True))
    return {u: v[1] for u, v in out.items()}


def data_files(rot):
    write("/assets/search-index.json", json.dumps(
        [{"title": g["title"], "category": g["category"], "categoryName": C[g["category"]]["name"],
          "url": f'/game/{g["slug"]}/', "image": g["thumbnail"]} for g in games], ensure_ascii=False, separators=(",", ":")))
    write("/assets/featured.json", json.dumps({
        "startDate": featured_cfg["startDate"], "daysPerRotation": featured_cfg["daysPerRotation"],
        "gamesPerRotation": featured_cfg["gamesPerRotation"], "secondsPerSlide": featured_cfg["secondsPerSlide"],
        "categories": {c["slug"]: c["name"] for c in cats},
        # each game is [slug, title, thumbnail, category] to keep the file small
        "pinned": [[s, G[s]["title"], G[s]["thumbnail"], G[s]["category"]] for s in featured_cfg["pinned"] if s in G],
        "rotation": [[s, G[s]["title"], G[s]["thumbnail"], G[s]["category"]] for s in rot]}, ensure_ascii=False, separators=(",", ":")))

    # XML sitemap with each game's image, for Google and Bing
    urls = indexable_urls()
    dates = lastmod_dates(urls)
    slug_of = {f'/game/{g["slug"]}/': g for g in games}
    rows = []
    for u in urls:
        img = ""
        post = next((p for p in POSTS if u == f"/blog/{p['slug']}/"), None)
        if post:
            img = f'<image:image><image:loc>{e(SITE + post["image"])}</image:loc></image:image>'
        if u in slug_of:
            g = slug_of[u]
            img = f'<image:image><image:loc>{e(SITE + g["thumbnail"])}</image:loc></image:image>'
        rows.append(f"<url><loc>{e(SITE + u)}</loc><lastmod>{dates[u]}</lastmod>{img}</url>")
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
          + "\n".join(rows) + "\n</urlset>\n")

    # robots.txt: everything open to search engines and AI assistants, except search results and raw game files
    bots = ["Googlebot", "Bingbot", "DuckDuckBot", "Applebot", "GPTBot", "OAI-SearchBot", "ChatGPT-User",
            "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot"]
    rules = "Allow: /\nDisallow: /search/\nDisallow: /games/\n"
    write("/robots.txt", "# arcadewebsite.com\n# Search engines and AI assistants are welcome to read every game and category page.\n\n"
          + "User-agent: *\n" + rules + "\n" + "".join(f"User-agent: {b}\n" for b in bots) + rules
          + f"\nSitemap: {SITE}/sitemap.xml\n")

    # llms.txt: a plain summary of the site for AI assistants
    pop = [s for s in COPY.written if s in G and G[s].get("index") is not False][:60]
    lines = [f"# {BRAND}", "",
             f"> {BRAND} (arcadewebsite.com) is a free browser game website with {TOTAL:,} games in {len(cats)} categories. "
             "Every game has its own page with a description, how-to-play notes and an FAQ, and plays in the browser with no download or sign-up.", "",
             "## Categories", ""]
    lines += [f"- [{c['name']} games]({SITE}/category/{c['slug']}/): {clip(c['intro'][0], 160)} ({len(c['games']):,} games)" for c in cats]
    lines += ["", "## Popular games", ""]
    lines += [f"- [{G[s]['title']}]({SITE}/game/{s}/): {clip(COPY.game_summary(G[s]), 150)}" for s in pop]
    if POSTS:
        lines += ["", "## Blog articles", ""] + [f"- [{p['title']}]({SITE}/blog/{p['slug']}/): {p['description']}" for p in POSTS[:40]]
    lines += ["", "## All pages", "", f"- [All games A to Z]({SITE}/all-games/)", f"- [Site map]({SITE}/sitemap/)", f"- [XML sitemap]({SITE}/sitemap.xml)", ""]
    write("/llms.txt", "\n".join(lines))

    # RSS feed of the current featured games
    picks = todays_picks(rot)
    items = "".join(f"<item><title>{e(G[s]['title'])}</title><link>{SITE}/game/{s}/</link><guid>{SITE}/game/{s}/</guid>"
                    f"<description>{e(COPY.game_summary(G[s]))}</description></item>" for s in picks + [s for s in pop if s not in picks][:24])
    write("/feed.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{BRAND}: featured games</title>'
          f'<link>{SITE}/</link><description>Featured free online games on {BRAND}.</description>{items}</channel></rss>\n')


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "public", OUT)
    shutil.copytree(ROOT / "src/assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / "favicon.svg").write_text(LOGO.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    build_blog()
    rot = rotation()
    page_home(rot)
    for g in games:
        page_game(g)
    for c in cats:
        page_category(c)
    page_all()
    page_search()
    page_404()
    page_html_sitemap()
    page_redirects()
    for p in POSTS:
        page_post(p)
    page_blog()
    data_files(rot)
    n = sum(1 for _ in OUT.rglob("index.html"))
    print(f"Built {n} pages into {OUT}/ ({TOTAL} games, {len(cats)} categories).")
    print("Today's featured games:", ", ".join(G[s]["title"] for s in todays_picks(rot)))


if __name__ == "__main__":
    main()
