/* =====================================================================================
   AD SETTINGS. This is the only file you need to edit to turn ads on.

   Every ad spot on the site has a size (e.g. "728x90") and a name (e.g. "game-below-player").
   - Paste ad code under `bySize` to fill EVERY spot of that size across the whole site.
   - Paste ad code under `bySlot` to fill ONE specific spot (this wins over bySize).
   - Leave a value as '' to keep showing the grey "Advertisement" placeholder.
   - Set `hidePlaceholders: true` before going live so empty spots disappear instead.

   For Google AdSense: put the adsbygoogle.js link (with your ca-pub ID) in `networkScript`,
   set `adsense: true`, and paste each <ins class="adsbygoogle" ...></ins> unit below.
   Note: <script> tags pasted inside ad code will not run; load SDKs via networkScript.

   Sizes used on the site:
     970x250 billboard   970x90 large leaderboard   728x90 leaderboard
     300x250 rectangle   300x600 half page
     160x600 skyscraper  320x100 / 320x50 mobile banners
   Slot names are listed in README.md.
   ===================================================================================== */
window.ARCADE_ADS = {
  networkScript: '',        // e.g. 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX'
  adsense: false,
  hidePlaceholders: false,
  bySize: {
    '970x250': '',
    '970x90': '',
    '728x90': '',
    '300x250': '',
    '300x600': '',
    '160x600': '',
    '320x100': '',
    '320x50': ''
  },
  bySlot: {
    // 'game-below-player': '<ins class="adsbygoogle" ...></ins>',
  }
};

(() => {
  const cfg = window.ARCADE_ADS;
  if (cfg.networkScript) {
    const s = document.createElement('script');
    s.async = true; s.crossOrigin = 'anonymous'; s.src = cfg.networkScript;
    document.head.append(s);
  }
  const fill = () => document.querySelectorAll('.ad[data-slot]').forEach(slot => {
    if (slot.dataset.done) return;
    if (getComputedStyle(slot).display === 'none') return;   // e.g. a desktop-only spot on a phone
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
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fill); else fill();
})();
