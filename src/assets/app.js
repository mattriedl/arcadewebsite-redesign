/* ArcadeWebsite — page behaviour. No dependencies. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------- Featured stage ----------
     The build writes the whole rotation order to /assets/featured.json. Which games show is worked out
     here from today's date, so the lineup changes every few days without rebuilding the site. */
  const stage = $(".stage");
  if (stage) {
    const lineup = $(".lineup ol");
    const dots = $(".stage-dots");
    const pauseBtn = $(".stage-pause");
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let slides = JSON.parse($("#stage-initial").textContent);
    let seconds = Number(stage.dataset.seconds) || 7;
    let current = 0, timer = null, paused = reduce, hovering = false;

    const card = (g, i) => `<li><button type="button" class="c-${esc(g.category)}" data-i="${i}">
        <img src="${esc(g.thumbnail)}" alt="" width="72" height="48" loading="lazy">
        <span><strong>${esc(g.title)}</strong><small>${esc(g.categoryName)}</small></span></button></li>`;

    function render() {
      lineup.innerHTML = slides.map(card).join("");
      dots.innerHTML = slides.map((g, i) => `<button type="button" data-i="${i}" aria-label="Featured game ${i + 1} of ${slides.length}: ${esc(g.title)}"></button>`).join("");
      $$("button[data-i]", stage.parentElement).forEach(b => b.addEventListener("click", () => { show(Number(b.dataset.i)); restart(); }));
    }
    function show(i) {
      current = (i + slides.length) % slides.length;
      const g = slides[current];
      stage.className = "stage c-" + g.category + (paused ? " paused" : "");
      $(".stage-backdrop", stage).style.backgroundImage = `url("${g.thumbnail}")`;
      const img = $(".stage-art img", stage); img.src = g.thumbnail; img.alt = g.title;
      $$(".stage-link", stage).forEach(a => a.href = g.url);
      $("[data-f=title]", stage).textContent = g.title;
      $("[data-f=desc]", stage).textContent = g.description;
      const chip = $("[data-f=chip]", stage); chip.href = "/category/" + g.category + "/"; chip.className = "chip c-" + g.category;
      $("[data-f=chipname]", stage).textContent = g.categoryName;
      $("[data-f=chipicon]", stage).innerHTML = (window.ARCADE_ICONS || {})[g.category] || "";
      markCurrent();
    }
    // Re-applying aria-current after a reflow restarts the progress bar on the current dot
    function markCurrent() {
      const btns = $$("button[data-i]", stage.parentElement);
      btns.forEach(b => b.setAttribute("aria-current", "false"));
      void dots.offsetWidth;
      btns.forEach(b => b.setAttribute("aria-current", String(Number(b.dataset.i) === current)));
    }
    function restart() {
      clearInterval(timer);
      if (!paused && !hovering) { markCurrent(); timer = setInterval(() => show(current + 1), seconds * 1000); }
    }
    function setPaused(p) {
      paused = p;
      stage.classList.toggle("paused", p);
      pauseBtn.setAttribute("aria-label", p ? "Play featured games slideshow" : "Pause featured games slideshow");
      pauseBtn.innerHTML = p ? '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4l13 8-13 8z"/></svg>' : '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>';
      restart();
    }
    pauseBtn.addEventListener("click", () => setPaused(!paused));
    const wrap = stage.parentElement;
    wrap.addEventListener("mouseenter", () => { hovering = true; stage.classList.add("paused"); clearInterval(timer); });
    wrap.addEventListener("mouseleave", () => { hovering = false; if (!paused) stage.classList.remove("paused"); restart(); });
    wrap.addEventListener("focusin", () => { hovering = true; clearInterval(timer); });
    wrap.addEventListener("focusout", () => { hovering = false; restart(); });
    stage.style.setProperty("--slide", seconds + "s");

    render(); show(0); setPaused(paused);

    // Pick today's set from the full rotation
    fetch("/assets/featured.json").then(r => r.ok ? r.json() : Promise.reject()).then(f => {
      const start = new Date(f.startDate + "T00:00:00");
      const today = new Date(); today.setHours(0, 0, 0, 0);
      const days = Math.max(0, Math.floor((today - start) / 86400000));
      const period = Math.floor(days / f.daysPerRotation);
      const toGame = ([slug, title, thumbnail, category]) => ({
        url: "/game/" + slug + "/", title, thumbnail, category, categoryName: f.categories[category],
        description: `Play ${title} free online in the ${f.categories[category]} collection.`
      });
      const n = f.gamesPerRotation, pool = f.rotation.map(toGame);
      f.pinned = f.pinned.map(toGame);
      const picks = [];
      for (const g of f.pinned) if (picks.length < n) picks.push(g);
      for (let k = 0; picks.length < n && k < pool.length; k++) {
        const g = pool[(period * (n - f.pinned.length) + k) % pool.length];
        if (!picks.some(p => p.url === g.url)) picks.push(g);
      }
      seconds = f.secondsPerSlide || seconds;
      stage.style.setProperty("--slide", seconds + "s");
      if (picks.map(p => p.url).join() !== slides.map(p => p.url).join()) { slides = picks; render(); show(0); }
      restart();
    }).catch(() => {});
  }

  /* ---------- Shelf arrows ---------- */
  $$("[data-shelf]").forEach(b => b.addEventListener("click", () => {
    const row = document.getElementById(b.dataset.shelf);
    row.scrollBy({ left: row.clientWidth * 0.85 * Number(b.dataset.dir), behavior: "smooth" });
  }));

  /* ---------- Game player ---------- */
  const player = $(".player");
  if (player) {
    const frame = $("iframe", player);
    const start = $(".player-start", player);
    const status = $(".share-status");
    const load = () => { if (!frame.src) frame.src = frame.dataset.src; start.hidden = true; frame.focus(); };
    start.addEventListener("click", load);
    $("[data-reload]")?.addEventListener("click", () => { frame.src = frame.dataset.src; start.hidden = true; });
    $("[data-fullscreen]")?.addEventListener("click", async () => {
      load();
      try { document.fullscreenElement ? await document.exitFullscreen() : await player.requestFullscreen(); }
      catch { if (status) status.textContent = "Fullscreen isn't available in this browser."; }
    });
    $("[data-copy]")?.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(location.href); status.textContent = "Link copied."; }
      catch { status.textContent = "Copy the address from your browser bar to share."; }
    });
  }

  /* ---------- Filter a grid on the page (categories, all games) ---------- */
  $$("[data-filter]").forEach(input => {
    const grid = document.getElementById(input.dataset.filter);
    const out = input.parentElement.querySelector("output");
    const cards = $$(".card", grid);
    const extras = $$(".ad-tile, .letter-head", grid.parentElement);
    const total = cards.length;
    input.addEventListener("input", () => {
      const terms = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
      let shown = 0;
      cards.forEach(c => { const hit = terms.every(t => c.dataset.name.includes(t)); c.hidden = !hit; shown += hit; });
      extras.forEach(e => e.hidden = terms.length > 0);
      out.textContent = terms.length ? `${shown} of ${total} games` : `${total} games`;
    });
  });

  /* ---------- Search page ---------- */
  const results = $("#search-results");
  if (results) {
    const q = new URLSearchParams(location.search).get("q") || "";
    const input = $(".search input"); if (input) input.value = q;
    const heading = $("#search-heading"), count = $("#search-count");
    heading.textContent = q ? `Results for “${q}”` : "Search games";
    fetch("/assets/search-index.json").then(r => r.ok ? r.json() : Promise.reject()).then(games => {
      const terms = q.toLowerCase().trim().split(/\s+/).filter(Boolean);
      const hits = terms.length ? games.filter(g => terms.every(t => (g.title + " " + g.categoryName).toLowerCase().includes(t))) : [];
      count.textContent = !terms.length ? "Type a game name or category in the search box." : hits.length ? `${hits.length} game${hits.length === 1 ? "" : "s"} found` : "";
      if (terms.length && !hits.length) {
        results.outerHTML = `<div class="empty">No games match “${esc(q)}”. Check the spelling, or <a href="/all-games/">browse all games</a>.</div>`;
        return;
      }
      results.innerHTML = hits.map(g => `<a class="card c-${esc(g.category)}" href="${esc(g.url)}">
          <span class="thumb"><img src="${esc(g.image)}" alt="" loading="lazy" width="480" height="320"></span>
          <span class="name">${esc(g.title)}</span><span class="cat">${esc(g.categoryName)}</span></a>`).join("");
    }).catch(() => { count.textContent = "Search couldn't load. Browse all games instead."; });
  }
})();
