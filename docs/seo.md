# Search engine optimization

What was done to every page, what to do when the site goes live, and how to keep it in good shape.
Run `python3 tools/seo_check.py` after every build: it checks every page the way a search engine reads it and lists anything that needs fixing.

## What each page targets

| Page | Main search terms | Title pattern |
|---|---|---|
| Homepage | free online games, free browser games, play games online | Free Online Games - Play 1,562 Games Free \| ArcadeWebsite |
| Category (×12) | free [category] games, [category] games online, play [category] games | Racing Games - Play Free Online Racing Games \| ArcadeWebsite |
| Game (×1,562) | [game name], play [game name] online, [game name] free, how to play [game name] | Slope - Play Online for Free \| ArcadeWebsite |
| All games A–Z | all free games, list of online games | All 1,562 Free Online Games A to Z \| ArcadeWebsite |

Every page has a unique title and a unique meta description of up to 160 characters, so search results show the whole thing.

## What's on every page

- **Game names people actually search for.** 722 names generated from file names were corrected, for example "Bald is Basics" to "Baldi's Basics" and "Do Kid Oki Literature Club" to "Doki Doki Literature Club". The full list is in `docs/name-changes.md`. Page addresses did not change.
- **Real content in the HTML**, readable without JavaScript, so Google, Bing and AI assistants can all read it: a summary, "About", "How to play" and an FAQ on every game page (380 to 730 words of readable text per page, including navigation); an introduction, a list of popular games and an FAQ on every category page.
- **Hand-written descriptions** for 171 of the most-searched games (`data/descriptions.json`). Other games get copy built from what's known about them: their category, series and similar games.
- **One H1 per page**, with H2 sections for About, How to play, FAQ, the series and similar games.
- **Internal links:** breadcrumbs, the category bar on every page, a link from each game to its category, other games in the same series, 24 similar games, linked game names in the text and FAQ, the A–Z page and a site map page that link every game.
- **Structured data (schema.org JSON-LD):** `VideoGame` with image, price and genre on game pages; `BreadcrumbList` everywhere; `FAQPage` on game and category pages; `CollectionPage` with an `ItemList` of games on category pages; `WebSite` with a search box and `Organization` on the homepage. Google currently shows FAQ rich results only for a few authoritative sites, but Bing and AI assistants still use FAQ markup.
- **Social and sharing tags:** Open Graph and Twitter card tags with the game's image on every page.
- **Canonical tags:** every page names its own address as the main version. 17 pages that load exactly the same game file as another page point to that page instead, so they don't compete with each other.

## Sitemaps and crawling

- `sitemap.xml` lists all 1,599 pages that should appear in search, with each game's image and a last-changed date that only changes when the page really changes (tracked in `data/lastmod.json`).
- `/sitemap/` is a site map page that links every game, grouped by category.
- `robots.txt` lets every search engine and AI assistant read the site (Google, Bing, DuckDuckGo, Apple, ChatGPT, Claude, Perplexity and others). It blocks only the search results page and the raw game files in `/games/`, so the game pages themselves are what get listed.
- `llms.txt` is a plain-text summary of the site with its categories and popular games, which some AI assistants read.
- `feed.xml` is an RSS feed of featured games.

## Speed (Google Lighthouse, phone settings)

| Page | SEO | Accessibility | Speed |
|---|---|---|---|
| Game page | 100 | 100 | 99 |
| Homepage | 100 | 100 | 92 |
| Category page | 100 | 100 | 95–98 |
| All games A–Z (one page per letter) | 100 | 100 | 92–95 |

Thumbnails are served as WebP (72% smaller), the game only loads when someone clicks Play, off-screen cards aren't drawn until scrolled to, and fonts don't block the first paint.

Big lists are split into numbered pages so they load quickly:
- Categories with more than 200 games (currently only Arcade, with 897) show 60 games per page: `/category/arcade/`, then `/category/arcade/page/2/` up to page 15. Page 1 has the introduction and FAQ; later pages have their own title and description. To change the numbers, edit `PER_PAGE` and `PAGINATE_OVER` in `build.py`.
- The A–Z list has one page per letter: `/all-games/` (numbers and A), then `/all-games/b/` to `/all-games/z/`, each titled for searches like "games starting with B".
- The filter box on these pages searches the whole category or all games, not just the page you're on.

## When the site goes live

1. **Google Search Console** (search.google.com/search-console): add `arcadewebsite.com` as a Domain property (Cloudflare can add the DNS record for you), then submit `https://arcadewebsite.com/sitemap.xml` under Sitemaps.
2. **Bing Webmaster Tools** (bing.com/webmasters): import the site from Google Search Console, which also covers Yahoo and DuckDuckGo, then submit the sitemap.
3. **IndexNow:** run `python3 tools/indexnow.py` to tell Bing about every page right away. The key file is already in `site/`.
4. **Check a few pages** with Google's URL Inspection tool in Search Console and the Rich Results Test (search.google.com/test/rich-results).
5. **Turn on Cloudflare caching and compression** for the site, so pages and images load fast everywhere.

## What decides first-page rankings beyond the site itself

The site is now set up the way search engines want, but nobody can guarantee first-page positions. For popular games you're competing with large, long-established game sites. What makes the biggest difference from here:

- **Links from other sites** (backlinks): mentions on gaming forums, Reddit, Discord communities, YouTube video descriptions and game lists. This is the single biggest factor for competitive game names.
- **Long-tail searches first.** "how to play [game]", "[game] controls" and "games like [game]" are easier to rank for, and every game page now answers them.
- **More hand-written descriptions.** Add entries to `data/descriptions.json` for the games that get the most visits (Search Console shows which).
- **Time.** New pages and the name changes usually take a few weeks to a few months to settle in search results.
- **Copyright.** See `docs/copyright-review.md`. Valid copyright removal notices remove pages from Google, and a high number of them can lower the whole site's rankings.
