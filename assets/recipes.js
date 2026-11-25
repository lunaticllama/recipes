/* Phil's Recipes: search and the A–Z index.
   Needs window.RECIPES (assets/search-index.js) and, for fuzzy matching,
   window.Fuse (assets/fuse.min.js). */
(function () {
  "use strict";

  var body = document.body;
  var root = body.getAttribute("data-root") || "";
  var current = body.getAttribute("data-current") || "";
  var recipes = window.RECIPES || [];

  // ---------- search ----------

  // "all" holds the title, every ingredient and the tags, so a search like
  // "lamb tomato" can match one word in the title and another in the ingredients.
  recipes.forEach(function (r) {
    r.tags = r.tags || [];
    r.all = r.title + " " + r.ingredients.join(" ") + " " + r.tags.join(" ");
  });

  var fuse = window.Fuse ? new window.Fuse(recipes, {
    keys: [{ name: "title", weight: 2 }, { name: "tags", weight: 1.5 }, { name: "all", weight: 1 }],
    threshold: 0.25,
    ignoreLocation: true,
    minMatchCharLength: 2,
    useExtendedSearch: true   // each word must match (fuzzily) somewhere
  }) : null;

  // "#greek" searches tags only: each #term must start one of the recipe's tags
  // (any case), so "#gr" already finds Greek and "#holidays #christmas" needs both.
  function searchTags(query) {
    var terms = query.toLowerCase().split("#").map(function (t) {
      return t.replace(/\s+/g, " ").trim();
    }).filter(Boolean);
    if (!terms.length) return null;
    return recipes.filter(function (r) {
      var tags = r.tags.map(function (t) { return t.toLowerCase(); });
      return terms.every(function (term) {
        return tags.some(function (t) { return t.indexOf(term) === 0; });
      });
    }).sort(function (a, b) { return a.title.localeCompare(b.title); });
  }

  function search(query) {
    if (query.trim().charAt(0) === "#") return searchTags(query);
    // Drop extended-search operator characters so typed text is always a plain fuzzy search.
    var q = query.replace(/[=!^$'|"]/g, " ").replace(/\s+/g, " ").trim();
    if (q.length < 2) return null;
    if (fuse) return fuse.search(q, { limit: 50 }).map(function (r) { return r.item; });
    var words = q.toLowerCase().split(" ");
    return recipes.filter(function (r) {
      var text = r.all.toLowerCase();
      return words.every(function (w) { return text.indexOf(w) !== -1; });
    });
  }

  function href(slug) { return root + "recipes/" + slug + ".html"; }

  var input = document.getElementById("search");
  var results = document.querySelector(".results");
  var azPage = document.querySelector(".az-page");
  var pickSection = document.querySelector(".pick");
  var lastMatches = [];

  function showResults(matches) {
    var count = results.querySelector(".results-count");
    var list = results.querySelector(".results-list");
    list.textContent = "";
    count.textContent = matches.length === 0 ? "No matches"
      : matches.length + (matches.length === 1 ? " match" : " matches");
    matches.forEach(function (r) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = href(r.slug);
      a.textContent = r.title;
      if (r.slug === current) {
        a.className = "is-current";
        a.setAttribute("aria-current", "page");
      }
      li.appendChild(a);
      list.appendChild(li);
    });
  }

  function onInput() {
    var matches = search(input.value);
    lastMatches = matches || [];
    var searching = matches !== null;
    if (searching) showResults(matches);
    results.hidden = !searching;
    if (azPage) azPage.hidden = searching;
    // The "Can't decide?" cards step aside while a search is showing.
    if (pickSection && recipes.length) pickSection.hidden = searching;
  }

  if (input && results) {
    input.addEventListener("input", onInput);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && lastMatches.length) {
        window.location.href = href(lastMatches[0].slug);
      }
    });
    // A tag link on a recipe page opens "index.html?q=#Greek": start with that search.
    var fromQuery = new URLSearchParams(window.location.search).get("q");
    if (fromQuery && !input.value) input.value = fromQuery;
    if (input.value) onInput();  // also text restored by the browser's back button
  }

  // ---------- A–Z ----------

  var buttons = Array.prototype.slice.call(document.querySelectorAll(".az-letter"));
  var lists = Array.prototype.slice.call(document.querySelectorAll(".az-list"));
  var hint = document.querySelector(".az-hint");

  function pick(letter) {
    var found = false;
    lists.forEach(function (el) {
      var on = el.id === "letter-" + letter;
      el.hidden = !on;
      found = found || on;
    });
    buttons.forEach(function (b) {
      if (!b.disabled) b.setAttribute("aria-pressed", String(b.getAttribute("data-letter") === letter));
    });
    if (hint) hint.hidden = found;
    if (found && window.history.replaceState) {
      // Remember the letter so Back from a recipe returns to the same list.
      window.history.replaceState(null, "", "#" + encodeURIComponent(letter));
    }
  }

  if (buttons.length) {
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { pick(b.getAttribute("data-letter")); });
    });
    var fromHash = decodeURIComponent(window.location.hash.slice(1));
    pick(fromHash);
  }

  // ---------- "Can't decide?" cards and "Surprise me" (home page) ----------

  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function shuffled(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  var hand = document.querySelector(".hand");
  var shuffleBtn = document.getElementById("shuffle");
  var dealt = [];

  function makeCard(r, k) {
    var li = document.createElement("li");
    li.className = "card";
    // A slight random tilt, -3° to 3°, so the hand looks dealt by hand.
    li.style.setProperty("--tilt", (Math.random() * 6 - 3).toFixed(1) + "deg");
    li.style.setProperty("--delay", k * 110 + "ms");
    var a = document.createElement("a");
    a.href = href(r.slug);
    var h = document.createElement("h3");
    h.className = "card-title";
    h.textContent = r.title;
    var p = document.createElement("p");
    p.className = "card-ing";
    p.textContent = (r.key || []).join(" · ");
    var go = document.createElement("span");
    go.className = "card-go";
    go.textContent = "Open recipe →";
    a.appendChild(h); a.appendChild(p); a.appendChild(go);
    li.appendChild(a);
    return li;
  }

  function deal(animate) {
    // Never deal a card that was in the last hand, when there are enough recipes.
    var last = dealt.map(function (r) { return r.slug; });
    var pool = recipes.filter(function (r) { return last.indexOf(r.slug) === -1; });
    if (pool.length < 3) pool = recipes;
    dealt = shuffled(pool).slice(0, 3);
    hand.textContent = "";
    dealt.forEach(function (r, k) {
      var card = makeCard(r, k);
      if (animate && !reducedMotion) card.classList.add("deal-in");
      hand.appendChild(card);
    });
  }

  if (hand && pickSection && recipes.length) {
    if (!(input && input.value)) pickSection.hidden = false;
    deal(true);
    shuffleBtn.addEventListener("click", function () {
      if (reducedMotion) { deal(false); return; }
      shuffleBtn.disabled = true;
      Array.prototype.forEach.call(hand.children, function (c, k) {
        c.style.setProperty("--delay", k * 70 + "ms");
        c.classList.remove("deal-in");
        c.classList.add("deal-out");
      });
      setTimeout(function () {
        deal(true);
        setTimeout(function () { shuffleBtn.disabled = false; }, 700);
      }, 480);
    });
  }

  var surprise = document.getElementById("surprise");
  var ticker = document.querySelector(".ticker");

  function resetSurprise() {
    surprise.disabled = false;
    surprise.classList.remove("is-rolling");
    ticker.hidden = true;
    ticker.textContent = "";
  }

  if (surprise && ticker && recipes.length) {
    surprise.hidden = false;
    surprise.addEventListener("click", function () {
      var chosen = recipes[Math.floor(Math.random() * recipes.length)];
      if (reducedMotion) { window.location.href = href(chosen.slug); return; }
      surprise.disabled = true;
      surprise.classList.add("is-rolling");
      ticker.textContent = "";
      ticker.className = "ticker is-spinning";
      var label = document.createElement("span");
      label.className = "ticker-label";
      label.textContent = "Rolling";
      var name = document.createElement("span");
      name.className = "ticker-name";
      ticker.appendChild(label);
      ticker.appendChild(name);
      ticker.hidden = false;
      // Each delay is longer than the last, so the names slow down before landing (about 1.3 s).
      var delays = [60, 60, 65, 70, 80, 90, 105, 125, 150, 185, 230];
      var i = 0;
      (function step() {
        if (i < delays.length) {
          name.textContent = recipes[Math.floor(Math.random() * recipes.length)].title;
          setTimeout(step, delays[i++]);
          return;
        }
        name.textContent = chosen.title;
        label.textContent = "Tonight";
        ticker.className = "ticker is-landed";
        setTimeout(function () { window.location.href = href(chosen.slug); }, 700);
      })();
    });
    // Coming Back from the recipe can restore this page mid-roll; start it fresh.
    window.addEventListener("pageshow", function (e) { if (e.persisted) resetSurprise(); });
  }

  // ---------- recipe page buttons ----------

  var printBtn = document.querySelector('[data-action="print"]');
  if (printBtn) printBtn.addEventListener("click", function () { window.print(); });

  // "Keep screen on" uses the Screen Wake Lock API (needs https). Browsers
  // without it never see the button.
  var wakeBtn = document.querySelector('[data-action="wake"]');
  if (wakeBtn && "wakeLock" in navigator) {
    var lock = null;
    var wanted = false;

    var setPressed = function (on) { wakeBtn.setAttribute("aria-pressed", String(on)); };

    var acquire = function () {
      return navigator.wakeLock.request("screen").then(function (l) {
        lock = l;
        setPressed(true);
        // The browser drops the lock when the tab is hidden; show that honestly.
        l.addEventListener("release", function () { lock = null; if (!wanted) setPressed(false); });
      }).catch(function () { wanted = false; setPressed(false); });
    };

    wakeBtn.hidden = false;
    wakeBtn.addEventListener("click", function () {
      wanted = !wanted;
      if (wanted) {
        acquire();
      } else {
        setPressed(false);
        if (lock) lock.release();
      }
    });
    document.addEventListener("visibilitychange", function () {
      if (wanted && !lock && document.visibilityState === "visible") acquire();
    });
  }
})();
