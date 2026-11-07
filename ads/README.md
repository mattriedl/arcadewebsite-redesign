# Banner ads

Banner ads for arcadewebsite.com in all eight BannerPromote sizes. Each size has a static PNG and an animated GIF in `banners/`, and every file is under 150 KB. Open `preview.html` through a local web server to see them all.

| BannerPromote name | Size | Static | Animated |
|---|---|---|---|
| leaderboard | 728×90 | `leaderboard-728x90-static.png` | `leaderboard-728x90-animated.gif` |
| full-banner | 468×60 | `full-banner-468x60-static.png` | `full-banner-468x60-animated.gif` |
| mobile-banner | 320×50 | `mobile-banner-320x50-static.png` | `mobile-banner-320x50-animated.gif` |
| medium-rectangle | 300×250 | `medium-rectangle-300x250-static.png` | `medium-rectangle-300x250-animated.gif` |
| large-rectangle | 336×280 | `large-rectangle-336x280-static.png` | `large-rectangle-336x280-animated.gif` |
| square | 250×250 | `square-250x250-static.png` | `square-250x250-animated.gif` |
| half-page | 300×600 | `half-page-300x600-static.png` | `half-page-300x600-animated.gif` |
| skyscraper | 160×600 | `skyscraper-160x600-static.png` | `skyscraper-160x600-animated.gif` |

Link every banner to `https://arcadewebsite.com/`.

## The idea

"Insert coin? Nope. Free." The ads open on an arcade coin slot and flip it: every game is free. Marquee lights chase around the edge like an arcade sign, and the colors, fonts and coin logo match the site, so the click lands somewhere that looks like the ad.

The animation runs about 5 seconds: a coin drops into the slot, "Free play!" stamps in, a counter rolls up to 1,500+ games while the category tags pop in, then "Your next high score is one click away" with the Play free button pulsing. It plays three times (about 15 seconds) and stops on that last frame, which fits common ad network rules (30 seconds and 3 loops at most).

## Changing them

The design is one page, `src/ad.html`, which lays itself out for each size. Edit the text or colors there, then rebuild:

```
python3 ads/make_banners.py
```

It needs Python with Pillow and Playwright, Google Chrome, and optionally `gifsicle` (it shrinks the GIFs; install with `npm i gifsicle` or your package manager, or point the `GIFSICLE` variable at it). The banners say "1,500+ games" so they stay accurate as games are added or removed; to change it, edit `src/ad.html`.
