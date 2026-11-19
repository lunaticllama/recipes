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

  // "all" holds the title and every ingredient, so a search like "lamb tomato"
  // can match one word in the title and another in the ingredients.
  recipes.forEach(function (r) { r.all = r.title + " " + r.ingredients.join(" "); });

  var fuse = window.Fuse ? new window.Fuse(recipes, {
    keys: [{ name: "title", weight: 2 }, { name: "all", weight: 1 }],
    threshold: 0.25,
    ignoreLocation: true,
    minMatchCharLength: 2,
    useExtendedSearch: true   // each word must match (fuzzily) somewhere
  }) : null;

  function search(query) {
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
})();
