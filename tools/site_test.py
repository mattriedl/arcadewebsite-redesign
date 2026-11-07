#!/usr/bin/env python3
"""Load pages in real browsers at common screen sizes and report layout and script problems.

    python3 -m http.server -d site 8765 &
    python3 tools/site_test.py            # every page in Chrome at desktop size, plus key pages everywhere
    python3 tools/site_test.py --quick    # key pages only

Checks on each page: JavaScript errors, sideways scrolling, images that fail to load, and ad spots
that are the wrong size, stick out of the screen, overlap other content, or sit off-centre in
their row. Results go to the terminal and to site-test-report.json.
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://localhost:8765"
SIZES = {  # name: (width, height, is_phone)
    "phone-small": (360, 740, True), "iphone": (390, 844, True), "tablet": (768, 1024, True),
    "tablet-wide": (1024, 768, False), "laptop": (1366, 768, False), "desktop": (1440, 900, False),
    "full-hd": (1920, 1080, False), "2k": (2560, 1440, False),
}
KEY_PAGES = ["/", "/game/slope/", "/game/cookie-clicker/", "/game/fireboy-and-water-girl/", "/category/racing/",
             "/category/arcade/", "/category/arcade/page/8/", "/all-games/", "/all-games/s/", "/search/?q=mario",
             "/sitemap/", "/404.html", "/game/cookie-clicker-357/"]

CHECK = r"""() => {
  const out = {overflow: 0, brokenImages: [], ads: [], adProblems: []};
  const W = innerWidth;
  out.overflow = Math.max(0, document.documentElement.scrollWidth - W);
  for (const img of document.images) {
    if (img.loading !== "lazy" && img.complete && img.naturalWidth === 0 && img.getClientRects().length) out.brokenImages.push(img.currentSrc || img.src);
  }
  const vis = el => el.getClientRects().length && getComputedStyle(el).visibility !== "hidden";
  const ads = [...document.querySelectorAll(".ad[data-slot]")].filter(vis);
  const content = [...document.querySelectorAll("h1, .card, .player, .about, .stage, .cat-hero, .cat-tile, .filter, .pager, .crumbs, .lineup")].filter(vis);
  const boxes = ads.map(a => ({el: a, r: a.getBoundingClientRect(), slot: a.dataset.slot, size: a.dataset.size}));
  for (const b of boxes) {
    const [w, h] = b.size.split("x").map(Number);
    const r = b.r;
    out.ads.push(b.slot);
    if (r.left < -1 || r.right > W + 1) out.adProblems.push(`${b.slot}: sticks out of the screen`);
    const fits = w <= W - 16 && !b.el.classList.contains("ad-sponsored");   // sponsored tiles are scaled to card size on purpose          // a spot narrower than its ad size is only allowed when the screen is too narrow
    if (fits && (Math.abs(r.width - w) > 1 || Math.abs(r.height - h) > 1)) out.adProblems.push(`${b.slot}: is ${Math.round(r.width)}x${Math.round(r.height)}, should be ${b.size}`);
    for (const c of content) {
      if (b.el.contains(c) || c.contains(b.el)) continue;
      const q = c.getBoundingClientRect();
      const ix = Math.min(r.right, q.right) - Math.max(r.left, q.left), iy = Math.min(r.bottom, q.bottom) - Math.max(r.top, q.top);
      if (ix > 2 && iy > 2) { out.adProblems.push(`${b.slot}: overlaps ${c.className || c.tagName}`); break; }
    }
    const row = b.el.closest(".ad-row, .ad-tile");
    if (row) {
      const p = row.getBoundingClientRect();
      const off = Math.abs((r.left - p.left) - (p.right - r.right));
      if (off > 2) out.adProblems.push(`${b.slot}: off-centre by ${Math.round(off / 2)}px`);
    }
  }
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const a = boxes[i].r, c = boxes[j].r;
    if (Math.min(a.right, c.right) - Math.max(a.left, c.left) > 2 && Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top) > 2)
      out.adProblems.push(`${boxes[i].slot} overlaps ${boxes[j].slot}`);
  }
  return out;
}"""


async def check_page(ctx, path, results, label):
    page = await ctx.new_page()
    errors = []
    page.on("pageerror", lambda ex: errors.append(f"script error: {str(ex)[:160]}"))
    page.on("console", lambda m: errors.append(f"console: {m.text[:160]}") if m.type == "error" and "bannerpromote" not in m.text and "googletagmanager" not in m.text and "Failed to load resource" not in m.text else None)
    try:
        resp = await page.goto(BASE + path, wait_until="load", timeout=45000)
        await page.wait_for_timeout(400)
        data = await page.evaluate(CHECK)
        status = resp.status if resp else 0
    except Exception as ex:
        data, status = {"overflow": 0, "brokenImages": [], "ads": [], "adProblems": []}, f"load failed: {str(ex)[:120]}"
    finally:
        await page.close()
    problems = []
    if status not in (200, 404) and not (path == "/404.html"):
        problems.append(f"status {status}")
    if data["overflow"] > 1:
        problems.append(f"scrolls sideways by {data['overflow']}px")
    problems += [f"broken image {u}" for u in data["brokenImages"][:3]]
    problems += data["adProblems"][:6]
    problems += errors[:4]
    results.append({"where": label, "page": path, "ads": len(data["ads"]), "problems": problems})


async def run(engine_name, launcher, size_name, paths, results, workers=4):
    w, h, phone = SIZES[size_name]
    browser = await launcher.launch(**({"executable_path": "/usr/bin/google-chrome", "args": ["--no-sandbox"]} if engine_name == "chrome" else {}))
    opts = {"viewport": {"width": w, "height": h}}
    if phone and engine_name != "firefox":
        opts.update(is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx = await browser.new_context(**opts)
    queue = list(paths)

    async def worker():
        while queue:
            await check_page(ctx, queue.pop(), results, f"{engine_name} {size_name}")

    await asyncio.gather(*(worker() for _ in range(workers)))
    await browser.close()


async def main():
    quick = "--quick" in sys.argv
    every = []
    for f in sorted((ROOT / "site").rglob("index.html")):
        rel = "/" + str(f.parent.relative_to(ROOT / "site")).replace("\\", "/")
        rel = "/" if rel == "/." else rel + "/"
        if not rel.startswith(("/games/", "/assets/")):
            every.append(rel)
    results = []
    async with async_playwright() as p:
        engines = {"chrome": p.chromium, "firefox": p.firefox, "safari-webkit": p.webkit}
        if not quick:
            print(f"Chrome, desktop: all {len(every)} pages…", flush=True)
            await run("chrome", p.chromium, "desktop", every, results, workers=6)
        for eng, launcher in engines.items():
            for size in SIZES:
                print(f"{eng}, {size}: key pages", flush=True)
                await run(eng, launcher, size, KEY_PAGES, results, workers=3)
    bad = [r for r in results if r["problems"]]
    (ROOT / "site-test-report.json").write_text(json.dumps(results, indent=1))
    print(f"\nChecked {len(results)} page loads; {len(bad)} with problems.")
    for r in bad[:80]:
        print(f"- [{r['where']}] {r['page']}: " + "; ".join(r["problems"]))


if __name__ == "__main__":
    asyncio.run(main())
