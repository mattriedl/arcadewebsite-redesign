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
import shutil
from pathlib import Path

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
def head(title, desc, path, image=None, ld=None, robots=None, preload=None):
    url = SITE + path
    image = image or "/thumbnails/" + "clslope.png"
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    extra = f'<meta name="robots" content="{robots}">' if robots else ""
    pre = f'<link rel="preload" as="image" href="{e(preload)}">' if preload else ""
    return f"""<!doctype html>
<html lang="en">
<head>
{GTM_HEAD}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{extra}<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(SITE + image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(SITE + image)}">
<meta name="theme-color" content="#12142e">
<link rel="icon" href="/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&family=Unbounded:wght@500;600;700&display=swap">
<link rel="stylesheet" href="/assets/style.css?v={ASSET_V}">
{pre}{lds}
<script defer src="/assets/app.js?v={ASSET_V}"></script>
<script defer src="/assets/ads.js?v={ASSET_V}"></script>
</head>
"""


def header(active=None, cat=None):
    nav = [("/", "Home", "home"), ("/all-games/", "All games", "all"), ("/#categories", "Categories", "cats")]
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
      <li><a href="/#featured">Featured games</a></li><li><a href="/sitemap.xml">Sitemap</a></li></ul></nav>
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
    return (f'<div class="ad-row{" tight" if tight else ""}">{ad(slot, big, "only-desktop")}'
            f'{ad(slot + "-mobile", small, "only-mobile")}</div>')


def ad_tile(slot):
    """A full-width ad row inside a game grid: a leaderboard on desktop, a rectangle on phones."""
    return f'<div class="ad-tile">{ad(slot, "728x90", "only-desktop")}{ad(slot + "-mobile", "300x250", "only-mobile")}</div>'


def card(g, lazy=True):
    c = C[g["category"]]
    load_attr = ' loading="lazy" decoding="async"' if lazy else ""
    return (f'<a class="card c-{c["slug"]}" href="/game/{g["slug"]}/" data-name="{e(g["title"].lower())}">'
            f'<span class="thumb"><img src="{e(g["thumbnail"])}" alt="" width="480" height="320"{load_attr}></span>'
            f'<span class="name">{e(g["title"])}</span><span class="cat">{e(c["name"])}</span></a>')


def grid(slugs, ad_prefix=None, every=0, gid=None, dense=False, eager=0):
    parts = []
    for i, s in enumerate(slugs):
        if ad_prefix and every and i and i % every == 0:
            parts.append(ad_tile(f"{ad_prefix}-{i // every}"))
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
            "category": c["slug"], "categoryName": c["name"], "description": g["description"]}

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
            shelves.append(ad_banner(f"home-between-{i // 3 + 1}", "970x250" if i // 3 % 2 == 0 else "728x90", "320x100"))
    desc = f"Discover {TOTAL:,} free arcade games. Explore puzzle, racing, action and platform games, each with its own player page. Find your next favorite at ArcadeWebsite."
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE + "/",
           "potentialAction": {"@type": "SearchAction", "target": SITE + "/search/?q={search_term_string}",
                               "query-input": "required name=search_term_string"}}]
    icons_js = json.dumps(ICONS)
    initial_js = json.dumps(picks, ensure_ascii=False).replace("</", "<\\/")
    body = f"""<main id="main">
<div class="wrap">
  {ad_banner("home-top", "970x90", "320x50", tight=True)}
  <h1 class="sr-only">Free online games</h1>
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

  {ad_banner("home-after-categories", "728x90", "320x100")}
  {shelf("spotlight", "Spotlight", "Our favorites to start with.", home_picks["spotlight"])}
  {shelf("trending", "Trending picks", "Games players keep coming back to.", home_picks["trending"])}
  {ad_banner("home-after-trending", "970x250", "300x250")}
  {shelf("new", "New to your rotation", "Classics worth another round.", home_picks["new"])}
  {"".join(shelves)}
  {ad_banner("home-bottom", "728x90", "320x50")}
</div>
</main>
"""
    write("/", head(f"Free Arcade Games — Find Your Next Obsession | {BRAND}", desc, "/", g0["thumbnail"], ld,
                    preload=g0["thumbnail"]) + header("home") + body + footer())


