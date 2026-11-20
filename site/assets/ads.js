/* =====================================================================================
   AD SETTINGS. This is the only file you need to edit to change ads.

   Every ad spot on the site has a size (e.g. "728x90") and a name (e.g. "game-below-player").
   - Code under `bySize` fills EVERY spot of that size across the whole site.
   - Code under `bySlot` fills ONE specific spot (this wins over bySize).
   - A value of '' shows the grey "Advertisement" placeholder instead.
   - Set `hidePlaceholders: true` so empty spots disappear instead.

   `networkScript` is the ad network's script. It is loaded once per page, after every spot
   has its code, because the network's script looks for the spots when it starts.
   Note: <script> tags pasted inside ad code will not run; put the script URL in networkScript.

   Ads come from BannerPromote. Sizes used on the site and their BannerPromote names:
     728x90  leaderboard        468x60  full-banner        300x250 medium-rectangle   300x600 half-page
     160x600 skyscraper         320x50  mobile-banner      250x250 square (sponsored tiles, scaled to card size)
   Slot names are listed in README.md.
   ===================================================================================== */
const spot = name => `<div data-gb-spot="${name}"></div>`;

window.ARCADE_ADS = {
  networkScript: 'https://bannerpromote.com/embed.js.php',
  adsense: false,          // set true only for Google AdSense
  hidePlaceholders: false,
  bySize: {
    '728x90':  spot('leaderboard'),
    '468x60':  spot('full-banner'),
    '300x250': spot('medium-rectangle'),
    '300x600': spot('half-page'),
    '160x600': spot('skyscraper'),
    '250x250': spot('square'),          // sponsored tiles inside category grids, shown at card size
    '320x50':  spot('mobile-banner')
  },
  bySlot: {
    // Example: show a different banner in one spot
    // 'game-beside-about': spot('large-rectangle'),
  }
};

(() => {
  const cfg = window.ARCADE_ADS;
  let loads = 0;
  // The network's script scans the page for its spots once each time it runs, so it is loaded again whenever
  // new spots have been filled in (spots it already handled are marked and skipped).
  const runNetwork = () => {
    if (!cfg.networkScript || loads > 6) return;
    loads++;
    const s = document.createElement('script');
    s.async = true; s.dataset.adNetwork = '1';
    s.src = cfg.networkScript + (loads > 1 ? (cfg.networkScript.includes('?') ? '&' : '?') + 'r=' + loads : '');
    if (cfg.adsense) s.crossOrigin = 'anonymous';
    document.head.append(s);
  };
  const fill = () => {
    // Check which spots are shown first, then fill them, so the page is measured only once
    const shown = [...document.querySelectorAll('.ad[data-slot]')]
      .filter(slot => !slot.dataset.done && slot.getClientRects().length);   // hidden at this screen size: skip for now
    shown.forEach(slot => {
      slot.dataset.done = '1';
      const html = cfg.bySlot[slot.dataset.slot] || cfg.bySize[slot.dataset.size] || '';
      if (!html) { if (cfg.hidePlaceholders) slot.hidden = true; return; }
      slot.classList.add('filled');
      slot.innerHTML = '<div class="ad-content"></div>';
      slot.firstChild.innerHTML = html;
      if (cfg.adsense && slot.querySelector('ins.adsbygoogle')) {
        try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) { console.warn('Ad could not start', e); }
      }
    });
    if (shown.length) runNetwork();
  };
  // A banner request that failed leaves its spot empty: give those spots one more try
  const retryEmpty = () => {
    const empty = [...document.querySelectorAll('.ad.filled [data-gb-spot]')]
      .filter(el => !el.children.length && el.getClientRects().length);
    if (!empty.length) return;
    empty.forEach(el => el.removeAttribute('data-gb-loaded'));
    runNetwork();
  };
  const start = () => {
    fill();
    setTimeout(retryEmpty, 5000);
    // Spots that only appear at another screen size (window resized, phone turned) get filled when they show up
    let t = 0;
    addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => { fill(); setTimeout(retryEmpty, 5000); }, 300); });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
