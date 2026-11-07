# Blog writing guide

This is the procedure for every new ArcadeWebsite blog article. The automatic posting task follows it word for word, and so should anyone writing a post by hand.

**The goal:** articles that rank because they are the most useful page for the search. Google's spam policies count mass-produced, low-value pages written to catch searches as "scaled content abuse". So each post has to be accurate, specific to the games on this site, and better than what already ranks. One good post every three days beats ten thin ones.

## 1. Pick the keyword

1. Read `blog/topics.md`. Never target a keyword or search intent that an existing post already covers; two posts competing for the same search hurt each other. To go deeper on a topic that's already covered, update the existing post instead (change `updated:` in its front matter).
2. Pick one main keyword. Use the backlog in `topics.md`, or research a new one:
   - Search the web for the candidate and its variations. Look at who ranks on page one. Big brands and huge portals (Poki, CrazyGames, Coolmath) on every result means it's too hard. Forum threads, small blogs or thin listicles on page one mean it's winnable.
   - Good keywords are longer and specific ("2 player games on one keyboard", "games like Slope", "best idle games to play in a browser"), have clear demand (autocomplete suggestions, "People also ask" questions, several sites targeting it), and match games that are on this site.
   - The intent has to be something an article can answer: a list ("best X games"), a how-to ("how to play X", "X controls"), a comparison ("games like X") or a question.
3. Check the site has enough real games for it. Look in `data/games.json` and `data/descriptions.json`, and check `data/game-play-test.json`.
   - Games marked `played` are fine.
   - A game marked "blank or didn't load" may still work, because the automatic test couldn't tell. Before featuring one, check it yourself: serve `site/` locally (`python3 -m http.server -d site 8765`), open its game page with Playwright, click the Play button, wait 10 seconds, take a screenshot and look at it. Only feature it if the game is visibly running.
   - Never feature removed games (`data/removed-games.json`).
4. **Don't feature emulated console games** (copies of Nintendo, Sega or Sony titles such as Mario, Pokémon or Zelda; see `docs/copyright-review.md`). Promoting them invites copyright complaints. Feature original browser games.
5. Record the choice in `topics.md` before writing.

## 2. Research the facts

- Every fact has to be checked: controls, game modes, who made the game, how many players. Check against the game's own description in `data/descriptions.json`, the game's start screen, or the developer's or a major game portal's page for that game. Leave out anything you can't check, and never guess controls.
- Never invent statistics, quotes, test results, player counts or personal stories. "We tested" is only allowed for something that really happened. The site's November 2026 play test (`data/game-play-test.json`) counts.
- Read the top 3 to 5 ranking pages to see what they cover, then cover it better: more accurate controls, real tips, a comparison table, direct links to playable pages.

## 3. Write

**Length:** 1,200–2,000 words for lists and guides, or 800–1,200 for a single question. Stop when the question is fully answered; never pad.

**Structure:**
- **H1:** the main keyword near the start, plus a reason to click (a number, "free", "no download", the year only if it's really a yearly list). Up to about 70 characters.
- **First paragraph:** answer the search directly in 2–3 sentences, naming the top picks. This is what Google lifts into featured snippets and AI answers.
- **Second paragraph:** how the games were picked, honestly.
- **A comparison table** near the top for list posts.
- **H2 for each main section,** with the main keyword or a close variation in some of them (not all). H3 for sub-points.
- **For each game:** what it is, controls, a practical tip, and a link to its game page.
- **A `[[games: slug, slug, ...]]` line** after the main list shows playable game cards.
- **A "Frequently asked questions" H2 at the end,** with 4–6 `###` questions taken from real "People also ask" questions and related searches. Each answer is 1–3 sentences and starts with the answer.

**Keywords:** use the main keyword in the H1, the first 100 words, one H2, the description and the URL. Use variations and related terms naturally (the `keywords:` list). Never repeat the exact phrase unnaturally.

**Links:**
- 8 or more internal links to `/game/<slug>/` pages, at least 2 links to `/category/<slug>/` pages, and a link to one earlier post if it's relevant.
- Optionally 1–2 outside links to official developer pages.
- Use descriptive link text (the game's name), never "click here".

**Voice:** plain, friendly, second person ("you"), short sentences, no hype words ("ultimate", "insane", "mind-blowing"), and no filler intros ("In today's digital age…"). Write for a 12–16-year-old reader and their parents.

**Honesty about school networks:** if "unblocked" or "school" comes up, say plainly that school and work networks may block game sites and that it depends on the network's rules. Never give instructions for getting around a school's or employer's filters (proxies, VPNs, tab cloaking).

## 4. The file

Create `blog/posts/<slug>.md`. The slug is the main keyword in lowercase with hyphens, 3–6 words, with no dates or stop words when they aren't needed (`best-2-player-games-one-keyboard`).

```
---
title: The H1 (about 70 characters max)
seo_title: Title tag, 60 characters max including " | ArcadeWebsite"
description: Meta description, 140–155 characters, contains the keyword, says what the reader gets
keyword: main keyword
keywords: 4–8 related phrases, comma separated
date: YYYY-MM-DD (today, Pacific time)
games: slug-1, slug-2, ... (the games featured, best first; the first four make the share image)
image_alt: Screenshots of <first four game names>
---
Markdown body…
```

The build makes everything else:
- the page, its share image, the contents list and the ads
- BlogPosting, Breadcrumb and FAQ structured data
- the sitemap entry, the RSS feed entry and the homepage "From the blog" cards
- "Featured in" links on every featured game's page

## 5. Check before publishing

1. `python3 build.py`, which must finish without errors.
2. `python3 tools/seo_check.py`, which must end with `Problems: 0`.
3. Open `site/blog/<slug>/index.html` and check:
   - the title is 60 characters or fewer and the description 155 or fewer
   - every `/game/` link works (the build fails on unknown slugs in `games:`; check the links in the body by hand)
   - the FAQ shows up
4. Re-read the article once just for facts (every control and claim) and once for readability.
5. Add the post to the "Published" table in `blog/topics.md`.

## 6. Publish

Commit the post, the rebuilt `site/` and the `topics.md` update to `main` and push. Cloudflare deploys the push to arcadewebsite.com within a couple of minutes.