def page_game(g):
    c = C[g["category"]]
    path = f'/game/{g["slug"]}/'
    title = f'{g["title"]} — Play Free Online | {BRAND}'
    related = [s for s in g["related"] if s in G and s != g["slug"]]
    more_cat = [s for s in c["games"] if s != g["slug"] and s not in related][:max(0, 24 - len(related))]
    related = (related + more_cat)[:24]
    about = "".join(f"<p>{e(p)}</p>" for p in g["about"]) or f'<p>{e(g["description"])}</p>'
    ld = [{"@context": "https://schema.org", "@type": "VideoGame", "name": g["title"], "url": SITE + path,
           "image": SITE + g["thumbnail"], "description": g["description"], "genre": c["name"],
           "gamePlatform": "Web browser", "applicationCategory": "Game", "isAccessibleForFree": True,
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
          breadcrumbs_ld([("Home", "/"), (c["name"], f'/category/{c["slug"]}/'), (g["title"], path)])]
    share_url = (SITE + path).replace(":", "%3A").replace("/", "%2F")
    body = f"""<main id="main" class="c-{c['slug']}">
<div class="wrap">
  {ad_banner("game-top", "970x90", "320x50", tight=True)}
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/category/{c['slug']}/">{e(c['name'])}</a><span aria-hidden="true">/</span><span aria-current="page">{e(g['title'])}</span></nav>
  <div class="game-top">
    <div><a class="chip c-{c['slug']}" href="/category/{c['slug']}/"><span class="icon">{ICONS[c['slug']]}</span>{e(c['name'])}</a><h1>{e(g['title'])}</h1></div>
  </div>
  <div class="play-area">
    <div class="rail rail-left">{ad("game-left", "160x600")}</div>
    <section class="player" aria-label="Play {e(g['title'])}">
      <div class="player-frame">
        <iframe data-src="{e(g['src'])}" title="{e(g['title'])}" allow="fullscreen; gamepad; autoplay" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
        <button type="button" class="player-start" aria-label="Start {e(g['title'])}">
          <img src="{e(g['thumbnail'])}" alt="" width="480" height="320">
          <span class="start-card"><img src="{e(g['thumbnail'])}" alt="" width="480" height="320"><span class="btn-play">{I_PLAY}Play {e(g['title'])}</span></span>
        </button>
        <noscript><iframe src="{e(g['src'])}" title="{e(g['title'])}" allowfullscreen style="position:absolute;inset:0;width:100%;height:100%;border:0;z-index:3"></iframe></noscript>
      </div>
      <div class="player-bar">
        <p>Click the game to start. Controls depend on the game; press Esc to leave fullscreen.</p>
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
    <section class="about" aria-labelledby="about-h">
      <h2 id="about-h">About {e(g['title'])}</h2>
      {about}
      <dl class="facts">
        <div><dt>Category</dt><dd><a href="/category/{c['slug']}/">{e(c['name'])}</a></dd></div>
        <div><dt>Price</dt><dd>Free</dd></div>
        <div><dt>Plays on</dt><dd>Web browser</dd></div>
      </dl>
      <div class="share">
        <span>Share</span>
        <a class="tool" href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" rel="noopener noreferrer">Facebook</a>
        <a class="tool" href="https://twitter.com/intent/tweet?url={share_url}&amp;text={e(('Play ' + g['title']).replace(' ', '%20'))}" target="_blank" rel="noopener noreferrer">X</a>
        <button type="button" class="tool" data-copy>{I_LINK}Copy link</button>
        <span class="share-status" role="status"></span>
      </div>
    </section>
    <div class="rail">{ad("game-beside-about", "300x250")}</div>
  </div>
  <section class="section" aria-labelledby="more-h">
    <div class="section-head"><div class="shelf-title"><span class="icon">{ICONS[c['slug']]}</span><div><h2 id="more-h">More {e(c['name'])} games</h2></div></div>
      <a class="more" href="/category/{c['slug']}/">See all {len(c['games']):,}</a></div>
    {grid(related, "game-related", 8)}
  </section>
  {ad_banner("game-bottom", "728x90", "320x100")}
</div>
</main>
"""
    write(path, head(title, g["description"], path, g["thumbnail"], ld) + header(cat=c["slug"]) + body + footer())


def page_category(c):
    path = f'/category/{c["slug"]}/'
    title = f'{c["name"]} Games — Play Free Online | {BRAND}'
    n = len(c["games"])
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f'{c["name"]} Games',
           "description": c["description"], "url": SITE + path, "numberOfItems": n},
          breadcrumbs_ld([("Home", "/"), (c["name"], path)])]
    body = f"""<main id="main" class="c-{c['slug']}">
<div class="wrap">
  {ad_banner("category-top", "970x90", "320x50", tight=True)}
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><span aria-current="page">{e(c['name'])}</span></nav>
  <header class="cat-hero c-{c['slug']}">
    <span class="big-icon">{ICONS[c['slug']]}</span>
    <h1>{e(c['title'])}</h1>
    <p>{e(c['description'])}</p>
    <span class="count">{n:,} free games</span>
  </header>
  {ad_banner("category-below-header", "728x90", "320x100")}
  <div class="with-rail">
    <div>
      <div class="filter"><label class="sr-only" for="f">Filter {e(c['name'])} games</label>
        <input id="f" type="search" placeholder="Filter {n:,} {e(c['name'].lower())} games" data-filter="cat-grid" autocomplete="off"><output>{n:,} games</output></div>
      {grid(c["games"], "category-in-grid", 20, gid="cat-grid", eager=12)}
    </div>
    <aside class="side-rail" aria-label="Advertisements">{ad("category-side-top", "300x600")}{ad("category-side", "300x250")}</aside>
  </div>
  {ad_banner("category-bottom", "728x90", "320x100")}
</div>
</main>
"""
    write(path, head(title, c["description"], path, G[c["games"][0]]["thumbnail"], ld) + header(cat=c["slug"]) + body + footer())


