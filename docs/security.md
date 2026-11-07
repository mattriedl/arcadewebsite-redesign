# Security review

Reviewed November 2026. This covers the redesigned site and the 1,536 game files it serves.

## The site itself: no problems found

- **Static pages only.** There are no logins, no forms that send data, no database and no server code, so there is nothing to break into on the server side. Search and filtering run in the visitor's browser.
- **HTTPS everywhere.** Every page, script, image and ad tag loads over `https://`. The headers below tell browsers to upgrade any stray `http://` request and to always use HTTPS for the domain.
- **No unsafe outside links.** None of our own pages open links in a new tab without `rel="noopener"`.
- **Games are kept in their own frame.** A game loads only when the visitor presses Play, inside an iframe.
- **Search engines skip the raw game files.** `/games/` is blocked in robots.txt and marked `noindex`, so visitors land on the proper game pages.
- **Third-party code on our pages:** Google Tag Manager (GTM-TVMCJHRM) and the BannerPromote ad script. Nothing else.

## Security headers

These are set in `public/_headers`, which Cloudflare applies automatically. When the site goes live on the current Apache server, add the same rules to `.htaccess`:

```apache
<IfModule mod_headers.c>
  Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set Content-Security-Policy "frame-ancestors 'self'; upgrade-insecure-requests; object-src 'none'; base-uri 'self'; form-action 'self'"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "geolocation=(), payment=(), usb=(), serial=(), bluetooth=(), browsing-topics=()"
  Header always set Cross-Origin-Opener-Policy "same-origin-allow-popups"
  <If "%{REQUEST_URI} =~ m#^/games/#">
    Header set X-Robots-Tag "noindex"
  </If>
</IfModule>

# Send http:// visitors to https://
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

What the headers do:

- `X-Frame-Options` and `frame-ancestors` stop other sites from embedding arcadewebsite.com pages inside their own pages to pass them off as theirs.
- `nosniff` stops browsers from treating a file as a type it isn't.
- `Permissions-Policy` switches off location, payment and device access that no game here needs.
- `object-src 'none'` blocks Flash and other old browser plug-ins.

A full script whitelist was deliberately left out of the Content-Security-Policy. The game files pull scripts from dozens of other places, and a strict list would break many games.

## Game files: found and fixed

- **Retro Bowl (two copies: `bowl-alt`, `retro-bowl-fixed`).** These contained a site-lock that took over the whole browser tab and sent visitors to another site. Both were removed and now forward to the working Retro Bowl page.
- **`eaglercraft-indev-offline-6`.** This sent visitors to a missing file. It was removed and now forwards to the working copy.
- **Cookie Clicker.** Pressing Play downloaded a .docx file. It now points to a working game file.

## Game files: still there, your decision

None of these are viruses or malware. They are third-party code that came bundled with the game files from wherever they were originally copied. They don't harm visitors' computers, but you may not want them on your site.

| What | Games | What it means |
|---|---|---|
| Other people's Google Analytics IDs | 68 games carry `G-MENBM6GSNY`, 13 carry `G-F32JC4N3VY`, plus about 35 other IDs in one or two games each | Visitor stats from those games are sent to whoever uploaded them originally |
| Other ad networks | `basket-bros` (ads plus push notifications), `1v1lolno-about-blank` (CPMStar) | Ads that aren't yours, and that you don't earn from |
| Google AdSense IDs from other publishers | 2 games | These may be against AdSense rules for your site |
| Tab cloaking (changes the browser tab's title and icon) | 14 games, including drift-hunters, smash-karts, slow-roads, escape-road | Made to hide games from school monitoring. It's harmless, but can confuse visitors |
| Opens pop-up windows | 15 games, mostly Eaglercraft (opens its own settings and help windows) | Mostly normal for those games |
| Hidden or compressed code (`eval`/`atob`) | `circlo-o2`, `escape-road` | Usually a game's own packed code |

Checked and harmless:

- The `reimageplus`/`outbrain` strings are ad-blocker lists, not ads.
- The Yandex redirect only runs on Yandex's own site.
- The Eaglercraft "refresh" lines only run when JavaScript is switched off.

**Recommendation.** Remove the other people's analytics IDs, the outside ad and push scripts, and the other publishers' AdSense tags from the game files, then re-test those games. Usually only a few lines need to come out of each file, but a game can stop working if its loader depends on one of them, so each changed game has to be played again before going live.

## How to re-check

- `python3 tools/site_test.py` loads the pages in Chrome, Firefox and Safari's engine at eight screen sizes. It reports script errors, broken images, sideways scrolling and misplaced ads.
- `python3 tools/seo_check.py` checks titles, descriptions, canonical links, structured data and the sitemap.
