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
     728x90  leaderboard        300x250 medium-rectangle   300x600 half-page
     160x600 skyscraper         320x50  mobile-banner
   Slot names are listed in README.md.
   ===================================================================================== */
const spot = name => `<div data-gb-spot="${name}"></div>`;

window.ARCADE_ADS = {
  networkScript: 'https://bannerpromote.com/embed.js.php',
  adsense: false,          // set true only for Google AdSense
  hidePlaceholders: false,
  bySize: {
    '728x90':  spot('leaderboard'),
    '300x250': spot('medium-rectangle'),
    '300x600': spot('half-page'),
    '160x600': spot('skyscraper'),
    '320x50':  spot('mobile-banner')
  },
  bySlot: {
    // Example: show a different banner in one spot
    // 'game-beside-about': spot('large-rectangle'),
  }
};

(() => {
  const cfg = window.ARCADE_ADS;
  const fill = () => {
    document.querySelectorAll('.ad[data-slot]').forEach(slot => {
      if (slot.dataset.done) return;
      if (!slot.getClientRects().length) return;   // not shown at this screen size (it or a parent is hidden)
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
    // Load the network script after the spots exist, so it finds all of them
    if (cfg.networkScript && !document.querySelector('script[data-ad-network]')) {
      const s = document.createElement('script');
      s.async = true; s.src = cfg.networkScript; s.dataset.adNetwork = '1';
      if (cfg.adsense) s.crossOrigin = 'anonymous';
      document.head.append(s);
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fill); else fill();
})();