def page_all():
    path = "/all-games/"
    ordered = sorted(games, key=lambda g: g["title"].lower())
    groups = {}
    for g in ordered:
        k = g["title"][:1].upper()
        k = k if k.isalpha() else "#"
        groups.setdefault(k, []).append(g["slug"])
    keys = sorted(groups, key=lambda k: (k != "#", k))
    letters = "".join(f'<a href="#l-{"0" if k == "#" else k}">{k}</a>' for k in keys)
    sections = []
    for i, k in enumerate(keys):
        sections.append(f'<h2 class="letter-head" id="l-{"0" if k == "#" else k}">{k}</h2>' + grid(groups[k], f"all-{k if k != '#' else '0'}", 16, dense=True))
        if i % 4 == 3:
            sections.append(ad_banner(f"all-between-{i // 4 + 1}", "728x90", "300x250"))
    desc = f"Browse the complete ArcadeWebsite catalog: {TOTAL:,} free browser games across {len(cats)} categories. Open any game on its own dedicated page."
    body = f"""<main id="main">
<div class="wrap">
  {ad_banner("all-top", "970x90", "320x50", tight=True)}
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><span aria-current="page">All games</span></nav>
  <h1>All {TOTAL:,} games, A to Z</h1>
  <div class="filter"><label class="sr-only" for="f">Filter all games</label>
    <input id="f" type="search" placeholder="Filter by name" data-filter="all-grid" autocomplete="off"><output>{TOTAL:,} games</output></div>
  <nav class="letters" aria-label="Jump to letter">{letters}</nav>
  <div class="with-rail">
    <div id="all-grid">{"".join(sections)}</div>
    <aside class="side-rail" aria-label="Advertisements">{ad("all-side-top", "300x600")}{ad("all-side", "300x250")}</aside>
  </div>
</div>
</main>
"""
    write(path, head(f"All {TOTAL:,} Free Games | {BRAND}", desc, path, ld=[breadcrumbs_ld([("Home", "/"), ("All games", path)])])
          + header("all") + body + footer())


def page_search():
    path = "/search/"
    body = f"""<main id="main">
<div class="wrap">
  {ad_banner("search-top", "970x90", "320x50", tight=True)}
  <div class="with-rail">
    <div>
      <h1 id="search-heading" style="margin-top:22px">Search games</h1>
      <p id="search-count" class="filter" role="status" style="color:var(--muted)">Loading search…</p>
      <div class="grid" id="search-results"></div>
    </div>
    <aside class="side-rail" aria-label="Advertisements">{ad("search-side-top", "300x600")}{ad("search-side", "300x250")}</aside>
  </div>
  {ad_banner("search-bottom", "728x90", "320x100")}
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
    urls = ["/", "/all-games/"] + [f'/category/{c["slug"]}/' for c in cats] + [f'/game/{g["slug"]}/' for g in games]
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{e(SITE + u)}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>\n" for u in urls) + "</urlset>\n")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "public", OUT)
    shutil.copytree(ROOT / "src/assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / "favicon.svg").write_text(LOGO.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    rot = rotation()
    page_home(rot)
    for g in games:
        page_game(g)
    for c in cats:
        page_category(c)
    page_all()
    page_search()
    page_404()
    data_files(rot)
    n = sum(1 for _ in OUT.rglob("index.html"))
    print(f"Built {n} pages into {OUT}/ ({TOTAL} games, {len(cats)} categories).")
    print("Today's featured games:", ", ".join(G[s]["title"] for s in todays_picks(rot)))


if __name__ == "__main__":
    main()
