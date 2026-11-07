#!/usr/bin/env python3
"""Take a real screenshot of each game running in its player, to use as its thumbnail.

    python3 -m http.server -d site 8765 &            # serve the built site locally
    python3 tools/capture_screenshots.py              # every game not done yet
    python3 tools/capture_screenshots.py slope run-3  # just these games (re-takes them)

For each game it opens the game page, clicks Play, and takes three shots over about 25 seconds,
clicking the game and pressing Enter and Space in between to get past splash and "press start"
screens. It keeps the most detailed shot. Shots that are blank or nearly blank are rejected and the
game keeps its current thumbnail. Screenshots go to public/screenshots/<slug>.webp and .jpg, and
data/screenshots.json records which games have one. New screenshots appear on the site only after they're
checked by eye and added to data/screenshot-reviewed.json (or data/screenshot-rejects.json to hide them). Progress is saved as it goes,
so the run can be stopped and started again.
"""
import asyncio
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "screenshots"
INDEX = ROOT / "data" / "screenshots.json"          # slug -> image path, for games with a good screenshot
STATUS = ROOT / "data" / "screenshots-status.json"  # slug -> what happened, for every game tried
BASE = "http://localhost:8765"
WORKERS = 3
RESTART_EVERY = 60   # restart the browser now and then so memory doesn't build up


def score(img):
    """How much is going on in a frame: blank screens and logo splashes score low."""
    small = img.convert("RGB").resize((160, 120))
    spread = sum(ImageStat.Stat(small).stddev) / 3
    colours = len(set(small.resize((80, 60)).getdata()))
    edges = ImageStat.Stat(small.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]
    ok = spread > 18 and colours > 60
    return ok, round(edges * 2 + spread * 0.5 + min(colours, 1500) / 60, 1)


async def capture(browser, slug):
    ctx = await browser.new_context(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    page = await ctx.new_page()
    shots = []
    try:
        await page.goto(f"{BASE}/game/{slug}/", wait_until="domcontentloaded", timeout=30000)
        await page.click(".player-start", timeout=10000)
        frame = page.locator(".player-frame")
        box = await frame.bounding_box()
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        game = page.frame_locator(".player-frame iframe")
        for wait, keys in ((7000, []), (6000, ["Enter"]), (7000, ["Space", "Enter"])):
            # Press a visible Play / Start button inside the game if there is one, otherwise click the middle
            try:
                btn = game.get_by_text(re.compile(r"^\s*(play|start|play now|start game|click to play|tap to play)\s*!?$", re.I)).first
                await btn.click(timeout=1500)
            except Exception:
                await page.mouse.click(cx, cy)
            for k in keys:
                await page.keyboard.press(k)
                await page.wait_for_timeout(300)
            await page.wait_for_timeout(wait)
            png = await frame.screenshot(timeout=15000)
            img = Image.open(io.BytesIO(png)).convert("RGB")
            ok, s = score(img)
            if ok:
                shots.append((s, img))
        if not shots:
            return slug, None, "no usable frame"
        s, img = max(shots, key=lambda t: t[0])
        w, h = img.size
        tw = min(w, int(h * 4 / 3)); th = int(tw * 3 / 4)
        left, top = (w - tw) // 2, (h - th) // 2
        img = img.crop((left, top, left + tw, top + th)).resize((400, 300), Image.LANCZOS)
        OUT.mkdir(parents=True, exist_ok=True)
        img.save(OUT / f"{slug}.webp", "WEBP", quality=82, method=6)
        img.save(OUT / f"{slug}.jpg", "JPEG", quality=84, optimize=True, progressive=True)
        return slug, f"/screenshots/{slug}.jpg", f"ok (score {s})"
    except Exception as ex:
        return slug, None, f"error: {str(ex).splitlines()[0][:80]}"
    finally:
        await ctx.close()


def load(p):
    return json.loads(p.read_text()) if p.exists() else {}


async def main(slugs):
    index, status = load(INDEX), load(STATUS)
    queue = asyncio.Queue()
    for s in slugs:
        queue.put_nowait(s)
    done, lock = 0, asyncio.Lock()

    def save():
        INDEX.write_text(json.dumps(index, indent=0, sort_keys=True))
        STATUS.write_text(json.dumps(status, indent=0, sort_keys=True))

    async with async_playwright() as p:
        async def new_browser():
            return await p.chromium.launch(executable_path="/usr/bin/google-chrome",
                                           args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required", "--mute-audio",
                                                 "--disable-dev-shm-usage"])

        async def worker():
            nonlocal done
            browser, n = await new_browser(), 0
            while not queue.empty():
                s = queue.get_nowait()
                try:   # never let one game stall the run
                    slug, path, result = await asyncio.wait_for(capture(browser, s), timeout=90)
                except asyncio.TimeoutError:
                    slug, path, result = s, None, "error: took longer than 90 seconds"
                    try:
                        await browser.close()
                    except Exception:
                        pass
                    browser = await new_browser()
                async with lock:
                    if path:
                        index[slug] = path
                    else:
                        index.pop(slug, None)
                    status[slug] = result
                    done += 1
                    print(f"[{done}/{len(slugs)}] {slug}: {result}", flush=True)
                    if done % 10 == 0:
                        save()
                n += 1
                if n % RESTART_EVERY == 0:
                    await browser.close()
                    browser = await new_browser()
            await browser.close()

        await asyncio.gather(*(worker() for _ in range(WORKERS)))
    save()
    print(f"Finished. {len(index)} games have a screenshot.")


if __name__ == "__main__":
    games = json.loads((ROOT / "data" / "games.json").read_text())
    if sys.argv[1:]:
        todo = sys.argv[1:]
    else:
        tried = load(STATUS)
        todo = [g["slug"] for g in games if g["slug"] not in tried]
    print(f"{len(todo)} games to capture", flush=True)
    asyncio.run(main(todo))
