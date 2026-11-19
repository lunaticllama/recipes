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
    if (matches === null) {
      results.hidden = true;
      if (azPage) azPage.hidden = false;
      return;
    }
    showResults(matches);
    results.hidden = false;
    if (azPage) azPage.hidden = true;
  }

  if (input && results) {
    input.addEventListener("input", onInput);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && lastMatches.length) {
        window.location.href = href(lastMatches[0].slug);
      }
    });
    if (input.value) onInput();  // e.g. text restored by the browser's back button
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
