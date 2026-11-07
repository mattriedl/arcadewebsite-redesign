#!/usr/bin/env python3
"""Tell Bing (and other IndexNow search engines) about every page in the sitemap.

Run this once after the new site is live on arcadewebsite.com, and again after big changes:
    python3 tools/indexnow.py                     every page in the sitemap
    python3 tools/indexnow.py URL [URL ...]       just these pages (e.g. a new blog post)
"""
import sys
import json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
key = (ROOT / "data" / "indexnow-key.txt").read_text().strip()
urls = re.findall(r"<loc>(https://arcadewebsite\.com/[^<]*)</loc>", (ROOT / "site" / "sitemap.xml").read_text())
urls = [u for u in urls if "/thumbnails/" not in u]
if len(sys.argv) > 1:
    urls = sys.argv[1:]
for i in range(0, len(urls), 10000):
    body = json.dumps({"host": "arcadewebsite.com", "key": key, "keyLocation": f"https://arcadewebsite.com/{key}.txt",
                       "urlList": urls[i:i + 10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "ArcadeWebsite-IndexNow/1.0"})
    with urllib.request.urlopen(req) as r:
        print(f"Sent {len(urls[i:i + 10000])} pages: HTTP {r.status} (200 or 202 means accepted)")
