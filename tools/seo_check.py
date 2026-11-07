#!/usr/bin/env python3
"""Check every built page the way a search engine would, without running any JavaScript.

    python3 tools/seo_check.py          (run after python3 build.py)

Prints a summary and exits with an error if anything that would hurt search listings is found.
"""
import json
import os
import re
import sys
import urllib.robotparser
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE = "https://arcadewebsite.com"
ROOT = Path(__file__).resolve().parent.parent / "site"


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""; self.meta = {}; self.canonical = None; self.h1 = []; self.links = []; self.imgs = []
        self.ld = []; self._in = None; self._buf = ""; self.text = []; self._skip = 0; self._intag = []

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1
            if tag == "script" and a.get("type") == "application/ld+json":
                self._in = "ld"; self._buf = ""
        if tag == "title": self._in = "title"
        if tag == "h1": self._in = "h1"; self._buf = ""
        if tag == "meta" and (a.get("name") or a.get("property")): self.meta[a.get("name") or a.get("property")] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical": self.canonical = a.get("href")
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if tag == "img": self.imgs.append(a)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self._skip -= 1
            if tag == "script" and self._in == "ld":
                self.ld.append(self._buf); self._in = None
        if tag == "title": self._in = None
        if tag == "h1" and self._in == "h1": self.h1.append(self._buf.strip()); self._in = None

    def handle_data(self, d):
        if self._in == "ld": self._buf += d
        elif self._in == "title": self.title += d
        elif self._in == "h1": self._buf += d
        if not self._skip: self.text.append(d)


def exists(u):
    p = unquote(urlsplit(u).path)
    f = ROOT / p.lstrip("/")
    return f.is_file() or (f / "index.html").is_file()


pages, problems = {}, []
for d, _, fs in os.walk(ROOT):
    rel = os.path.relpath(d, ROOT)
    if rel.split(os.sep)[0] in ("games", "assets", "thumbnails"):
        continue
    for f in fs:
        if f.endswith(".html"):
            path = "/" + (os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/"))
            url = path[:-10] if path.endswith("index.html") else path
            p = Page(); p.feed((ROOT / path.lstrip("/")).read_text(encoding="utf-8")); pages[url] = p

sitemap = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text())
page_locs = [u for u in sitemap if "/thumbnails/" not in u]
rp = urllib.robotparser.RobotFileParser(); rp.parse((ROOT / "robots.txt").read_text().splitlines())

shown = [p for p in pages.values() if "noindex" not in p.meta.get("robots", "")]   # pages search engines may list
titles = Counter(p.title for p in shown)
descs = Counter(p.meta.get("description", "") for p in shown)
stats = Counter(); words = []
for url, p in pages.items():
    robots = p.meta.get("robots", "")
    indexable = "noindex" not in robots
    if not p.title: problems.append(f"{url}: no title")
    if titles[p.title] > 1 and indexable: stats["duplicate title"] += 1
    d = p.meta.get("description", "")
    if not d: problems.append(f"{url}: no meta description")
    elif descs[d] > 1 and indexable: stats["duplicate description"] += 1
    if indexable and not (50 <= len(d) <= 160): stats["description length outside 50-160"] += 1
    if len(p.title) > 70: stats["title over 70 characters"] += 1
    if len(p.h1) != 1: problems.append(f"{url}: {len(p.h1)} H1 headings")
    if not p.canonical or not p.canonical.startswith(SITE): problems.append(f"{url}: missing/relative canonical")
    elif p.canonical != SITE + url and indexable: stats["points to another page as main (duplicate)"] += 1
    for blob in p.ld:
        try:
            j = json.loads(blob)
            if "@context" not in j or "@type" not in j: problems.append(f"{url}: structured data missing @context/@type")
        except Exception as ex:
            problems.append(f"{url}: structured data is not valid JSON ({ex})")
    for img in p.imgs:
        if "alt" not in img: problems.append(f"{url}: image without alt attribute")
    for l in p.links:
        if l.startswith("/") and not exists(l.replace("&amp;", "&")): problems.append(f"{url}: broken link {l}")
    if url.startswith("/game/"):
        words.append(len(" ".join(p.text).split()))
    if not p.meta.get("og:image"): problems.append(f"{url}: no social image")

for u in page_locs:
    path = u[len(SITE):]
    if path not in pages: problems.append(f"sitemap lists a missing page: {u}")
    elif "noindex" in pages[path].meta.get("robots", ""): problems.append(f"sitemap lists a noindex page: {u}")
    elif pages[path].canonical != u: problems.append(f"sitemap lists a non-canonical page: {u}")
    if not rp.can_fetch("Googlebot", u) or not rp.can_fetch("GPTBot", u) or not rp.can_fetch("Bingbot", u):
        problems.append(f"robots.txt blocks {u}")
indexable_pages = [u for u, p in pages.items() if "noindex" not in p.meta.get("robots", "") and p.canonical == SITE + u]
missing_from_sitemap = [u for u in indexable_pages if SITE + u not in sitemap and u != "/404.html"]
for u in missing_from_sitemap: problems.append(f"indexable page missing from sitemap: {u}")

print(f"Pages checked: {len(pages)}   in sitemap: {len(page_locs)}   images in sitemap: {(ROOT / 'sitemap.xml').read_text().count('<image:image>')}")
print(f"Game page words readable without JavaScript: min {min(words)}, median {sorted(words)[len(words)//2]}, max {max(words)}")
for k, v in stats.items():
    print(f"  {k}: {v}")
print(f"Problems: {len(problems)}")
for x in problems[:40]:
    print("  -", x)
sys.exit(1 if problems else 0)
