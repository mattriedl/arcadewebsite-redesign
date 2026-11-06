# arcadewebsite.com redesign

The redesigned arcadewebsite.com: all 1,562 games and 12 categories from the live site, each on its own page at the **same address as today**, so links, bookmarks and search rankings carry over.

- **Homepage** with an auto-rotating featured area that picks a new set of games every 2 days by itself, category tiles, editorial shelves and a shelf for every category.
- **Game pages** with a click-to-play player, fullscreen and restart buttons, game info, sharing and more games from the same category.
- **Category pages**, an **A–Z page of every game**, **search** and a **404 page**.
- **Ad spots on every page** in standard sizes (14 on each game page, more on the homepage and category pages), all controlled from one file.
- **Google Tag Manager** (container `GTM-TVMCJHRM`) on every page.

Nothing here is live until you upload it. The live site is backed up separately in the `live-site-backup` branch of `mattriedl/arcaderom`.

## Folders

```
site/        The finished website. This is what gets uploaded to the server.
data/        The game list, categories and homepage settings (edit these).
src/         Styles, scripts, ad settings and the Tag Manager snippet.
public/      Game files, thumbnails and robots.txt, copied into site/ as-is.
build.py     Turns data/ + src/ + public/ into site/.
docs/        Notes, including files the live site is missing.
```

## Preview it on your computer

You need Python 3 (already on Mac and Linux; on Windows install it from python.org).

```
python3 build.py
python3 -m http.server -d site 8000
```

Then open http://localhost:8000. The site has to be opened through that address rather than by double-clicking the files, because pages use paths that start from the site root.

To test on the real server before switching over, upload `site/` to a test location such as a `staging.arcadewebsite.com` subdomain. It must be served from the root of a domain or subdomain, not from a sub-folder like `arcadewebsite.com/new/`.

## Going live

1. Run `python3 build.py`.
2. Ads are already set up (see Ads below). If you remove a size's code, set `hidePlaceholders: true` in `src/assets/ads.js` so empty spots disappear.
3. Upload everything **inside** `site/` to the web root, replacing the old files. The game files and thumbnails are the same as the live ones.
4. Point your server's 404 page at `/404.html` if it isn't picked up automatically.
5. In Google Search Console, resubmit `https://arcadewebsite.com/sitemap.xml`.

## Editing games

All game info is in `data/games.json`, one entry per game:

```json
{
  "slug": "drive-mad",                         // the address: /game/drive-mad/
  "title": "Drive Mad",
  "category": "racing",                        // a slug from data/categories.json
  "description": "...",                        // search engine description and page text
  "about": ["..."],                            // paragraphs in the About section
  "thumbnail": "/thumbnails/cldrivemad.png",
  "src": "/games/cldrivemad.html",             // the file the player loads
  "related": ["wheel-y6", "..."]               // games shown under the player
}
```

To add a game, put its file in `public/games/` and its 480×320 thumbnail in `public/thumbnails/`, add an entry, and run `python3 build.py`. Categories, their descriptions and their game order are in `data/categories.json`.

## Featured games

`data/featured.json` controls the featured area on the homepage:

| Setting | What it does |
|---|---|
| `daysPerRotation` | How often a new set of games is featured (default 2 days). |
| `gamesPerRotation` | How many games are in each set (default 6). |
| `secondsPerSlide` | How long each game is shown before it moves to the next (default 7). |
| `startDate` | The day the first set starts. |
| `favorites` | Featured first, before the rest of the library. |
| `includeWholeLibrary` | After the favorites, cycle through every other game in a fixed shuffled order, so each one gets a turn before any repeats. |
| `pinned` | Games always shown in the set, for example a new game you want to promote. |

The set changes on its own in each visitor's browser based on the date; you don't need to rebuild for it to rotate. Visitors can pause the slideshow, and it pauses while the mouse is over it. It stays still for people who have turned on reduced motion.

## Ads

Ads come from BannerPromote. Every ad spot reads from `src/assets/ads.js`, which gives each size its BannerPromote embed name and loads `https://bannerpromote.com/embed.js.php` once per page:

| Size | BannerPromote name |
|---|---|
| 728×90 | `leaderboard` |
| 300×250 | `medium-rectangle` |
| 300×600 | `half-page` |
| 160×600 | `skyscraper` |
| 320×50 | `mobile-banner` |

To show a different banner in one spot, add it under `bySlot`, for example `'game-beside-about': spot('large-rectangle')`. Wide banners swap for a phone-sized spot on small screens (named the same with `-mobile` on the end), and spots that are hidden at the current screen size don't request a banner.

| Page | Spot name | Size |
|---|---|---|
| Every page | `*-top` / `*-top-mobile` | 728×90 / 320×50 |
| Home | `home-beside-categories` | 300×250 |
| Home | `home-after-categories`, `home-after-trending`, `home-between-1` … `3`, `home-bottom` | 728×90 (phones: 320×50, or 300×250 after trending) |
| Game | `game-left` | 160×600 |
| Game | `game-right-top`, `game-right` | 300×600, 300×250 |
| Game | `game-below-player` / `-mobile` | 728×90 / 300×250 |
| Game | `game-beside-about` | 300×250 |
| Game | `game-related-1`, `-2` / `-mobile` (inside the game grid) | 728×90 / 300×250 |
| Game | `game-bottom` / `-mobile` | 728×90 / 320×50 |
| Category | `category-below-header`, `category-bottom` / `-mobile` | 728×90 / 320×50 |
| Category | `category-side-top`, `category-side` | 300×600, 300×250 |
| Category | `category-in-grid-N` / `-mobile` (every 20 games) | 728×90 / 300×250 |
| All games | `all-side-top`, `all-side` | 300×600, 300×250 |
| All games | `all-between-N` / `-mobile`, and in-grid spots per letter | 728×90 / 300×250 |
| Search | `search-side-top`, `search-side`, `search-bottom` | 300×600, 300×250, 728×90 |

To switch to a different network later, change `networkScript` and the codes under `bySize`. Check the network's rules on ad density, and your privacy and consent requirements.

## Google Tag Manager

The container `GTM-TVMCJHRM` loads at the top of every page from `src/tag-manager.html`, with the `<noscript>` part from `src/tag-manager-body.html`. It uses Google's standard Tag Manager snippet. Set up Google Analytics as a tag inside the Tag Manager container, and check it with Tag Manager's Preview mode once the site is live.

## Changes from the live site

- Same addresses, titles and descriptions for every page; sitemap and robots.txt carried over.
- Games now load when the visitor clicks Play rather than as soon as the page opens, so pages load faster and visitors see the ads around the player first.
- Each game page's structured data was broken on the live site and is now a valid `VideoGame` entry, which search engines can read.
- The unused Google Analytics placeholder script was replaced by Tag Manager.
- `docs/broken-files.md` lists 67 files the live game files ask for that are missing on the server.
