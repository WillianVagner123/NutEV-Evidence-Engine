/*
 * NutEV Open Evidence Explorer — user interface.
 *
 * Read-only, login-free and static. Network access lives only in sources.js;
 * classification lives only in core.js. Everything rendered from external data
 * goes through textContent (never innerHTML) and links are limited to http(s).
 */
(function () {
  "use strict";

  var DATA = window.NUTEV_OPEN_DATA;
  var BUILD = window.NUTEV_OPEN_BUILD || { commit: "local" };
  var Core = window.NutEVOpenCore;
  var Sources = window.NutEVOpenSources;
  var Planner = window.NutEVOpenPlanner;
  var I18n = window.NutEVOpenI18n;
  var t = I18n.t;

  var PAGE_SIZE = 30;
  var MAX_FILE_ROWS = 20000;
  var LEVELS = ["A", "B", "Q"];
  var GROUPS = {};
  var FAMILIES = {};
  DATA.taxonomy.groups.forEach(function (group) { GROUPS[group.id] = group; });
  DATA.taxonomy.families.forEach(function (family) { FAMILIES[family.id] = family; });
  var SOURCE_LABELS = { bvs_lilacs: "BVS / LILACS", scielo: "SciELO" };
  Sources.SOURCES.forEach(function (source) { SOURCE_LABELS[source.id] = source.label; });
  var TAXONOMY_TERMS = Planner.taxonomyTermsFromBundle(DATA);
  var VOCABULARY = DATA.query_vocabulary;
  var STRATEGY_PROVIDERS = ["pubmed", "europepmc", "openalex", "crossref", "bvs_lilacs", "scielo"];
  var BASE_TITLE = document.title;
  var EXPLORER_PRODUCT = "NutEV Open Evidence Explorer";
  var MAX_TERM_LENGTH = 80;
  var MAX_LINK_STRING = 4000;

  var state = {
    query: "",
    sources: new Set(Sources.SOURCES.filter(function (s) { return s.defaultOn; }).map(function (s) { return s.id; })),
    limit: 50,
    origin: null,
    fileName: "",
    statuses: [],
    result: null,
    finishedAt: "",
    sort: "priority",
    shown: PAGE_SIZE,
    tab: "results",
    token: 0,
    plan: null,
    compiled: null,
    fieldMode: "title_abstract",
    includePt: false,
    overrides: {},
    literal: false,
    fileManifest: null,
    executed: null,
    filters: emptyFilters()
  };

  function emptyFilters() {
    return {
      levels: new Set(),
      groups: new Set(),
      unclassified: false,
      docClasses: new Set(),
      sources: new Set(),
      yearFrom: null,
      yearTo: null,
      abstractOnly: false
    };
  }

  // ------------------------------------------------------------------ DOM helpers

  function $(id) { return document.getElementById(id); }

  function el(tag, attrs) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        var value = attrs[key];
        if (value === null || value === undefined || value === false) return;
        if (key === "class") node.className = value;
        else if (key === "text") node.textContent = value;
        else if (key === "href") {
          var safe = safeHref(value);
          if (safe) node.setAttribute("href", safe);
        } else if (key.slice(0, 2) === "on" && typeof value === "function") node.addEventListener(key.slice(2), value);
        else node.setAttribute(key, value === true ? "" : String(value));
      });
    }
    for (var i = 2; i < arguments.length; i += 1) append(node, arguments[i]);
    return node;
  }

  function append(node, child) {
    if (child === null || child === undefined || child === false) return;
    if (Array.isArray(child)) { child.forEach(function (item) { append(node, item); }); return; }
    node.appendChild(typeof child === "string" || typeof child === "number" ? document.createTextNode(String(child)) : child);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
  }

  function safeHref(value) {
    var text = String(value || "").trim();
    return /^https?:\/\/[^\s]+$/i.test(text) ? text : null;
  }

  function externalLink(href, text, cls) {
    var safe = safeHref(href);
    if (!safe) return el("span", { class: cls, text: text });
    return el("a", { href: safe, class: cls, target: "_blank", rel: "noopener noreferrer", text: text });
  }

  function pct(part, whole) {
    return whole ? Math.round((part / whole) * 100) : 0;
  }

  function fmtNumber(value) {
    return Number(value || 0).toLocaleString(I18n.lang() === "pt" ? "pt-BR" : "en");
  }

  function fmtTime(iso) {
    if (!iso) return "—";
    var date = new Date(iso);
    if (isNaN(date.getTime())) return String(iso);
    return date.toLocaleString(I18n.lang() === "pt" ? "pt-BR" : "en", { dateStyle: "short", timeStyle: "short" });
  }

  function groupLabel(id) {
    var group = GROUPS[id];
    if (!group) return id;
    return I18n.lang() === "pt" ? group.label_pt : group.label_en;
  }

  function familyLabel(family, short) {
    if (!family) return t("family.unclassified");
    var suffix = I18n.lang() === "pt" ? "_pt" : "_en";
    return family[(short ? "short" : "label") + suffix];
  }

  function familyOf(groupId) {
    var group = GROUPS[groupId];
    return group ? FAMILIES[group.family] : null;
  }

  function docClassLabel(id) {
    var labels = I18n.lang() === "pt" ? DATA.document_classes.labels_pt : DATA.document_classes.labels_en;
    return labels[id] || id;
  }

  function sourceLabel(id) {
    return SOURCE_LABELS[id] || id;
  }

  function levelOf(row) {
    return Core.traceabilityLevel(row.audit_traceability);
  }

  function levelBadge(level) {
    return el("span", { class: "level-badge level-" + level },
      el("span", { class: "level-letter", "aria-hidden": "true", text: level }),
      t("level." + level + ".name"));
  }

  function reasonsText(reasons) {
    return (reasons || []).map(function (reason) { return t("reason." + reason); }).join("; ");
  }

  function works() {
    return state.result ? state.result.ranked.concat(state.result.quarantined) : [];
  }

  function abstractPresent(row) {
    return Boolean(row.metadata_completeness && row.metadata_completeness.fields.abstract);
  }

  // ------------------------------------------------------------------ tooltip

  var tooltip = null;

  function bindTooltip() {
    tooltip = $("tooltip");
    document.addEventListener("mouseover", function (event) {
      var target = event.target.closest ? event.target.closest("[data-tip]") : null;
      if (!target) { tooltip.hidden = true; return; }
      tooltip.textContent = target.getAttribute("data-tip");
      tooltip.hidden = false;
    });
    document.addEventListener("mousemove", function (event) {
      if (tooltip.hidden) return;
      var width = document.documentElement.clientWidth || window.innerWidth;
      var height = document.documentElement.clientHeight || window.innerHeight;
      var x = event.clientX + 14;
      if (x + tooltip.offsetWidth > width - 8) x = event.clientX - tooltip.offsetWidth - 14;
      var y = event.clientY + 16;
      if (y + tooltip.offsetHeight > height - 8) y = event.clientY - tooltip.offsetHeight - 12;
      tooltip.style.left = Math.max(8, x) + "px";
      tooltip.style.top = Math.max(8, y) + "px";
    });
    document.addEventListener("scroll", function () { tooltip.hidden = true; }, { passive: true });
  }

  // ------------------------------------------------------------------ A/B/Q bar

  function abqBar(counts, options) {
    var total = LEVELS.reduce(function (sum, level) { return sum + (counts[level] || 0); }, 0);
    var bar = el("div", {
      class: "abq-bar" + (options && options.tall ? " tall" : ""),
      role: "img",
      "aria-label": LEVELS.map(function (level) { return level + " " + (counts[level] || 0); }).join(", ")
    });
    if (options && typeof options.widthPct === "number") bar.style.width = Math.max(1, options.widthPct) + "%";
    LEVELS.forEach(function (level) {
      var count = counts[level] || 0;
      if (!count) return;
      var segment = el("span", {
        class: "abq-seg " + level,
        "data-tip": t("level." + level + ".name") + ": " + fmtNumber(count) + " (" + pct(count, total) + "%)"
      });
      segment.style.flexGrow = String(count);
      segment.style.flexBasis = "0";
      bar.appendChild(segment);
    });
    return bar;
  }

  function abqValues(counts) {
    return LEVELS.map(function (level) { return level + " " + fmtNumber(counts[level] || 0); }).join(" · ");
  }

  function abqLegend() {
    return el("div", { class: "abq-legend" }, LEVELS.map(function (level) {
      return el("span", null, el("i", { class: "abq-key " + level, "aria-hidden": "true" }), t("level." + level + ".name"));
    }));
  }

  // ------------------------------------------------------------------ static sections

  function levelCards(container, compact) {
    clear(container);
    LEVELS.forEach(function (level) {
      var code = level === "Q" ? t("level.Q.codes") : t("level." + level + ".code");
      container.appendChild(el("article", { class: "level-card level-" + level },
        el("h4", null, levelBadge(level)),
        el("p", { text: t("level." + level + ".short") }),
        compact ? null : el("code", { text: code })));
    });
  }

  function renderSourcePicker() {
    var picker = clear($("source-picker"));
    Sources.SOURCES.forEach(function (source) {
      var input = el("input", { type: "checkbox", value: source.id, checked: state.sources.has(source.id) });
      input.checked = state.sources.has(source.id);
      input.addEventListener("change", function () {
        if (input.checked) state.sources.add(source.id); else state.sources.delete(source.id);
      });
      picker.appendChild(el("label", { class: "chip-toggle" }, input, el("span", { text: source.label })));
    });
  }

  function renderExamples() {
    var box = clear($("examples"));
    var english = I18n.lang() === "en" && (DATA.example_queries_en || []).length;
    (english ? DATA.example_queries_en : DATA.example_queries).slice(0, 3).forEach(function (query) {
      box.appendChild(el("button", {
        type: "button",
        class: "chip-button",
        text: query,
        onclick: function () { $("q").value = query; runSearch(query); }
      }));
    });
  }

  function reviewStatusLabel(status) {
    var key = "vocab.status." + status;
    var label = t(key);
    return label === key ? String(status) : label;
  }

  function renderGuide() {
    $("guide-q0-lead").textContent = t("guide.q0.lead", { version: VOCABULARY.vocabulary_version, n: VOCABULARY.concepts.length });
    $("guide-q1-lead").textContent = t("guide.q1.lead", { policy: DATA.guardrail_policy_version });
    $("guide-q3-lead").textContent = t("guide.q3.lead", {
      version: DATA.taxonomy_version,
      groups: DATA.taxonomy.canonical_groups_loaded,
      terms: fmtNumber(DATA.taxonomy.canonical_terms_total)
    });
    levelCards($("guide-levels"), false);
    levelCards($("empty-levels"), true);

    var fields = clear($("guide-fields"));
    Core.COMPLETENESS_FIELDS.forEach(function (field) { fields.appendChild(el("li", { text: t("field." + field) })); });

    var axes = clear($("guide-axes"));
    DATA.taxonomy.families.forEach(function (family) {
      var groups = DATA.taxonomy.groups.filter(function (group) { return group.family === family.id; });
      axes.appendChild(el("section", { class: "guide-family" },
        el("h4", null, el("span", { class: "family-tag", text: familyLabel(family, true) }), familyLabel(family, false)),
        groups.map(function (group) {
          return el("details", null,
            el("summary", null, el("span", { text: groupLabel(group.id) }), el("small", { text: t("guide.axes.terms", { n: group.terms.length }) })),
            el("p", { class: "terms", text: group.terms.join(" · ") }));
        })));
    });

    clear($("guide-provenance"));
    $("footer-meta").textContent = t("footer.meta");
  }

  // ------------------------------------------------------------------ tabs

  function selectTab(name, focus) {
    state.tab = name;
    document.querySelectorAll(".tabs [role=tab]").forEach(function (tab) {
      var selected = tab.getAttribute("data-tab") === name;
      tab.setAttribute("aria-selected", selected ? "true" : "false");
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focus) tab.focus();
    });
    document.querySelectorAll(".panel").forEach(function (panel) {
      panel.hidden = panel.id !== "panel-" + name;
    });
  }

  function bindTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".tabs [role=tab]"));
    tabs.forEach(function (tab, index) {
      tab.addEventListener("click", function () { selectTab(tab.getAttribute("data-tab")); });
      tab.addEventListener("keydown", function (event) {
        var next = null;
        if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
        if (event.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
        if (next) { event.preventDefault(); selectTab(next.getAttribute("data-tab"), true); }
      });
    });
    document.querySelectorAll("[data-goto]").forEach(function (button) {
      button.addEventListener("click", function () { selectTab(button.getAttribute("data-goto"), true); });
    });
  }

  // ------------------------------------------------------------------ status

  function statusDetail(status) {
    if (status.status === "pending") return t("status.pending");
    if (status.status === "ok") {
      var seconds = ((status.elapsed_ms || 0) / 1000).toLocaleString(I18n.lang() === "pt" ? "pt-BR" : "en", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
      var parts = [t("status.ok", { n: fmtNumber(status.returned), s: seconds })];
      if (typeof status.total_found === "number") parts.push(t("status.total", { total: fmtNumber(status.total_found) }));
      (status.notes || []).forEach(function (note) { parts.push(t("status.note." + note)); });
      return parts.join(" · ");
    }
    var kind = status.error_kind || "network_error";
    return t("status.error") + ": " + t("status.error." + kind, { code: status.http_status || "?" });
  }

  // A reopened JSON export holds the unique works only; say what the original
  // search retrieved so its counts are not mistaken for the file's.
  function originalSearchNote() {
    var original = state.origin === "file" && state.fileManifest;
    var counts = original && original.counts;
    if (!counts || typeof counts.retrieved_rows !== "number") return "";
    return " " + t("file.originalSearch", {
      query: original.query || "—",
      retrieved: fmtNumber(counts.retrieved_rows),
      duplicates: fmtNumber(counts.duplicates_merged || 0)
    });
  }

  function renderStatus() {
    var panel = $("status");
    var list = clear($("status-list"));
    if (!state.statuses.length) { panel.hidden = true; return; }
    panel.hidden = false;
    state.statuses.forEach(function (status) {
      var label = status.source === "file" ? t("status.file") : sourceLabel(status.source);
      if (status.source === "file") {
        list.appendChild(el("li", { class: "status-item", "data-state": "ok" },
          el("strong", { text: label }), el("span", { class: "detail", text: fmtNumber(status.returned) })));
      } else if (status.status === "ok") {
        var n = typeof status.total_found === "number" ? status.total_found : status.returned;
        list.appendChild(el("li", { class: "status-item", "data-state": "ok" },
          el("strong", { text: label }), el("span", { class: "detail", text: fmtNumber(n) })));
      } else if (status.status === "error") {
        var detail = statusDetail(status);
        list.appendChild(el("li", { class: "status-item", "data-state": "error", "data-tip": detail },
          el("strong", { text: "⚠ " + label }), el("span", { class: "detail", text: t("status.error") })));
      } else {
        list.appendChild(el("li", { class: "status-item", "data-state": status.status },
          el("strong", { text: label }), el("span", { class: "detail", text: t("status.pending") })));
      }
    });
    $("status-stale").hidden = !anyStale();
  }

  // ------------------------------------------------------------------ search

  function setSearching(active) {
    var button = $("search-btn");
    button.disabled = active;
    button.textContent = t(active ? "search.searching" : "search.button");
  }

  function currentYear() {
    return new Date().getFullYear();
  }

  function compilePlan() {
    state.compiled = Planner.compileQueries(state.plan, {
      fieldMode: state.fieldMode,
      includePt: state.includePt,
      currentYear: currentYear()
    });
    return state.compiled;
  }

  function queryFor(provider) {
    var compiled = state.compiled.providers[provider];
    var override = state.overrides[provider];
    var edited = typeof override === "string";
    return {
      query: edited ? override : compiled.query,
      params: compiled.params || {},
      edited: edited
    };
  }

  function freshPlan(question, literal) {
    return Planner.planQuestion(question, VOCABULARY, {
      currentYear: currentYear(),
      taxonomyGroups: TAXONOMY_TERMS,
      detectManual: !literal
    });
  }

  // options: { literal: interpret a Boolean-looking string as a question,
  //            strategy: edits restored from a shared link (see strategyDelta) }
  function runSearch(rawQuery, options) {
    var question = String(rawQuery || "").trim();
    if (!question) { $("q").focus(); return; }
    state.literal = Boolean(options && options.literal);
    state.plan = freshPlan(question, state.literal);
    state.overrides = {};
    if (options && options.strategy) applyStrategyDelta(state.plan, options.strategy);
    state.query = question;
    compilePlan();
    renderStrategy();
    executePlan({ fresh: true });
  }

  // options.fresh: a new question. If it has nothing to search, the previous
  // question's results are cleared instead of staying on screen under the new one.
  async function executePlan(options) {
    var ids = Sources.SOURCES.map(function (s) { return s.id; }).filter(function (id) { return state.sources.has(id); });
    if (!ids.length) { ids = Sources.SOURCES.map(function (s) { return s.id; }); ids.forEach(function (id) { state.sources.add(id); }); renderSourcePicker(); }
    var queries = {};
    ids.forEach(function (id) {
      var spec = queryFor(id);
      queries[id] = { query: spec.query, params: spec.params };
    });
    var runnable = ids.filter(function (id) { return String(queries[id].query || "").trim(); });
    if (!runnable.length) {
      if (options && options.fresh) {
        state.token += 1;
        state.origin = "search";
        state.fileName = "";
        state.result = null;
        state.statuses = [];
        state.executed = null;
        setSearching(false);
        document.title = BASE_TITLE;
        renderAll();
      } else {
        renderStrategy();
      }
      $("strategy").scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    var token = state.token + 1;
    state.token = token;
    state.origin = "search";
    state.fileName = "";
    state.limit = Number($("limit").value) || 50;
    var record = {};
    runnable.forEach(function (id) {
      var spec = queryFor(id);
      record[id] = { query: spec.query, params: spec.params };
      if (spec.edited) {
        record[id].edited_by_hand = true;
        record[id].generated_query = state.compiled.providers[id].query;
      }
    });
    state.executed = {
      queries: record,
      field_mode: state.fieldMode,
      include_pt: state.includePt,
      literal: state.literal,
      strategy: strategyDelta(),
      at: new Date().toISOString()
    };
    state.statuses = runnable.map(function (id) { return { source: id, status: "pending" }; });
    setSearching(true);
    renderStatus();
    updateHash();
    document.title = state.query + " · NutEV";

    var outcome = await Sources.searchSources(queries, runnable, state.limit, {
      DOMParser: window.DOMParser,
      onSource: function (status) {
        if (token !== state.token) return;
        state.statuses = state.statuses.map(function (item) { return item.source === status.source ? status : item; });
        renderStatus();
      }
    });
    if (token !== state.token) return;
    state.statuses = outcome.statuses;
    state.finishedAt = new Date().toISOString();
    loadRows(outcome.rows);
    setSearching(false);
    $("strategy").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ------------------------------------------------------------------ strategy panel

  function roleLabel(role) {
    var labels = I18n.lang() === "pt"
      ? { population: "Quem", intervention: "O quê", comparator: "Comparação", outcome: "Resultado", context: "Contexto", design: "Desenho", free: "Palavra digitada" }
      : { population: "Who", intervention: "What", comparator: "Comparison", outcome: "Outcome", context: "Context", design: "Design", free: "Typed word" };
    return labels[role] || role;
  }

  function blockLabel(block) {
    return I18n.lang() === "pt" ? block.label_pt : block.label_en;
  }

  function warningText(warning) {
    var block = (state.plan.blocks || []).find(function (b) { return b.key === warning.block; });
    return t("warn." + warning.code, { label: block ? blockLabel(block) : "", count: warning.count || "" });
  }

  function siteUrlFor(provider, query, params) {
    var enc = encodeURIComponent;
    if (!query) return "";
    if (provider === "pubmed") return "https://pubmed.ncbi.nlm.nih.gov/?term=" + enc(query);
    if (provider === "europepmc") return "https://europepmc.org/search?query=" + enc(query);
    if (provider === "openalex") return "https://api.openalex.org/works?search=" + enc(query) + (params && params.filter ? "&filter=" + enc(params.filter) : "");
    if (provider === "crossref") return "https://api.crossref.org/works?query.bibliographic=" + enc(query) + (params && params.filter ? "&filter=" + enc(params.filter) : "");
    if (provider === "bvs_lilacs") return "https://pesquisa.bvsalud.org/portal/?lang=pt&q=" + enc(query) + "&" + enc("filter[db_cluster][]") + "=LILACS";
    if (provider === "scielo") return "https://search.scielo.org/?lang=pt&q=" + enc(query);
    return "";
  }

  function copyText(text, button) {
    var done = function () {
      var original = button.textContent;
      button.textContent = t("strategy.copied");
      setTimeout(function () { button.textContent = original; }, 1500);
    };
    try {
      navigator.clipboard.writeText(text).then(done, function () { window.prompt("", text); });
    } catch (error) {
      window.prompt("", text);
    }
  }

  function refreshStrategy(focusKey) {
    compilePlan();
    renderStrategy(focusKey);
  }

  // The panel is rebuilt on every change. Controls carry a data-fk key so the
  // control in use keeps focus and stays where it was on screen.
  function captureStrategyView() {
    var view = { y: window.scrollY, key: null, top: 0 };
    var active = document.activeElement;
    if (active && active !== document.body && $("strategy-body").contains(active) && active.getAttribute("data-fk")) {
      view.key = active.getAttribute("data-fk");
      view.top = active.getBoundingClientRect().top;
      try {
        if (typeof active.selectionStart === "number") view.selection = [active.selectionStart, active.selectionEnd];
      } catch (error) { view.selection = null; }
    }
    return view;
  }

  function restoreStrategyView(view, focusKey) {
    var key = focusKey || view.key;
    var target = null;
    if (key) {
      $("strategy-body").querySelectorAll("[data-fk]").forEach(function (node) {
        if (!target && node.getAttribute("data-fk") === key) target = node;
      });
    }
    if (target) {
      target.focus({ preventScroll: true });
      if (view.key === key && view.selection) {
        try { target.setSelectionRange(view.selection[0], view.selection[1]); } catch (error) { /* not a text control */ }
      }
    }
    if (target && view.key === key) {
      // Same control: keep it at the same height on screen (document coordinates,
      // because the browser may have clamped the scroll while the panel was rebuilt).
      var docTop = target.getBoundingClientRect().top + window.scrollY;
      window.scrollTo(window.scrollX, Math.max(0, docTop - view.top));
    } else {
      window.scrollTo(window.scrollX, view.y);
    }
  }

  function blockCard(block) {
    var toggle = el("input", { type: "checkbox", "data-fk": "use:" + block.key, "aria-label": t("strategy.use") + ": " + blockLabel(block) });
    toggle.checked = Boolean(block.enabled);
    toggle.addEventListener("change", function () { block.enabled = toggle.checked; refreshStrategy(); });

    var chips = el("div", { class: "term-chips" }, block.terms.map(function (term, index) {
      var on = term.enabled !== false;
      var regionalOnly = term.lang === "pt" && !state.includePt;
      return el("button", {
        type: "button",
        "data-fk": "term:" + block.key + ":" + index,
        class: "term-chip" + (on ? "" : " off") + (regionalOnly ? " regional" : ""),
        "aria-pressed": on ? "true" : "false",
        "data-tip": (regionalOnly ? t("strategy.ptRegional") + " " : "") + t(on ? "strategy.termOff" : "strategy.termOn"),
        onclick: function () { term.enabled = on ? false : true; refreshStrategy(); }
      }, term.lang === "pt" ? el("small", { text: "PT" }) : term.lang === "en" ? el("small", { text: "EN" }) : null, term.text);
    }));

    var input = el("input", { type: "text", maxlength: String(MAX_TERM_LENGTH), "data-fk": "add:" + block.key, placeholder: t("strategy.addTerm"), "aria-label": t("strategy.addTerm") + ": " + blockLabel(block) });
    var addForm = el("form", { class: "add-term" }, input);
    addForm.addEventListener("submit", function (event) {
      event.preventDefault();
      var value = cleanTerm(input.value);
      if (!value) return;
      if (!block.terms.some(function (term) { return term.text === value; })) {
        block.terms.push({ text: value, lang: block.role === "free" ? "any" : "en", enabled: true, added: true });
      }
      refreshStrategy("add:" + block.key);
    });

    return el("article", { class: "block-card role-" + block.role + (block.enabled ? "" : " off") },
      el("header", null,
        el("div", { class: "block-title" },
          el("strong", { text: blockLabel(block) }),
          el("small", { text: roleLabel(block.role) })),
        el("label", { class: "switch" }, toggle, el("span", { class: "sr-only", text: blockLabel(block) }))),
      chips,
      addForm);
  }

  // True when the source was searched and its string or filters changed since:
  // the counts on screen then belong to the previous search.
  function isStale(provider) {
    if (state.origin !== "search" || !state.executed || !state.compiled) return false;
    var ran = state.executed.queries[provider];
    if (!ran) return false;
    var now = queryFor(provider);
    return ran.query !== now.query || JSON.stringify(ran.params || {}) !== JSON.stringify(now.params || {});
  }

  function anyStale() {
    return Planner.LIVE_PROVIDERS.some(isStale);
  }

  function badgeFor(provider) {
    var status = state.statuses.find(function (item) { return item.source === provider; });
    if (Planner.LIVE_PROVIDERS.indexOf(provider) < 0) return { cls: "link", text: t("strategy.linkOnly") };
    if (!status) return null;
    var stale = isStale(provider) ? " · " + t("strategy.staleShort") : "";
    if (status.status === "ok") {
      return {
        cls: "ok" + (stale ? " stale" : ""),
        text: t("strategy.returned", { n: fmtNumber(status.returned) }) + (typeof status.total_found === "number" ? " · " + t("status.total", { total: fmtNumber(status.total_found) }) : "") + stale
      };
    }
    if (status.status === "error") return { cls: "error" + (stale ? " stale" : ""), text: t("status.error") + stale };
    return null;
  }

  function updateStaleMarkers() {
    var body = $("strategy-body");
    body.querySelectorAll(".query-card[data-provider]").forEach(function (card) {
      var badge = card.querySelector(".query-status");
      var info = badgeFor(card.getAttribute("data-provider"));
      if (badge && info) { badge.className = "query-status " + info.cls; badge.textContent = info.text; }
    });
    var stale = anyStale();
    var notice = $("strategy-stale");
    if (notice) notice.hidden = !stale;
    var statusNote = $("status-stale");
    if (statusNote) statusNote.hidden = !stale;
  }

  function filterText(params) {
    return params && params.filter ? t("strategy.filter", { filter: params.filter }) : "";
  }

  function queryCard(provider) {
    var compiled = state.compiled.providers[provider];
    var spec = queryFor(provider);
    var edited = spec.edited;
    var live = Planner.LIVE_PROVIDERS.indexOf(provider) >= 0;
    var status = state.statuses.find(function (item) { return item.source === provider; });
    var area = el("textarea", { class: "query-text", rows: "3", spellcheck: "false", "data-fk": "query:" + provider, "aria-label": sourceLabel(provider) });
    area.value = spec.query;
    var link = externalLink(siteUrlFor(provider, spec.query, spec.params), t("strategy.open." + provider), "btn btn-ghost btn-small");
    var copy = el("button", { type: "button", class: "btn btn-ghost btn-small", text: t("strategy.copy") });
    copy.addEventListener("click", function () { copyText(area.value, copy); });
    var restore = el("button", {
      type: "button",
      class: "btn btn-ghost btn-small",
      "data-fk": "restore:" + provider,
      text: t("strategy.restore"),
      hidden: !edited,
      onclick: function () { delete state.overrides[provider]; renderStrategy("query:" + provider); }
    });
    area.addEventListener("input", function () {
      state.overrides[provider] = area.value;
      var url = siteUrlFor(provider, area.value, spec.params);
      if (url) link.setAttribute("href", url);
      card.classList.add("edited");
      restore.hidden = false;
      updateStaleMarkers();
    });

    var info = badgeFor(provider);
    var badge = info ? el("span", { class: "query-status " + info.cls, text: info.text }) : null;

    var notes = (compiled.notes || []).filter(function (note) { return note !== "link_only"; }).map(function (note) {
      return el("li", { text: t("note." + note) });
    });
    var translation = null;
    if (provider === "pubmed" && status && status.translation && status.translation.query_translation) {
      var tr = status.translation;
      var missing = tr.phrases_not_found.concat(tr.fields_not_found);
      translation = el("details", { class: "translation" },
        el("summary", { text: t("strategy.translation") }),
        el("code", { text: tr.query_translation }),
        missing.length ? el("p", { class: "warn-line", text: t("strategy.notFound", { list: missing.join(", ") }) }) : null,
        tr.phrases_ignored.length ? el("p", { class: "note", text: t("strategy.ignored", { list: tr.phrases_ignored.join(", ") }) }) : null);
    }

    var filter = filterText(spec.params);
    var card = el("article", { class: "query-card" + (edited ? " edited" : "") + (live ? "" : " link-only"), "data-provider": provider },
      el("header", null,
        el("strong", { text: sourceLabel(provider) }),
        badge,
        el("span", { class: "edited-tag", text: t("strategy.edited") })),
      area,
      filter ? el("p", { class: "query-filter" }, el("code", { text: filter })) : null,
      el("p", { class: "edited-note", text: t("strategy.editedNote") }),
      el("div", { class: "query-actions" }, copy, link, restore),
      translation);
    return card;
  }

  // Removes PubMed field tags ([tiab], [mh] ...) from the other sources' strings.
  // The result is an ordinary hand edit: visible, and undone with "Restaurar".
  function stripPubmedTags() {
    STRATEGY_PROVIDERS.forEach(function (provider) {
      if (provider === "pubmed") return;
      var text = queryFor(provider).query.replace(/\[[A-Za-z /-]+\]/g, " ").replace(/\s+/g, " ").replace(/\(\s+/g, "(").replace(/\s+\)/g, ")").trim();
      state.overrides[provider] = text;
    });
    refreshStrategy();
  }

  function plural(key, n, params) {
    return t(key + (n === 1 ? ".one" : ".other"), params);
  }

  function renderStrategy(focusKey) {
    var section = $("strategy");
    var view = section.hidden ? null : captureStrategyView();
    var body = $("strategy-body");
    // Hold the current height while rebuilding so the page does not shrink and jump.
    if (view) body.style.minHeight = body.offsetHeight + "px";
    clear(body);
    if (!state.plan || state.origin === "file") { body.style.minHeight = ""; section.hidden = true; return; }
    section.hidden = false;
    buildStrategy(body);
    updateStaleMarkers();
    body.style.minHeight = "";
    if (view) restoreStrategyView(view, focusKey);
  }

  function buildStrategy(body) {
    var plan = state.plan;
    var enabledBlocks = plan.blocks.filter(function (block) { return block.enabled; });
    var recognised = plan.blocks.filter(function (b) { return b.source === "vocabulary"; }).length;
    var summary = plan.mode === "manual"
      ? t("strategy.summaryManual")
      : plural("strategy.concepts", recognised, { n: recognised }) + " · " + plural("strategy.blocksOn", enabledBlocks.length, { on: enabledBlocks.length });
    $("strategy-summary").textContent = summary;

    if (plan.mode === "manual") {
      body.appendChild(el("div", { class: "manual-box" },
        plan.warnings.filter(function (warning) { return warning.code !== "manual_string"; }).length
          ? el("ul", { class: "strategy-warnings" }, plan.warnings.filter(function (warning) { return warning.code !== "manual_string"; }).map(function (warning) {
            return el("li", { text: warningText(warning) });
          }))
          : null,
        el("p", { text: t("warn.manual_string") }),
        el("div", { class: "manual-actions" },
          el("button", { type: "button", class: "btn btn-ghost", text: t("strategy.interpret"), onclick: function () { runSearch(state.query, { literal: true }); } }),
          plan.warnings.some(function (warning) { return warning.code === "manual_pubmed_tags"; })
            ? el("button", { type: "button", class: "btn btn-ghost", text: t("strategy.stripTags"), onclick: stripPubmedTags })
            : null)));
    } else {
      body.appendChild(el("p", { class: "strategy-lead", text: t("strategy.lead", { version: VOCABULARY.vocabulary_version }) }));
      var warnings = plan.warnings.slice();
      if (!enabledBlocks.length && plan.blocks.length) warnings.push({ code: "no_enabled_blocks" });
      if (warnings.length) {
        body.appendChild(el("ul", { class: "strategy-warnings" }, warnings.map(function (warning) {
          return el("li", { text: warningText(warning) });
        })));
      }
      body.appendChild(el("div", { class: "block-grid" }, plan.blocks.map(blockCard)));
      // Boolean logic remains in the compiled queries, not in the primary UI.
      if (plan.dropped_terms.length) {
        body.appendChild(el("p", { class: "note", text: t("strategy.dropped", { list: plan.dropped_terms.join(", ") }) }));
      }

      var fieldGroup = el("div", { class: "field-mode", role: "radiogroup", "aria-label": t("strategy.fieldMode") },
        el("span", { class: "control-label", text: t("strategy.fieldMode") }),
        Planner.FIELD_MODES.map(function (mode) {
          var radio = el("input", { type: "radio", name: "field-mode", value: mode, "data-fk": "field:" + mode });
          radio.checked = state.fieldMode === mode;
          radio.addEventListener("change", function () { state.fieldMode = mode; refreshStrategy(); });
          return el("label", { class: "radio" }, radio, el("span", { text: t("strategy.field." + mode) }));
        }));
      var pt = el("input", { type: "checkbox", "data-fk": "include-pt" });
      pt.checked = state.includePt;
      pt.addEventListener("change", function () { state.includePt = pt.checked; refreshStrategy(); });
      var yearFrom = el("input", { type: "number", min: "1900", max: String(currentYear() + 1), placeholder: "—", "data-fk": "year-from", "aria-label": t("strategy.years") + " " + t("filters.yearFrom") });
      var yearTo = el("input", { type: "number", min: "1900", max: String(currentYear() + 1), placeholder: "—", "data-fk": "year-to", "aria-label": t("strategy.years") + " " + t("filters.yearTo") });
      if (plan.year_from) yearFrom.value = String(plan.year_from);
      if (plan.year_to) yearTo.value = String(plan.year_to);
      var onYears = function () {
        var from = Number(yearFrom.value);
        var to = Number(yearTo.value);
        plan.year_from = from >= 1900 ? from : null;
        plan.year_to = to >= 1900 ? to : null;
        // "change" fires while focus is moving (Tab); rebuild once it has landed.
        setTimeout(function () { refreshStrategy(); }, 0);
      };
      yearFrom.addEventListener("change", onYears);
      yearTo.addEventListener("change", onYears);
      body.appendChild(el("div", { class: "strategy-controls" },
        fieldGroup,
        el("label", { class: "check" }, pt, el("span", { text: t("strategy.includePt") })),
        el("div", { class: "years" }, el("span", { class: "control-label", text: t("strategy.years") }),
          el("span", { text: t("filters.yearFrom") }), yearFrom, el("span", { text: t("filters.yearTo") }), yearTo)));
    }

    var copyAll = el("button", { type: "button", class: "btn btn-ghost", text: t("strategy.copyAll") });
    copyAll.addEventListener("click", function () {
      copyText(STRATEGY_PROVIDERS.map(function (provider) {
        return sourceLabel(provider) + "\n" + queryFor(provider).query;
      }).join("\n\n"), copyAll);
    });
    body.appendChild(el("details", { class: "queries-details" },
      el("summary", { text: t("strategy.queries") }),
      el("div", { class: "query-grid" }, STRATEGY_PROVIDERS.map(queryCard)),
      el("p", null, copyAll)));
    body.appendChild(el("p", { id: "strategy-stale", class: "stale-note", role: "status", hidden: true, text: t("strategy.stale") }));
    body.appendChild(el("div", { class: "strategy-actions" },
      el("button", { type: "button", class: "btn btn-primary", text: t("strategy.rerun"), onclick: function () { executePlan(); } }),
      el("button", { type: "button", class: "btn btn-ghost", text: t("strategy.close"), onclick: closeStrategy })));
  }

  function loadRows(rows) {
    state.result = Core.runPipeline(rows, DATA);
    if (state.origin === "file" && state.fileManifest && state.fileManifest.counts) {
      var originalCounts = state.fileManifest.counts;
      if (typeof originalCounts.retrieved_rows === "number") state.result.stats.retrieved_rows = originalCounts.retrieved_rows;
      if (typeof originalCounts.duplicates_merged === "number") state.result.stats.duplicates_merged = originalCounts.duplicates_merged;
    }
    state.filters = emptyFilters();
    state.shown = PAGE_SIZE;
    renderAll();
    if (state.tab !== "results" && state.tab !== "quality") selectTab("results");
  }

  // ------------------------------------------------------------------ hash state

  function cleanTerm(value) {
    return String(value || "").replace(/"/g, " ").replace(/\s+/g, " ").trim().slice(0, MAX_TERM_LENGTH);
  }

  function linkYear(value) {
    var year = Number(value);
    return Number.isInteger(year) && year >= 1900 && year <= currentYear() + 1 ? year : null;
  }

  // What the person changed in the strategy panel, relative to the plan the same
  // question produces on its own: blocks switched on/off (e), terms switched off (x),
  // synonyms added (a), the period (y) and strings edited by hand (o).
  function strategyDelta() {
    var plan = state.plan;
    var delta = {};
    if (!plan) return delta;
    if (plan.mode !== "manual") {
      var fresh = freshPlan(state.query, state.literal);
      var defaults = {};
      fresh.blocks.forEach(function (block) { defaults[block.key] = block.enabled; });
      var blocks = {};
      plan.blocks.forEach(function (block) {
        var entry = {};
        if (defaults[block.key] !== undefined && block.enabled !== defaults[block.key]) entry.e = block.enabled ? 1 : 0;
        var off = block.terms.filter(function (term) { return term.enabled === false; }).map(function (term) { return term.text; });
        var added = block.terms.filter(function (term) { return term.added; }).map(function (term) { return term.text; });
        if (off.length) entry.x = off;
        if (added.length) entry.a = added;
        if (Object.keys(entry).length) blocks[block.key] = entry;
      });
      if (Object.keys(blocks).length) delta.b = blocks;
      if ((plan.year_from || null) !== (fresh.year_from || null) || (plan.year_to || null) !== (fresh.year_to || null)) {
        delta.y = [plan.year_from || null, plan.year_to || null];
      }
    }
    var edited = {};
    STRATEGY_PROVIDERS.forEach(function (provider) {
      if (typeof state.overrides[provider] === "string") edited[provider] = state.overrides[provider];
    });
    if (Object.keys(edited).length) delta.o = edited;
    return delta;
  }

  // Applies a delta read from a link. Everything is validated: the link is input
  // from anyone, and unknown blocks, sources or malformed values are ignored.
  function applyStrategyDelta(plan, delta) {
    if (!delta || typeof delta !== "object") return;
    if (plan.mode !== "manual" && delta.b && typeof delta.b === "object") {
      plan.blocks.forEach(function (block) {
        var entry = delta.b[block.key];
        if (!entry || typeof entry !== "object") return;
        if (entry.e === 0 || entry.e === 1) block.enabled = entry.e === 1;
        (Array.isArray(entry.a) ? entry.a.slice(0, 20) : []).forEach(function (raw) {
          var text = cleanTerm(raw);
          if (text && !block.terms.some(function (term) { return term.text === text; })) {
            block.terms.push({ text: text, lang: block.role === "free" ? "any" : "en", enabled: true, added: true });
          }
        });
        (Array.isArray(entry.x) ? entry.x.slice(0, 100) : []).forEach(function (raw) {
          block.terms.forEach(function (term) { if (term.text === String(raw)) term.enabled = false; });
        });
      });
    }
    if (plan.mode !== "manual" && Array.isArray(delta.y)) {
      plan.year_from = linkYear(delta.y[0]);
      plan.year_to = linkYear(delta.y[1]);
    }
    if (delta.o && typeof delta.o === "object") {
      STRATEGY_PROVIDERS.forEach(function (provider) {
        if (typeof delta.o[provider] === "string") state.overrides[provider] = delta.o[provider].slice(0, MAX_LINK_STRING);
      });
    }
  }

  // The link reproduces the search whose results are on screen: the strategy as it
  // was executed, not unsaved edits made afterwards.
  function updateHash() {
    var params = new URLSearchParams();
    var executed = state.origin === "search" ? state.executed : null;
    if (state.query) params.set("q", state.query);
    params.set("src", Array.from(state.sources).join(","));
    params.set("n", String(state.limit));
    var fieldMode = executed ? executed.field_mode : state.fieldMode;
    var includePt = executed ? executed.include_pt : state.includePt;
    if (fieldMode !== "title_abstract") params.set("f", fieldMode);
    if (includePt) params.set("pt", "1");
    if (executed && executed.literal) params.set("lit", "1");
    if (executed && executed.strategy && Object.keys(executed.strategy).length) params.set("s", JSON.stringify(executed.strategy));
    if (I18n.lang() !== "pt") params.set("lang", I18n.lang());
    try { history.replaceState(null, "", "#" + params.toString()); } catch (error) { location.hash = params.toString(); }
  }

  function readHash() {
    var params = new URLSearchParams(String(location.hash || "").replace(/^#/, ""));
    var src = params.get("src");
    if (src) {
      var chosen = src.split(",").filter(function (id) { return SOURCE_LABELS[id]; });
      if (chosen.length) state.sources = new Set(chosen);
    }
    var limit = Number(params.get("n"));
    if ([25, 50, 100].indexOf(limit) >= 0) { state.limit = limit; $("limit").value = String(limit); }
    if (Planner.FIELD_MODES.indexOf(params.get("f")) >= 0) state.fieldMode = params.get("f");
    state.includePt = params.get("pt") === "1";
    var strategy = null;
    try { strategy = params.get("s") ? JSON.parse(params.get("s")) : null; } catch (error) { strategy = null; }
    return {
      query: params.get("q") || "",
      lang: params.get("lang") || "",
      literal: params.get("lit") === "1",
      strategy: strategy
    };
  }

  // ------------------------------------------------------------------ results: filters

  function facetCounts(rows) {
    var counts = { levels: {}, groups: {}, unclassified: 0, docClasses: {}, sources: {}, years: [] };
    rows.forEach(function (row) {
      var level = levelOf(row);
      counts.levels[level] = (counts.levels[level] || 0) + 1;
      var groups = row.taxonomy_groups || [];
      if (!groups.length) counts.unclassified += 1;
      groups.forEach(function (group) { counts.groups[group] = (counts.groups[group] || 0) + 1; });
      var docClass = row.document_classification.document_class;
      counts.docClasses[docClass] = (counts.docClasses[docClass] || 0) + 1;
      (row.source_providers || [Core.pyText(row.source_provider || row.source)]).forEach(function (source) {
        counts.sources[source] = (counts.sources[source] || 0) + 1;
      });
      if (row.reference_year) counts.years.push(row.reference_year);
    });
    return counts;
  }

  function checkboxOption(label, count, checked, onChange) {
    var input = el("input", { type: "checkbox" });
    input.checked = checked;
    input.addEventListener("change", function () { onChange(input.checked); });
    return el("label", { class: "filter-option" }, input, el("span", { text: label }), el("span", { class: "count", text: fmtNumber(count) }));
  }

  function toggleIn(set, value, on) {
    if (on) set.add(value); else set.delete(value);
    state.shown = PAGE_SIZE;
    renderResults();
  }

  function renderFilters() {
    var box = clear($("filters"));
    var rows = state.result.ranked;
    var counts = facetCounts(rows);
    var f = state.filters;

    var levelGroup = el("div", { class: "filter-group" }, el("h3", { text: t("filters.level") }));
    ["A", "B"].forEach(function (level) {
      if (!counts.levels[level]) return;
      levelGroup.appendChild(checkboxOption(t("level." + level + ".name"), counts.levels[level], f.levels.has(level), function (on) { toggleIn(f.levels, level, on); }));
    });
    box.appendChild(levelGroup);

    var axisGroup = el("div", { class: "filter-group" }, el("h3", { text: t("filters.axis") }));
    DATA.taxonomy.families.forEach(function (family) {
      var present = DATA.taxonomy.groups.filter(function (group) { return group.family === family.id && counts.groups[group.id]; })
        .sort(function (a, b) { return counts.groups[b.id] - counts.groups[a.id]; });
      if (!present.length) return;
      axisGroup.appendChild(el("h4", { text: familyLabel(family, false) }));
      present.forEach(function (group) {
        axisGroup.appendChild(checkboxOption(groupLabel(group.id), counts.groups[group.id], f.groups.has(group.id), function (on) { toggleIn(f.groups, group.id, on); }));
      });
    });
    if (counts.unclassified) {
      axisGroup.appendChild(checkboxOption(t("filters.unclassified"), counts.unclassified, f.unclassified, function (on) {
        f.unclassified = on; state.shown = PAGE_SIZE; renderResults();
      }));
    }
    box.appendChild(axisGroup);

    var docGroup = el("div", { class: "filter-group" }, el("h3", { text: t("filters.doctype") }));
    Object.keys(counts.docClasses).sort(function (a, b) { return counts.docClasses[b] - counts.docClasses[a]; }).forEach(function (docClass) {
      docGroup.appendChild(checkboxOption(docClassLabel(docClass), counts.docClasses[docClass], f.docClasses.has(docClass), function (on) { toggleIn(f.docClasses, docClass, on); }));
    });
    box.appendChild(docGroup);

    var sourceGroup = el("div", { class: "filter-group" }, el("h3", { text: t("filters.source") }));
    Object.keys(counts.sources).sort().forEach(function (source) {
      sourceGroup.appendChild(checkboxOption(sourceLabel(source), counts.sources[source], f.sources.has(source), function (on) { toggleIn(f.sources, source, on); }));
    });
    box.appendChild(sourceGroup);

    if (counts.years.length) {
      var minYear = Math.min.apply(null, counts.years);
      var maxYear = Math.max.apply(null, counts.years);
      var from = el("input", { type: "number", inputmode: "numeric", min: minYear, max: maxYear, placeholder: String(minYear), "aria-label": t("filters.year") + " " + t("filters.yearFrom") });
      var to = el("input", { type: "number", inputmode: "numeric", min: minYear, max: maxYear, placeholder: String(maxYear), "aria-label": t("filters.year") + " " + t("filters.yearTo") });
      if (f.yearFrom) from.value = String(f.yearFrom);
      if (f.yearTo) to.value = String(f.yearTo);
      var onYear = function () {
        f.yearFrom = Number(from.value) || null;
        f.yearTo = Number(to.value) || null;
        state.shown = PAGE_SIZE;
        renderResults();
      };
      from.addEventListener("change", onYear);
      to.addEventListener("change", onYear);
      box.appendChild(el("div", { class: "filter-group" }, el("h3", { text: t("filters.year") }),
        el("div", { class: "year-range" }, el("span", { text: t("filters.yearFrom") }), from, el("span", { text: t("filters.yearTo") }), to)));
    }

    var abstractInput = el("input", { type: "checkbox" });
    abstractInput.checked = f.abstractOnly;
    abstractInput.addEventListener("change", function () { f.abstractOnly = abstractInput.checked; state.shown = PAGE_SIZE; renderResults(); });
    box.appendChild(el("div", { class: "filter-group" }, el("label", { class: "filter-option" }, abstractInput, el("span", { text: t("filters.abstract") }))));

    box.appendChild(el("button", {
      type: "button",
      class: "btn btn-ghost",
      text: t("filters.clear"),
      onclick: function () { state.filters = emptyFilters(); state.shown = PAGE_SIZE; renderFilters(); renderResults(); }
    }));
    updateMobileFilterLabel();
  }

  function activeFilterCount() {
    var f = state.filters;
    return f.levels.size + f.groups.size + f.docClasses.size + f.sources.size +
      (f.unclassified ? 1 : 0) + (f.yearFrom ? 1 : 0) + (f.yearTo ? 1 : 0) + (f.abstractOnly ? 1 : 0);
  }

  function updateMobileFilterLabel() {
    var button = $("mobile-filter-btn");
    if (!button) return;
    var n = activeFilterCount();
    button.textContent = t("filters.mobile") + (n ? " (" + n + ")" : "");
  }

  function passesFilters(row) {
    var f = state.filters;
    if (f.levels.size && !f.levels.has(levelOf(row))) return false;
    if (f.groups.size || f.unclassified) {
      var groups = row.taxonomy_groups || [];
      var axisHit = groups.some(function (group) { return f.groups.has(group); }) || (f.unclassified && !groups.length);
      if (!axisHit) return false;
    }
    if (f.docClasses.size && !f.docClasses.has(row.document_classification.document_class)) return false;
    if (f.sources.size) {
      var providers = row.source_providers || [Core.pyText(row.source_provider || row.source)];
      if (!providers.some(function (source) { return f.sources.has(source); })) return false;
    }
    if (f.yearFrom && !(row.reference_year && row.reference_year >= f.yearFrom)) return false;
    if (f.yearTo && !(row.reference_year && row.reference_year <= f.yearTo)) return false;
    if (f.abstractOnly && !abstractPresent(row)) return false;
    return true;
  }

  // Alphabetical order starts at the first letter: leading brackets, digits and
  // abstract codes ("[Article in Portuguese]", "607-P: ...") are skipped.
  function titleSortKey(row) {
    var title = String(row.title || "");
    var code = title.match(/^\s*\d+[-\w]*\s*:\s*/);
    if (code) title = title.slice(code[0].length);
    var key = title.replace(/^[^\p{L}]+/u, "");
    return key || title;
  }

  function sortRows(rows) {
    var sorted = rows.slice();
    var byRank = function (a, b) { return a.reference_rank - b.reference_rank; };
    if (state.sort === "recent") {
      sorted.sort(function (a, b) { return (Number(b.reference_year || 0) - Number(a.reference_year || 0)) || byRank(a, b); });
    } else if (state.sort === "completeness") {
      sorted.sort(function (a, b) { return (b.metadata_completeness.present - a.metadata_completeness.present) || byRank(a, b); });
    } else if (state.sort === "title") {
      sorted.sort(function (a, b) { return titleSortKey(a).localeCompare(titleSortKey(b), undefined, { sensitivity: "base" }) || byRank(a, b); });
    } else {
      sorted.sort(byRank);
    }
    return sorted;
  }

  // ------------------------------------------------------------------ results: cards

  function completenessMeter(row) {
    var completeness = row.metadata_completeness;
    var missing = Core.COMPLETENESS_FIELDS.filter(function (field) { return !completeness.fields[field]; })
      .map(function (field) { return t("field." + field); });
    if (!missing.length) return null;
    return el("span", { class: "meter", text: t("completeness.label", { fields: missing.join(", ") }) });
  }

  function axisChips(row, limit) {
    var groups = (row.taxonomy_groups || []).slice();
    if (!groups.length) return null;
    var primary = row.taxonomy_primary;
    groups.sort(function (a, b) { return (a === primary ? -1 : 0) - (b === primary ? -1 : 0); });
    var shown = groups.slice(0, limit || 2);
    return el("span", { class: "axis-topics", text: shown.map(groupLabel).join(", ") });
  }

  function authorsText(authors) {
    var text = String(authors || "").trim();
    if (!text) return "";
    var parts = text.split(";").map(function (part) { return part.trim(); }).filter(Boolean);
    if (parts.length > 3) return parts.slice(0, 3).join(", ") + " et al.";
    return text.length > 140 ? text.slice(0, 137).replace(/[;,\s]+\S*$/, "") + " et al." : text;
  }

  function identifierLinks(row) {
    var items = [];
    var doi = Core.normalizeDoi(row.doi);
    var pmid = Core.normalizePmid(row.pmid);
    if (doi) items.push(externalLink("https://doi.org/" + doi, "DOI"));
    if (pmid) items.push(externalLink("https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/", "PMID"));
    return items.length ? el("span", { class: "record-ids" }, items) : null;
  }

  function whyBlock(title, children, wide) {
    var block = el("div", { class: "why-block" }, el("h4", { text: title }), children);
    if (wide) block.style.gridColumn = "1 / -1";
    return block;
  }

  function buildWhy(row, quarantined) {
    var level = levelOf(row);
    var blocks = [];
    blocks.push(whyBlock(t("card.traceability"), [
      levelBadge(level),
      el("p", { text: reasonsText(row.audit_reasons) || t("level." + level + ".short") })
    ]));

    var completeness = row.metadata_completeness;
    var missing = Core.COMPLETENESS_FIELDS.filter(function (field) { return !completeness.fields[field]; });
    blocks.push(whyBlock(t("completeness.title"), missing.length
      ? el("p", { text: t("completeness.label", { fields: missing.map(function (field) { return t("field." + field); }).join(", ") }) })
      : el("p", { text: I18n.lang() === "pt" ? "Completos" : "Complete" })));

    var groups = row.taxonomy_groups || [];
    blocks.push(whyBlock(t("card.taxonomy"), groups.length
      ? el("p", { text: groups.slice(0, 6).map(groupLabel).join(", ") })
      : el("p", { class: "note", text: t("card.unclassified") })));

    var doc = row.document_classification;
    blocks.push(whyBlock(t("card.doctype"), el("p", { text: docClassLabel(doc.document_class) })));

    if (!quarantined) {
      var breakdown = row.score_breakdown;
      var keys = ["taxonomy", "focus_keywords", "document_type", "provider", "identifier", "recency", "penalties"];
      var table = el("table", { class: "score-table" }, el("tbody", null,
        keys.map(function (key) {
          return el("tr", null, el("td", { text: t("score." + key) }), el("td", { text: String(breakdown[key]) }));
        }),
        el("tr", { class: "total" }, el("td", { text: "Total" }), el("td", { text: String(row.reference_score) }))));
      blocks.push(whyBlock(t("card.priority") + " · " + t("card.priority.value", { rank: row.reference_rank, score: row.reference_score }), [
        table,
        row.focus_keyword_hits && row.focus_keyword_hits.length ? el("p", { class: "terms", text: row.focus_keyword_hits.join(" · ") }) : null,
        el("p", { class: "note", text: t("card.priority.note") })
      ]));
    }

    var manifestations = row.source_manifestations || [];
    var providers = manifestations.map(function (item) { return sourceLabel(item.provider || item.source || "?"); })
      .filter(function (provider, index, all) { return all.indexOf(provider) === index; });
    if (!providers.length) providers = (row.source_providers || [row.source_provider || row.source]).filter(Boolean).map(sourceLabel);
    if (providers.length) blocks.push(whyBlock(t("card.provenance"), el("p", { text: providers.join(", ") })));

    var abstract = Core.pyText(row.abstract || row.summary || row.snippet);
    blocks.push(whyBlock(t("card.abstract"), abstract
      ? el("p", { class: "abstract", text: abstract })
      : el("p", { class: "note", text: t("card.noAbstract") }), true));

    return el("div", { class: "why-grid" }, blocks);
  }

  function recordCard(row, quarantined) {
    var level = levelOf(row);
    var doc = row.document_classification;
    var titleText = Core.pyText(row.title) || "(" + t("reason.missing_title") + ")";
    var doi = Core.normalizeDoi(row.doi);
    var pmid = Core.normalizePmid(row.pmid);
    var href = doi ? "https://doi.org/" + doi : (pmid ? "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/" : (Core.normalizeUrl(row.url) ? row.url : null));
    var meta = [authorsText(row.authors), Core.pyText(row.journal), row.reference_year || Core.extractYear(row, new Date().getFullYear()) || ""]
      .filter(function (part) { return part; }).join(" · ");

    var details = el("details", { class: "why" }, el("summary", { text: t("card.why") }));
    var built = false;
    details.addEventListener("toggle", function () {
      if (details.open && !built) { built = true; details.appendChild(buildWhy(row, quarantined)); }
    });

    return el("li", { class: "record level-" + level },
      el("h3", null, href ? externalLink(href, titleText) : titleText),
      meta ? el("p", { class: "record-meta", text: meta }) : null,
      el("div", { class: "record-line" },
        el("span", { "data-tip": t("level." + level + ".short") }, levelBadge(level)),
        doc.document_class !== "unclassified" ? el("span", { class: "doctype-tag", text: docClassLabel(doc.document_class) }) : null,
        completenessMeter(row),
        identifierLinks(row),
        axisChips(row, 2),
        details));
  }

  function renderResults() {
    var list = clear($("results-list"));
    var filtered = sortRows(state.result.ranked.filter(passesFilters));
    var visible = filtered.slice(0, state.shown);
    visible.forEach(function (row) { list.appendChild(recordCard(row, false)); });
    if (!filtered.length) list.appendChild(el("li", { class: "empty-note", text: t("results.none") }));
    $("results-count").textContent = t("results.count", { shown: fmtNumber(visible.length), n: fmtNumber(filtered.length) });
    var more = $("show-more");
    var remaining = filtered.length - visible.length;
    more.hidden = remaining <= 0;
    more.textContent = t("results.more", { n: fmtNumber(Math.min(PAGE_SIZE, remaining)) });
  }

  function renderStrip() {
    var strip = clear($("quality-strip"));
    var stats = state.result.stats;
    var all = works();
    var withAbstract = all.filter(abstractPresent).length;
    strip.appendChild(el("h2", { text: t("strip.title") }));
    strip.appendChild(abqBar(stats.levels, { tall: true }));
    strip.appendChild(el("div", { class: "abq-legend" }, LEVELS.map(function (level) {
      return el("span", null, el("i", { class: "abq-key " + level, "aria-hidden": "true" }),
        t("level." + level + ".name") + ": " + fmtNumber(stats.levels[level]) + " (" + pct(stats.levels[level], stats.works) + "%)");
    })));
    strip.appendChild(el("div", { class: "strip-facts" },
      el("span", { text: t("strip.merged", { n: fmtNumber(stats.duplicates_merged) }) }),
      el("span", { text: t("strip.classified", { p: pct(stats.classified, stats.works) }) }),
      el("span", { text: t("strip.abstract", { p: pct(withAbstract, stats.works) }) })));
  }

  // ------------------------------------------------------------------ quality panel

  function hbarRows(items, max, formatValue) {
    return items.map(function (item) {
      var fill = el("div", { class: "hbar-fill", "data-tip": item.label + ": " + formatValue(item) });
      fill.style.width = (max ? (item.value / max) * 100 : 0) + "%";
      return el("div", { class: "hbar-row" },
        el("span", { class: "hbar-label", text: item.label }),
        el("div", { class: "hbar-track" }, fill),
        el("span", { class: "hbar-value", text: formatValue(item) }));
    });
  }

  function renderQuality() {
    var stats = state.result.stats;
    var all = works();
    var withAbstract = all.filter(abstractPresent).length;

    var kpis = clear($("kpis"));
    [
      [t("quality.kpi.retrieved"), fmtNumber(stats.retrieved_rows), ""],
      [t("quality.kpi.unique"), fmtNumber(stats.unique_ranked), ""],
      [t("quality.kpi.merged"), fmtNumber(stats.duplicates_merged), ""],
      [t("quality.kpi.A"), fmtNumber(stats.levels.A), pct(stats.levels.A, stats.works) + "%", "A"],
      [t("quality.kpi.B"), fmtNumber(stats.levels.B), pct(stats.levels.B, stats.works) + "%", "B"],
      [t("quality.kpi.Q"), fmtNumber(stats.levels.Q), pct(stats.levels.Q, stats.works) + "%", "Q"],
      [t("quality.kpi.classified"), pct(stats.classified, stats.works) + "%", fmtNumber(stats.classified)],
      [t("quality.kpi.abstract"), pct(withAbstract, stats.works) + "%", fmtNumber(withAbstract)]
    ].forEach(function (kpi) {
      kpis.appendChild(el("div", { class: "kpi" + (kpi[3] ? " level-" + kpi[3] : "") },
        el("div", { class: "kpi-value", text: kpi[1] }),
        el("div", { class: "kpi-label" }, kpi[3] ? el("span", { class: "level-letter", "aria-hidden": "true", text: kpi[3] }) : null, kpi[0]),
        kpi[2] ? el("div", { class: "kpi-sub", text: kpi[2] }) : null));
    });

    var legend = $("abq-legend");
    legend.replaceWith(Object.assign(abqLegend(), { id: "abq-legend" }));

    var chart = clear($("axis-chart"));
    var byGroup = stats.by_group;
    var maxWorks = Object.keys(byGroup).reduce(function (max, key) { return Math.max(max, byGroup[key].works); }, 0);
    var tableRows = [];
    DATA.taxonomy.families.forEach(function (family) {
      var entries = Object.keys(byGroup).map(function (key) { return byGroup[key]; })
        .filter(function (entry) { return entry.family === family.id; })
        .sort(function (a, b) { return (b.works - a.works) || a.group.localeCompare(b.group); });
      var block = el("section", { class: "family-block" },
        el("h3", null, el("span", { class: "family-tag", text: familyLabel(family, true) }), familyLabel(family, false)));
      if (!entries.length) block.appendChild(el("p", { class: "empty-note", text: t("quality.noAxis") }));
      entries.forEach(function (entry) {
        tableRows.push(entry);
        block.appendChild(el("button", {
          type: "button",
          class: "axis-row",
          onclick: function () {
            state.filters = emptyFilters();
            state.filters.groups.add(entry.group);
            state.shown = PAGE_SIZE;
            renderFilters();
            renderResults();
            selectTab("results", true);
          }
        },
          el("span", { class: "axis-label", text: groupLabel(entry.group) }),
          el("span", { class: "axis-track" }, abqBar(entry, { widthPct: maxWorks ? (entry.works / maxWorks) * 100 : 0 })),
          el("span", { class: "axis-values", text: t("quality.works", { n: fmtNumber(entry.works) }) + " · " + abqValues(entry) + " · " + t("quality.withAbstract", { p: pct(entry.with_abstract, entry.works) }) })));
      });
      chart.appendChild(block);
    });
    chart.appendChild(el("details", { class: "table-toggle" },
      el("summary", { text: t("quality.table") }),
      el("table", { class: "data-table" },
        el("thead", null, el("tr", null,
          el("th", { text: t("quality.col.axis") }),
          el("th", { class: "num", text: t("quality.col.works") }),
          LEVELS.map(function (level) { return el("th", { class: "num", text: level }); }),
          el("th", { class: "num", text: t("field.abstract") }))),
        el("tbody", null, tableRows.map(function (entry) {
          return el("tr", null,
            el("td", { text: groupLabel(entry.group) }),
            el("td", { class: "num", text: fmtNumber(entry.works) }),
            LEVELS.map(function (level) { return el("td", { class: "num", text: fmtNumber(entry[level]) }); }),
            el("td", { class: "num", text: pct(entry.with_abstract, entry.works) + "%" }));
        })))));

    var sourceChart = clear($("source-chart"));
    var sources = Object.keys(stats.by_source);
    var maxRows = sources.reduce(function (max, key) { return Math.max(max, stats.by_source[key].rows); }, 0);
    sources.sort(function (a, b) { return stats.by_source[b].rows - stats.by_source[a].rows; }).forEach(function (source) {
      var entry = stats.by_source[source];
      sourceChart.appendChild(el("div", { class: "hbar-row" },
        el("span", { class: "hbar-label", text: sourceLabel(source) }),
        abqBar(entry, { widthPct: maxRows ? (entry.rows / maxRows) * 100 : 0 }),
        el("span", { class: "hbar-value", text: abqValues(entry) })));
    });

    var completenessChart = clear($("completeness-chart"));
    append(completenessChart, hbarRows(Core.COMPLETENESS_FIELDS.map(function (field) {
      return { label: t("field." + field), value: stats.completeness_fields[field] };
    }), stats.works, function (item) { return pct(item.value, stats.works) + "% (" + fmtNumber(item.value) + ")"; }));

    var docChart = clear($("doctype-chart"));
    var docItems = Object.keys(stats.document_classes).map(function (key) {
      return { label: docClassLabel(key), value: stats.document_classes[key] };
    }).sort(function (a, b) { return b.value - a.value; });
    append(docChart, hbarRows(docItems, docItems.length ? docItems[0].value : 0, function (item) { return fmtNumber(item.value); }));

    renderYears(clear($("year-chart")), stats.years);
  }

  function renderYears(container, years) {
    var keys = Object.keys(years).map(Number).sort(function (a, b) { return a - b; });
    if (!keys.length) { container.appendChild(el("p", { class: "empty-note", text: "—" })); return; }
    var maxYear = keys[keys.length - 1];
    var minYear = Math.max(keys[0], maxYear - 39);
    var buckets = [];
    var earlier = 0;
    keys.forEach(function (year) { if (year < minYear) earlier += years[year]; });
    if (earlier) buckets.push({ label: "≤" + (minYear - 1), value: earlier });
    for (var year = minYear; year <= maxYear; year += 1) buckets.push({ label: String(year), value: years[year] || 0 });
    var peak = buckets.reduce(function (max, bucket) { return Math.max(max, bucket.value); }, 0);
    var hist = el("div", { class: "year-hist", role: "img", "aria-label": buckets.filter(function (b) { return b.value; }).map(function (b) { return b.label + ": " + b.value; }).join(", ") });
    buckets.forEach(function (bucket) {
      var column = el("span", { class: "year-col", "data-tip": bucket.label + ": " + fmtNumber(bucket.value) });
      column.style.height = (peak ? (bucket.value / peak) * 100 : 0) + "%";
      if (!bucket.value) column.style.visibility = "hidden";
      hist.appendChild(column);
    });
    container.appendChild(hist);
    container.appendChild(el("div", { class: "year-axis" },
      el("span", { text: buckets[0].label }),
      el("span", { text: buckets[buckets.length - 1].label })));
  }

  // ------------------------------------------------------------------ quarantine

  function renderQuarantine() {
    var list = clear($("quarantine-list"));
    var rows = state.result.quarantined;
    $("quarantine-empty").hidden = rows.length > 0;
    rows.forEach(function (row) { list.appendChild(recordCard(row, true)); });
  }

  // ------------------------------------------------------------------ render all

  function renderAll() {
    var has = Boolean(state.result);
    document.body.classList.toggle("has-results", has);
    $("search-summary").hidden = !has;
    if (has) {
      var okSources = state.statuses.filter(function (s) { return s.status === "ok" && s.source !== "file"; });
      var elapsed = state.statuses.reduce(function (max, s) { return Math.max(max, Number(s.elapsed_ms || 0)); }, 0);
      $("search-summary-text").textContent = t("summary.line", {
        n: fmtNumber(state.result.ranked.length),
        sources: state.origin === "search" ? okSources.length : 1,
        seconds: (elapsed / 1000).toLocaleString(I18n.lang() === "pt" ? "pt-BR" : "en", { maximumFractionDigits: 1 })
      });
      $("open-strategy").hidden = !(state.plan && state.origin === "search");
    }
    $("results-empty").hidden = has;
    $("results-view").hidden = !has;
    $("quality-empty").hidden = has;
    $("quality-view").hidden = !has;
    $("count-results").textContent = has ? fmtNumber(state.result.ranked.length) : "";
    $("count-quarantine").textContent = has && state.result.quarantined.length ? fmtNumber(state.result.quarantined.length) : "";
    renderStatus();
    renderStrategy();
    if (!has) return;
    renderStrip();
    renderFilters();
    renderResults();
    renderQuality();
    renderQuarantine();
  }

  // ------------------------------------------------------------------ export

  var EXPORT_INPUT_FIELDS = ["source", "source_provider", "title", "abstract", "summary", "keywords", "doi", "pmid", "pmcid", "url", "journal", "year", "publication_date", "article_type", "authors", "provider_query", "query", "retrieved_at", "is_open_access", "source_providers", "source_manifestations"];

  function exportRecord(row, quarantined) {
    var input = {};
    EXPORT_INPUT_FIELDS.forEach(function (key) { if (row[key] !== undefined && row[key] !== "") input[key] = row[key]; });
    var nutev = {
      data_level: levelOf(row),
      audit_traceability: row.audit_traceability,
      audit_reasons: row.audit_reasons,
      audit_quarantined: Boolean(quarantined),
      metadata_completeness: row.metadata_completeness,
      taxonomy_primary: row.taxonomy_primary || "",
      taxonomy_groups: row.taxonomy_groups || [],
      taxonomy_group_terms: row.taxonomy_group_terms || {},
      document_classification: row.document_classification
    };
    if (!quarantined) {
      nutev.reference_rank = row.reference_rank;
      nutev.reference_score = row.reference_score;
      nutev.score_breakdown = row.score_breakdown;
      nutev.focus_keyword_hits = row.focus_keyword_hits;
      nutev.document_type_applied = row.document_type_applied;
      nutev.taxonomy_ranks = row.taxonomy_ranks;
      nutev.reference_year = row.reference_year;
    }
    return { input: input, nutev: nutev };
  }

  function manifest() {
    return {
      product: EXPLORER_PRODUCT,
      generated_at: new Date().toISOString(),
      origin: state.origin,
      query: state.origin === "search" ? state.query : "",
      file_name: state.origin === "file" ? state.fileName : "",
      sources_queried: state.origin === "search" ? state.statuses.map(function (s) { return s.source; }) : [],
      limit_per_source: state.origin === "search" ? state.limit : null,
      sources_not_queried: Sources.NOT_QUERIED,
      pipeline: "SEARCH -> NORMALIZE -> TRACEABILITY GATE -> DEDUPLICATE -> CLASSIFY -> RANK -> EXPORT",
      engine_version: DATA.engine_version,
      taxonomy_version: DATA.taxonomy_version,
      guardrail_policy_version: DATA.guardrail_policy_version,
      document_class_ontology_version: DATA.document_class_ontology_version,
      rule_bundle_sha256: DATA.bundle_sha256,
      page_build: BUILD,
      planner_version: DATA.planner_version,
      query_vocabulary_version: VOCABULARY.vocabulary_version,
      query_plan: state.origin === "search" ? state.plan : null,
      executed_queries: state.origin === "search" ? state.executed : null,
      counts: state.result.stats,
      guardrail: {
        pt: I18n.STRINGS.pt["footer.disclaimer"],
        en: I18n.STRINGS.en["footer.disclaimer"]
      }
    };
  }

  function download(name, mime, content) {
    var blob = new Blob([content], { type: mime });
    var url = URL.createObjectURL(blob);
    var link = el("a", { download: name });
    link.href = url;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }

  function fileStem() {
    var base = state.origin === "file" ? state.fileName.replace(/\.[^.]+$/, "") : state.query;
    var slug = String(base || "nutev").normalize("NFKD").replace(/[^\w]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60).toLowerCase();
    return "nutev-open-" + (slug || "resultado") + "-" + new Date().toISOString().slice(0, 10);
  }

  function csvCell(value) {
    var text;
    if (value === null || value === undefined) text = "";
    else if (typeof value === "number") return String(value);
    else if (Array.isArray(value)) text = value.join("; ");
    else if (typeof value === "object") text = JSON.stringify(value);
    else text = String(value);
    if (/^[=+\-@\t\r]/.test(text)) text = "'" + text;
    return "\"" + text.replace(/"/g, "\"\"") + "\"";
  }

  function exportCsv() {
    var columns = ["reference_rank", "data_level", "audit_traceability", "audit_reasons", "metadata_completeness", "missing_fields", "title", "authors", "journal", "year", "doi", "pmid", "pmcid", "url", "sources", "taxonomy_primary", "taxonomy_primary_label", "taxonomy_groups", "document_class", "document_class_basis", "reference_score", "score_taxonomy", "score_focus_keywords", "score_document_type", "score_provider", "score_identifier", "score_recency", "score_penalties", "provider_query", "retrieved_at", "abstract"];
    var lines = [columns.join(",")];
    function line(row, quarantined) {
      var completeness = row.metadata_completeness;
      var breakdown = row.score_breakdown || {};
      var values = {
        reference_rank: quarantined ? null : row.reference_rank,
        data_level: levelOf(row),
        audit_traceability: row.audit_traceability,
        audit_reasons: row.audit_reasons,
        metadata_completeness: completeness.present + "/" + completeness.total,
        missing_fields: Core.COMPLETENESS_FIELDS.filter(function (field) { return !completeness.fields[field]; }),
        title: row.title,
        authors: row.authors,
        journal: row.journal,
        year: row.reference_year || row.year,
        doi: row.doi,
        pmid: row.pmid,
        pmcid: row.pmcid,
        url: row.url,
        sources: row.source_providers || [row.source_provider || row.source],
        taxonomy_primary: row.taxonomy_primary,
        taxonomy_primary_label: row.taxonomy_primary ? groupLabel(row.taxonomy_primary) : "",
        taxonomy_groups: row.taxonomy_groups,
        document_class: row.document_classification.document_class,
        document_class_basis: row.document_classification.basis,
        reference_score: quarantined ? null : row.reference_score,
        score_taxonomy: breakdown.taxonomy,
        score_focus_keywords: breakdown.focus_keywords,
        score_document_type: breakdown.document_type,
        score_provider: breakdown.provider,
        score_identifier: breakdown.identifier,
        score_recency: breakdown.recency,
        score_penalties: breakdown.penalties,
        provider_query: row.provider_query || row.query,
        retrieved_at: row.retrieved_at,
        abstract: row.abstract || row.summary || row.snippet
      };
      lines.push(columns.map(function (column) { return csvCell(values[column]); }).join(","));
    }
    state.result.ranked.forEach(function (row) { line(row, false); });
    state.result.quarantined.forEach(function (row) { line(row, true); });
    download(fileStem() + ".csv", "text/csv;charset=utf-8", "﻿" + lines.join("\r\n") + "\r\n");
  }

  function exportJson() {
    var payload = {
      manifest: manifest(),
      source_statuses: state.statuses,
      records: state.result.ranked.map(function (row) { return exportRecord(row, false); }),
      quarantine: state.result.quarantined.map(function (row) { return exportRecord(row, true); })
    };
    download(fileStem() + ".json", "application/json", JSON.stringify(payload, null, 2));
  }

  function copyLink() {
    updateHash();
    var button = $("copy-link");
    var done = function () {
      button.textContent = t("export.copied");
      setTimeout(function () { button.textContent = t("export.link"); }, 1800);
    };
    try {
      navigator.clipboard.writeText(location.href).then(done, function () { window.prompt(t("export.link"), location.href); });
    } catch (error) {
      window.prompt(t("export.link"), location.href);
    }
  }

  // ------------------------------------------------------------------ local files

  function parseCsv(text) {
    var rows = [];
    var row = [];
    var field = "";
    var quoted = false;
    for (var i = 0; i < text.length; i += 1) {
      var ch = text[i];
      if (quoted) {
        if (ch === "\"") {
          if (text[i + 1] === "\"") { field += "\""; i += 1; } else quoted = false;
        } else field += ch;
      } else if (ch === "\"") quoted = true;
      else if (ch === ",") { row.push(field); field = ""; }
      else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && text[i + 1] === "\n") i += 1;
        row.push(field); field = "";
        if (row.length > 1 || row[0] !== "") rows.push(row);
        row = [];
      } else field += ch;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    if (!rows.length) return [];
    var header = rows[0].map(function (name) { return name.replace(/^﻿/, "").trim(); });
    return rows.slice(1).map(function (cells) {
      var record = {};
      header.forEach(function (name, index) { if (name) record[name] = cells[index] === undefined ? "" : cells[index]; });
      return record;
    });
  }

  function fromExport(item) {
    if (item && typeof item === "object" && item.input && typeof item.input === "object") return item.input;
    return item;
  }

  // The explorer's own CSV lists every provider of a work in "sources"
  // ("europepmc; pubmed") instead of source/source_provider.
  function fromExplorerCsv(row) {
    if (row.source || row.source_provider || !row.sources) return row;
    var providers = String(row.sources).split(";").map(function (item) { return item.trim(); }).filter(Boolean);
    if (!providers.length) return row;
    var copy = Object.assign({}, row);
    copy.source_provider = providers[0];
    copy.source_providers = providers;
    return copy;
  }

  // Returns { rows, manifest }; manifest is set only for this explorer's own JSON export.
  function parseFileText(name, text) {
    var clean = text.replace(/^﻿/, "");
    if (/\.csv$/i.test(name)) return { rows: parseCsv(clean).map(fromExplorerCsv), manifest: null };
    var trimmed = clean.trim();
    if (!trimmed) return { rows: [], manifest: null };
    if (trimmed[0] === "[" || (trimmed[0] === "{" && !/\}\s*\n\s*\{/.test(trimmed))) {
      try {
        var parsed = parseJson(trimmed);
        if (Array.isArray(parsed)) return { rows: parsed.map(fromExport), manifest: null };
        if (parsed && typeof parsed === "object") {
          if (Array.isArray(parsed.records) || Array.isArray(parsed.quarantine)) {
            var manifest = parsed.manifest && parsed.manifest.product === EXPLORER_PRODUCT ? parsed.manifest : null;
            return { rows: (parsed.records || []).concat(parsed.quarantine || []).map(fromExport), manifest: manifest };
          }
          return { rows: [fromExport(parsed)], manifest: null };
        }
      } catch (error) {
        if (trimmed[0] === "[") throw error;
      }
    }
    return {
      rows: trimmed.split(/\r?\n/).filter(function (line) { return line.trim(); }).map(function (line) {
        return fromExport(parseJson(line));
      }),
      manifest: null
    };
  }

  function parseJson(text) {
    try { return JSON.parse(text); } catch (error) { throw new Error(t("file.invalidJson")); }
  }

  var RECORD_FIELDS = ["title", "doi", "pmid", "pmcid", "url"];

  // A file is accepted only if its rows look like bibliographic records; anything
  // else is rejected without touching the results already on screen.
  function looksBibliographic(rows) {
    var hits = rows.filter(function (row) {
      return RECORD_FIELDS.some(function (field) { return String(row[field] || "").trim(); });
    }).length;
    return hits > 0 && hits >= Math.ceil(rows.length / 2);
  }

  function loadFile(file) {
    var message = $("file-message");
    message.classList.remove("error");
    file.text().then(function (text) {
      var parsed = parseFileText(file.name, text);
      var rows = parsed.rows.filter(function (row) { return row && typeof row === "object" && !Array.isArray(row); });
      if (!rows.length) throw new Error(t("file.empty"));
      if (!looksBibliographic(rows)) throw new Error(t("file.notRecognised"));
      if (rows.length > MAX_FILE_ROWS) rows = rows.slice(0, MAX_FILE_ROWS);
      state.token += 1;
      state.origin = "file";
      state.fileName = file.name;
      state.query = "";
      state.statuses = [{ source: "file", status: "ok", returned: rows.length }];
      state.fileManifest = parsed.manifest;
      message.textContent = t("file.loaded", { n: fmtNumber(rows.length), name: file.name }) + originalSearchNote();
      loadRows(rows);
      selectTab("quality");
    }).catch(function (error) {
      message.classList.add("error");
      message.textContent = t("file.error", { name: file.name, error: error && error.message ? error.message : String(error) });
    });
  }

  function bindFile() {
    var input = $("file-input");
    var zone = $("dropzone");
    input.addEventListener("change", function () { if (input.files && input.files[0]) loadFile(input.files[0]); input.value = ""; });
    ["dragenter", "dragover"].forEach(function (type) {
      zone.addEventListener(type, function (event) { event.preventDefault(); zone.classList.add("drag"); });
    });
    ["dragleave", "drop"].forEach(function (type) {
      zone.addEventListener(type, function (event) { event.preventDefault(); zone.classList.remove("drag"); });
    });
    zone.addEventListener("drop", function (event) {
      var file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
      if (file) loadFile(file);
    });
  }

  // ------------------------------------------------------------------ language

  function setLanguage(lang, persist) {
    I18n.setLang(lang);
    if (persist) { try { localStorage.setItem("nutev-open-lang", I18n.lang()); } catch (error) { /* storage unavailable */ } }
    document.querySelectorAll(".lang-switch button").forEach(function (button) {
      button.setAttribute("aria-pressed", button.getAttribute("data-lang") === I18n.lang() ? "true" : "false");
    });
    I18n.apply(document);
    setSearching($("search-btn").disabled);
    renderExamples();
    renderGuide();
    renderAll();
    if (state.query) updateHash();
  }

  // ------------------------------------------------------------------ drawers & theme

  var strategyReturnFocus = null;

  function openStrategy() {
    var panel = $("strategy");
    if (!state.plan || state.origin !== "search") return;
    strategyReturnFocus = document.activeElement;
    panel.hidden = false;
    panel.removeAttribute("inert");
    panel.setAttribute("aria-hidden", "false");
    document.body.classList.add("strategy-open");
    $("strategy-close").focus();
  }

  function closeStrategy() {
    var panel = $("strategy");
    document.body.classList.remove("strategy-open");
    panel.setAttribute("aria-hidden", "true");
    panel.setAttribute("inert", "");
    if (strategyReturnFocus && strategyReturnFocus.focus) strategyReturnFocus.focus();
  }

  function toggleTheme() {
    var root = document.documentElement;
    var current = root.getAttribute("data-theme");
    var systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var dark = current ? current === "dark" : systemDark;
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("nutev-open-theme", next); } catch (error) {}
  }

  // ------------------------------------------------------------------ init

  function init() {
    // On the hosted NutEV runtime this page lives at /aberto/; only there does the
    // login-protected advanced search exist on the same site.
    if (location.pathname.indexOf("/aberto/") === 0) $("advanced-link").hidden = false;
    bindTooltip();
    bindTabs();
    bindFile();
    var fromHash = readHash();
    var saved = "";
    try { saved = localStorage.getItem("nutev-open-lang") || ""; } catch (error) { saved = ""; }
    try {
      var savedTheme = localStorage.getItem("nutev-open-theme");
      if (savedTheme === "light" || savedTheme === "dark") document.documentElement.setAttribute("data-theme", savedTheme);
    } catch (error) {}
    renderSourcePicker();
    // On narrow screens the filters start closed so the first result is in view.
    if (window.matchMedia && window.matchMedia("(max-width: 860px)").matches) $("filters-details").open = false;
    setLanguage(fromHash.lang || saved || "pt", false);
    selectTab("results");

    $("search-form").addEventListener("submit", function (event) {
      event.preventDefault();
      runSearch($("q").value);
    });
    $("limit").addEventListener("change", function () { state.limit = Number($("limit").value) || 50; });
    $("sort").addEventListener("change", function () { state.sort = $("sort").value; state.shown = PAGE_SIZE; renderResults(); });
    $("show-more").addEventListener("click", function () { state.shown += PAGE_SIZE; renderResults(); });
    $("export-csv").addEventListener("click", exportCsv);
    $("export-json").addEventListener("click", exportJson);
    $("copy-link").addEventListener("click", copyLink);
    $("theme-toggle").addEventListener("click", toggleTheme);
    $("open-strategy").addEventListener("click", openStrategy);
    $("strategy-close").addEventListener("click", closeStrategy);
    $("strategy-scrim").addEventListener("click", closeStrategy);
    $("mobile-filter-btn").addEventListener("click", function () { document.body.classList.toggle("filters-open"); });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && document.body.classList.contains("strategy-open")) closeStrategy();
      if (event.key === "Escape" && document.body.classList.contains("filters-open")) document.body.classList.remove("filters-open");
    });
    $("brand-home").addEventListener("click", function (event) { event.preventDefault(); window.scrollTo({ top: 0, behavior: "smooth" }); $("q").focus(); });
    document.querySelectorAll(".lang-switch button").forEach(function (button) {
      button.addEventListener("click", function () { setLanguage(button.getAttribute("data-lang"), true); });
    });

    if (fromHash.query) {
      $("q").value = fromHash.query;
      runSearch(fromHash.query, { literal: fromHash.literal, strategy: fromHash.strategy });
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
