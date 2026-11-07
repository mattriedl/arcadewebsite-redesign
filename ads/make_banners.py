#!/usr/bin/env python3
"""Render the ArcadeWebsite banner ads from ads/src/ad.html.

    python3 ads/make_banners.py

Writes, for each size, a static PNG and an animated GIF to ads/banners/, plus a preview page.
The animation is about 5 seconds, plays 3 times (about 15 seconds in all) and stops on the
"Play free" frame, which keeps it inside common ad network limits (30 seconds, 3 loops).
"""
import asyncio
import io
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "banners"
SIZES = {  # BannerPromote embed name: (width, height)
    "medium-rectangle": (300, 250), "leaderboard": (728, 90), "full-banner": (468, 60), "mobile-banner": (320, 50),
    "skyscraper": (160, 600), "half-page": (300, 600), "large-rectangle": (336, 280), "square": (250, 250),
}
FPS = 10
PLAYS = 3
MAX_KB = 150   # common ad network limit for banner files
# gifsicle shrinks the GIFs further. Install with "npm i gifsicle" or your package manager, or set GIFSICLE.
GIFSICLE = os.environ.get("GIFSICLE") or shutil.which("gifsicle")


def shrink(path):
    """Compress a GIF with gifsicle, a little more each time, until it's under MAX_KB."""
    if not GIFSICLE:
        return
    for lossy in (25, 40, 60, 80, 100):
        tmp = path.with_suffix(".tmp.gif")
        subprocess.run([GIFSICLE, "-O3", f"--lossy={lossy}", str(path), "-o", str(tmp)], check=True)
        if tmp.stat().st_size // 1024 <= MAX_KB or lossy == 100:
            tmp.replace(path)
            return
        tmp.unlink()


BRAND = ["#ff5c8a", "#3d9bff", "#22d3b6", "#ff8a3d", "#b07cff", "#9ad94a", "#ffc83d", "#c98a00", "#2a1d00",
         "#ffffff", "#f2f3ff", "#b9bce6", "#12142e", "#1a1d40", "#fff4c2", "#5a4a20", "#6c72c4", "#050616"]


def to_gif_frames(frames, static, colors=80):
    """One shared palette for every frame keeps colours steady and the file small. It holds the exact
    brand colours (tags, coin, button, text) plus the best colours for everything else, taken from
    the static banner (which shows every element) and a spread of frames."""
    w, h = frames[0].size
    picks = [static] + frames[:: max(1, len(frames) // 8)][:8] + [frames[-1]]
    strip = Image.new("RGB", (w, h * len(picks)))
    for i, f in enumerate(picks):
        strip.paste(f, (0, i * h))
    rest = colors - len(BRAND)
    adaptive = strip.quantize(colors=rest, method=Image.Quantize.MEDIANCUT).getpalette()[: rest * 3]
    brand = [int(c[i:i + 2], 16) for c in BRAND for i in (1, 3, 5)]
    pal = Image.new("P", (1, 1))
    pal.putpalette(brand + adaptive + [0] * (768 - len(brand) - len(adaptive)))
    return [f.quantize(colors=colors, palette=pal, dither=Image.Dither.NONE) for f in frames]


async def main():
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--allow-file-access-from-files"])
        for name, (w, h) in SIZES.items():
            page = await b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            await page.goto(f"file://{HERE / 'src' / 'ad.html'}?w={w}&h={h}")
            await page.evaluate("document.fonts.ready")
            await page.wait_for_timeout(300)
            # static
            await page.evaluate("renderStatic()")
            png = await page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h})
            static = Image.open(io.BytesIO(png)).convert("RGB")
            static.save(OUT / f"{name}-{w}x{h}-static.png", optimize=True)
            # animated
            dur = await page.evaluate("DURATION")
            frames = []
            n = int(dur * FPS)
            for i in range(n + 1):
                await page.evaluate(f"render({i / FPS})")
                frames.append(Image.open(io.BytesIO(await page.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("RGB"))
            gif = to_gif_frames(frames, static, colors=56 if w * h > 150000 else 80)   # the biggest size needs fewer colours to stay under MAX_KB
            durations = [round(1000 / FPS)] * len(gif)
            durations[-1] = 1600                      # hold the last frame a little before looping
            gif[0].save(OUT / f"{name}-{w}x{h}-animated.gif", save_all=True, append_images=gif[1:], duration=durations,
                        loop=PLAYS - 1, optimize=True, disposal=1)
            shrink(OUT / f"{name}-{w}x{h}-animated.gif")
            await page.close()
            s = (OUT / f"{name}-{w}x{h}-static.png").stat().st_size // 1024
            a = (OUT / f"{name}-{w}x{h}-animated.gif").stat().st_size // 1024
            print(f"{name:17} {w}x{h}: static {s} KB, animated {a} KB ({len(gif)} frames)")
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
