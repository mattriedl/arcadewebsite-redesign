#!/usr/bin/env python3
"""Check whether each game's outside files (on jsDelivr, githack, S3 and similar) can still be downloaded.

    python3 tools/check_game_files.py

Writes docs/broken-games.md and data/game-file-check.json. A game is "broken" when a file it needs
is refused by the host: a banned account, a deleted repository or commit, a package too large to serve,
or a missing file.
"""
import json, re, subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urljoin

ROOT = Path(__file__).resolve().parent.parent
games = json.loads((ROOT / "data/games.json").read_text())
HOSTS = ("cdn.jsdelivr.net", "githack.com", "s3.amazonaws.com", "statically.io", "githubusercontent.com", "gitcdn")

def needed_files(g):
    """Script, stylesheet and data URLs the game file loads from outside hosts (up to 4)."""
    t = (ROOT / "public" / unquote(g["src"]).lstrip("/")).read_text(encoding="utf-8", errors="replace")
    base = re.search(r'<base\s+href=["\']([^"\']+)', t)
    urls = []
    for m in re.finditer(r'(?:src|href)=["\']([^"\'#]+)["\']', t):
        u = m.group(1)
        if base and not u.startswith(("http", "/", "data:", "javascript:")):
            u = urljoin(base.group(1), u)
        if u.startswith("http") and any(h in u for h in HOSTS) and not u.endswith((".ico", ".png", ".jpg", ".svg", ".gif")):
            urls.append(u)
    return list(dict.fromkeys(urls))[:4]

def probe(url):
    r = subprocess.run(["curl", "-sS", "-r", "0-400", "-o", "-", "-w", "\n%{http_code}", "--max-time", "25", url],
                       capture_output=True, text=True, errors="replace")
    out = r.stdout
    body, code = (out.rsplit("\n", 1) + [""])[:2] if "\n" in out else ("", out)
    b = body.lower()
    if "is blocked" in b: why = "host banned the account"
    elif "package size exceeded" in b: why = "files too large for the host"
    elif "failed to fetch" in b or "couldn't find the requested" in b or code.strip() == "404": why = "files deleted or moved"
    elif code.strip() in ("200", "206") or code.strip().startswith("3"): why = "ok"   # 3xx: browsers follow the redirect
    elif code.strip() == "000": why = "no response"
    else: why = f"refused (HTTP {code.strip()})"
    return url, why

need = {g["slug"]: needed_files(g) for g in games}
all_urls = sorted({u for v in need.values() for u in v})
with ThreadPoolExecutor(12) as ex:
    result = dict(ex.map(probe, all_urls))
report = {}
for g in games:
    fails = [result[u] for u in need[g["slug"]] if result[u] != "ok"]
    if not need[g["slug"]]: state = "self-contained"
    elif not fails: state = "ok"
    elif all(f == "no response" for f in fails): state = "unknown"
    else: state = sorted(set(f for f in fails if f != "no response"))[0]
    report[g["slug"]] = state
(ROOT / "data/game-file-check.json").write_text(json.dumps(report, indent=0, sort_keys=True))
by = defaultdict(list)
for g in games:
    by[report[g["slug"]]].append(g)
broken = {k: v for k, v in by.items() if k not in ("ok", "self-contained", "unknown")}
n_broken = sum(len(v) for v in broken.values())
md = ["# Games whose files can't be downloaded", "",
      f"Checked {len(all_urls):,} outside files used by the games. **{n_broken} games** need a file that the host now refuses to serve, "
      "so they don't load for anyone, on the live site or the redesign.", "",
      "| Result | Games |", "|---|---|"] + [f"| {k} | {len(v)} |" for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))]
md += ["", "To fix a game, find a working copy of its files, upload them to your own server (for example under `/games/files/<game>/`) and change the game file to load them from there. Games you can't fix can be removed, or hidden with `\"index\": false` in `data/games.json`.", ""]
for k, v in sorted(broken.items(), key=lambda kv: -len(kv[1])):
    md += [f"## {k[0].upper() + k[1:]} ({len(v)})", ""] + [f"- [{g['title']}](https://arcadewebsite.com/game/{g['slug']}/)" for g in sorted(v, key=lambda g: g["title"].lower())] + [""]
(ROOT / "docs/broken-games.md").write_text("\n".join(md))
print({k: len(v) for k, v in by.items()})
