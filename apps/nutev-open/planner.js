/*
 * NutEV Open Evidence Explorer — question-to-strategy planner.
 *
 * Browser port of src/nutev/search/question_planner.py (parity enforced by
 * nutev_tests/test_question_planner.py). Deterministic: no language model and no
 * network. The question is organised into PICO-style concept blocks from the
 * curated vocabulary (config/query_vocabulary.json) and compiled into one query
 * per source, in that source's own syntax. MeSH/DeCS headings are never invented.
 */
(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module.exports) {
    module.exports = factory(require("./core.js"));
  } else {
    root.NutEVOpenPlanner = factory(root.NutEVOpenCore);
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function (Core) {
  "use strict";

  var PLANNER_VERSION = "nutev-question-planner-v1";
  var FIELD_MODES = ["title_abstract", "broad"];
  var LIVE_PROVIDERS = ["europepmc", "pubmed", "openalex", "crossref"];
  var LINK_PROVIDERS = ["bvs_lilacs", "scielo"];
  var ROLES = ["population", "intervention", "comparator", "context", "outcome", "design", "free"];
  var MAX_QUESTION_LENGTH = 500;
  var MAX_BLOCKS_WARNING = 5;
  var MAX_CROSSREF_WORDS = 14;

  var BOOLEAN_RE = /\b(AND|OR|NOT)\b|\[[A-Za-z /-]+\]|"|\b[A-Z_]{2,}:|\b(?:tw|mh|ti|ab|au):/;
  var NUMBER_WORDS = {
    um: 1, uma: 1, dois: 2, duas: 2, tres: 3, quatro: 4, cinco: 5, seis: 6,
    sete: 7, oito: 8, nove: 9, dez: 10, quinze: 15, vinte: 20,
    one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7,
    eight: 8, nine: 9, ten: 10, fifteen: 15, twenty: 20
  };
  var FROM_MARKERS = [["desde"], ["a", "partir", "de"], ["apos"], ["depois", "de"], ["since"], ["from"], ["after"]];
  var TO_MARKERS = [["ate"], ["until"], ["through"]];
  var BEFORE_MARKERS = [["antes", "de"], ["before"]];
  var RANGE_START = [["entre"], ["between"], ["de"], ["from"]];
  var RANGE_JOIN = [["e"], ["and"], ["a"], ["to"], ["ate"]];
  var LAST_MARKERS = [["ultimos"], ["nos", "ultimos"], ["last"], ["past"], ["the", "last"], ["the", "past"]];
  var YEAR_UNITS = ["anos", "ano", "years", "year"];

  function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

  function cmpTuple(left, right) {
    for (var i = 0; i < Math.min(left.length, right.length); i += 1) {
      var result = cmp(left[i], right[i]);
      if (result) return result;
    }
    return left.length - right.length;
  }

  function casefold(text) {
    return String(text).toLowerCase().replace(/ß/g, "ss");
  }

  function stem(token) {
    return token.length > 4 && token.charAt(token.length - 1) === "s" ? token.slice(0, -1) : token;
  }

  function tokensOf(text) {
    var normalized = Core.norm(text);
    return normalized ? normalized.split(" ") : [];
  }

  function isDigits(token) { return /^[0-9]+$/.test(token); }

  function queryString(params) {
    return Object.keys(params).map(function (key) {
      return encodeURIComponent(key) + "=" + encodeURIComponent(params[key]);
    }).join("&");
  }

  function looksLikeBoolean(question) {
    return BOOLEAN_RE.test(question);
  }

  function matchAt(tokens, index, sequence) {
    if (index + sequence.length > tokens.length) return false;
    for (var k = 0; k < sequence.length; k += 1) {
      if (tokens[index + k] !== sequence[k]) return false;
    }
    return true;
  }

  function anyConsumed(consumed, start, end) {
    for (var k = start; k < end; k += 1) { if (consumed[k]) return true; }
    return false;
  }

  function yearValue(token, currentYear) {
    if (token && token.length === 4 && isDigits(token)) {
      var year = parseInt(token, 10);
      if (year >= 1900 && year <= currentYear + 1) return year;
    }
    return null;
  }

  function extractYears(tokens, consumed, currentYear) {
    var yearFrom = null;
    var yearTo = null;
    var n = tokens.length;
    function free(start, end) { return end <= n && !anyConsumed(consumed, start, end); }
    function take(start, end) { for (var k = start; k < end; k += 1) consumed[k] = true; }

    var i = 0;
    while (i < n) {
      var handled = false;
      var m;
      var marker;
      var end;
      for (m = 0; m < LAST_MARKERS.length; m += 1) {
        marker = LAST_MARKERS[m];
        end = i + marker.length;
        if (free(i, end + 2) && matchAt(tokens, i, marker) && YEAR_UNITS.indexOf(tokens[end + 1]) >= 0) {
          var raw = tokens[end];
          var amount = isDigits(raw) ? parseInt(raw, 10) : (Object.prototype.hasOwnProperty.call(NUMBER_WORDS, raw) ? NUMBER_WORDS[raw] : null);
          if (amount && amount > 0 && amount <= 100) {
            yearFrom = currentYear - amount;
            take(i, end + 2);
            i = end + 2;
            handled = true;
            break;
          }
        }
      }
      if (handled) continue;
      for (m = 0; m < RANGE_START.length && !handled; m += 1) {
        marker = RANGE_START[m];
        end = i + marker.length;
        if (!(free(i, end + 1) && matchAt(tokens, i, marker))) continue;
        var first = end < n ? yearValue(tokens[end], currentYear) : null;
        if (first === null) continue;
        for (var j = 0; j < RANGE_JOIN.length; j += 1) {
          var join = RANGE_JOIN[j];
          var joinEnd = end + 1 + join.length;
          if (free(end + 1, joinEnd + 1) && matchAt(tokens, end + 1, join) && joinEnd < n) {
            var second = yearValue(tokens[joinEnd], currentYear);
            if (second !== null) {
              yearFrom = Math.min(first, second);
              yearTo = Math.max(first, second);
              take(i, joinEnd + 1);
              i = joinEnd + 1;
              handled = true;
              break;
            }
          }
        }
      }
      if (handled) continue;
      var groups = [[FROM_MARKERS, "from"], [TO_MARKERS, "to"], [BEFORE_MARKERS, "before"]];
      for (var g = 0; g < groups.length && !handled; g += 1) {
        for (m = 0; m < groups[g][0].length; m += 1) {
          marker = groups[g][0][m];
          end = i + marker.length;
          if (free(i, end + 1) && matchAt(tokens, i, marker) && end < n) {
            var year = yearValue(tokens[end], currentYear);
            if (year === null) continue;
            if (groups[g][1] === "from") yearFrom = year;
            else if (groups[g][1] === "to") yearTo = year;
            else yearTo = year - 1;
            take(i, end + 1);
            i = end + 1;
            handled = true;
            break;
          }
        }
      }
      if (handled) continue;
      var a = !consumed[i] ? yearValue(tokens[i], currentYear) : null;
      var b = i + 1 < n && !consumed[i + 1] ? yearValue(tokens[i + 1], currentYear) : null;
      if (a !== null && b !== null) {
        yearFrom = Math.min(a, b);
        yearTo = Math.max(a, b);
        take(i, i + 2);
        i += 2;
        continue;
      }
      i += 1;
    }
    return [yearFrom, yearTo];
  }

  function triggerIndex(vocabulary) {
    var index = new Map();
    vocabulary.concepts.forEach(function (concept) {
      concept.triggers.forEach(function (trigger) {
        var key = tokensOf(trigger).map(stem);
        if (!key.length) return;
        if (!index.has(key[0])) index.set(key[0], []);
        var entries = index.get(key[0]);
        var exists = entries.some(function (entry) { return entry[1] === concept.id && cmpTuple(entry[0], key) === 0; });
        if (!exists) entries.push([key, concept.id]);
      });
    });
    index.forEach(function (entries) {
      entries.sort(function (x, y) { return (y[0].length - x[0].length) || cmp(x[1], y[1]); });
    });
    return index;
  }

  function markerList(raw) {
    return raw.map(tokensOf).filter(function (m) { return m.length; })
      .sort(function (x, y) { return (y.length - x.length) || cmpTuple(x, y); });
  }

  function dedupeTerms(terms) {
    var seen = new Set();
    return terms.filter(function (term) {
      var key = term.lang + "\u0000" + casefold(term.text);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  /**
   * Build an editable, explainable plan. options: { currentYear, taxonomyGroups, detectManual }
   * taxonomyGroups: { groupId: [normalized terms] } in canonical order.
   */
  function planQuestion(question, vocabulary, options) {
    var opts = options || {};
    var currentYear = opts.currentYear;
    var text = Array.from(String(question === null || question === undefined ? "" : question).replace(/\s+/g, " ").trim())
      .slice(0, MAX_QUESTION_LENGTH).join("");
    var base = {
      planner_version: PLANNER_VERSION,
      vocabulary_version: vocabulary.vocabulary_version,
      question: text,
      normalized: Core.norm(text),
      mode: "planned",
      year_from: null,
      year_to: null,
      blocks: [],
      dropped_terms: [],
      warnings: []
    };
    if (!text) {
      base.warnings.push({ code: "empty_question" });
      return base;
    }
    if (opts.detectManual !== false && looksLikeBoolean(text)) {
      base.mode = "manual";
      base.warnings.push({ code: "manual_string" });
      return base;
    }

    var tokens = tokensOf(text);
    var stems = tokens.map(stem);
    var consumed = tokens.map(function () { return false; });
    var years = extractYears(tokens, consumed, currentYear);
    base.year_from = years[0];
    base.year_to = years[1];

    var concepts = {};
    vocabulary.concepts.forEach(function (concept) { concepts[concept.id] = concept; });
    var index = triggerIndex(vocabulary);
    var stopwords = new Set();
    Object.keys(vocabulary.stopwords || {}).forEach(function (lang) {
      vocabulary.stopwords[lang].forEach(function (word) { stopwords.add(Core.norm(word)); });
    });
    var comparatorMarkers = markerList(vocabulary.comparator_markers || []);

    var markerEnds = new Set();
    var position;
    var k;
    for (position = 0; position < tokens.length; position += 1) {
      if (consumed[position]) continue;
      for (k = 0; k < comparatorMarkers.length; k += 1) {
        var marker = comparatorMarkers[k];
        var markerEnd = position + marker.length;
        if (matchAt(tokens, position, marker) && !anyConsumed(consumed, position, markerEnd)) {
          for (var covered = position; covered < markerEnd; covered += 1) consumed[covered] = true;
          markerEnds.add(markerEnd);
          break;
        }
      }
    }

    var matches = [];
    var i = 0;
    while (i < tokens.length) {
      if (consumed[i]) { i += 1; continue; }
      var found = null;
      var entries = index.get(stems[i]) || [];
      for (k = 0; k < entries.length; k += 1) {
        var key = entries[k][0];
        var end = i + key.length;
        if (matchAt(stems, i, key) && !anyConsumed(consumed, i, end)) {
          found = [end, entries[k][1]];
          break;
        }
      }
      if (!found) { i += 1; continue; }
      var probe = i;
      while (probe > 0 && !markerEnds.has(probe) && stopwords.has(tokens[probe - 1]) && !consumed[probe - 1]) probe -= 1;
      matches.push({
        concept_id: found[1],
        start: i,
        text: tokens.slice(i, found[0]).join(" "),
        comparator: markerEnds.has(probe)
      });
      for (k = i; k < found[0]; k += 1) consumed[k] = true;
      i = found[0];
    }

    var runs = [];
    var dropped = [];
    var current = [];
    var currentStart = 0;
    tokens.forEach(function (token, pos) {
      var keep = !consumed[pos] && !stopwords.has(token) && !isDigits(token) && token.length >= 3;
      if (keep) {
        if (!current.length) currentStart = pos;
        current.push(token);
        return;
      }
      if (!consumed[pos]) dropped.push(token);
      if (current.length) {
        runs.push([currentStart, current.join(" ")]);
        current = [];
      }
    });
    if (current.length) runs.push([currentStart, current.join(" ")]);
    base.dropped_terms = dropped;

    var mergeRoles = new Set(vocabulary.merge_roles || []);
    var blocks = new Map();
    var order = [];
    matches.forEach(function (match) {
      var concept = concepts[match.concept_id];
      var role = match.comparator ? "comparator" : concept.role;
      var blockKey = mergeRoles.has(role) ? role : role + ":" + (concept.merge_key || concept.id);
      var block = blocks.get(blockKey);
      if (!block) {
        block = {
          key: blockKey, role: role, concept_ids: [], labels_pt: [], labels_en: [], matched: [],
          taxonomy_groups: [], enabled: true, terms: [], pubmed_filters: [], source: "vocabulary",
          position: match.start, _defaults: []
        };
        blocks.set(blockKey, block);
        order.push(blockKey);
      }
      if (block.concept_ids.indexOf(concept.id) < 0) {
        block.concept_ids.push(concept.id);
        block.labels_pt.push(concept.label_pt);
        block.labels_en.push(concept.label_en);
        block._defaults.push(concept.default_enabled === undefined ? true : Boolean(concept.default_enabled));
        var group = concept.taxonomy_group;
        if (group && block.taxonomy_groups.indexOf(group) < 0) block.taxonomy_groups.push(group);
        concept.en.forEach(function (t) { block.terms.push({ text: t, lang: "en" }); });
        (concept.pt || []).forEach(function (t) { block.terms.push({ text: t, lang: "pt" }); });
        (concept.pubmed_filters || []).forEach(function (item) {
          if (block.pubmed_filters.indexOf(item) < 0) block.pubmed_filters.push(item);
        });
      }
      if (block.matched.indexOf(match.text) < 0) block.matched.push(match.text);
    });

    var taxonomyTerms = [];
    var taxonomyGroups = opts.taxonomyGroups || {};
    Object.keys(taxonomyGroups).forEach(function (group) {
      taxonomyGroups[group].forEach(function (term) {
        if (term.length >= 4) taxonomyTerms.push([term, group]);
      });
    });
    taxonomyTerms.sort(function (x, y) { return (y[0].length - x[0].length) || cmp(x[0], y[0]) || cmp(x[1], y[1]); });

    runs.forEach(function (run) {
      var runKey = "free:" + run[1];
      if (blocks.has(runKey)) return;
      var hit = taxonomyTerms.find(function (entry) { return (" " + run[1] + " ").indexOf(" " + entry[0] + " ") >= 0; });
      blocks.set(runKey, {
        key: runKey, role: "free", concept_ids: [], labels_pt: [run[1]], labels_en: [run[1]], matched: [run[1]],
        taxonomy_groups: hit ? [hit[1]] : [], enabled: true, terms: [{ text: run[1], lang: "any" }],
        pubmed_filters: [], source: "free_text", position: run[0], _defaults: [true]
      });
      order.push(runKey);
    });

    var roleOrder = {};
    ROLES.forEach(function (role) { roleOrder[role] = Number(vocabulary.roles[role].order); });
    var output = order.slice().sort(function (x, y) {
      var bx = blocks.get(x);
      var by = blocks.get(y);
      return (roleOrder[bx.role] - roleOrder[by.role]) || (bx.position - by.position) || cmp(x, y);
    }).map(function (blockKey) {
      var block = blocks.get(blockKey);
      var defaults = block._defaults;
      delete block._defaults;
      block.enabled = block.role !== "comparator" && defaults.some(Boolean);
      block.terms = dedupeTerms(block.terms);
      block.label_pt = block.labels_pt.join(" / ");
      block.label_en = block.labels_en.join(" / ");
      delete block.labels_pt;
      delete block.labels_en;
      return block;
    });
    base.blocks = output;

    var warnings = base.warnings;
    if (!output.length) warnings.push({ code: "nothing_recognised" });
    else if (output.every(function (block) { return block.source === "free_text"; })) warnings.push({ code: "no_vocabulary_concepts" });
    output.forEach(function (block) {
      if (block.role === "comparator") warnings.push({ code: "comparator_disabled", block: block.key });
      else if (!block.enabled) warnings.push({ code: "default_disabled", block: block.key });
    });
    var enabledCount = output.filter(function (block) { return block.enabled; }).length;
    if (enabledCount > MAX_BLOCKS_WARNING) warnings.push({ code: "many_blocks", count: enabledCount });
    return base;
  }

  // ---------------------------------------------------------------------------- compilation

  function clean(text) {
    return String(text).replace(/"/g, " ").replace(/,/g, " ").replace(/\s+/g, " ").trim();
  }

  function isTruncated(text) {
    return text.charAt(text.length - 1) === "*" && text.indexOf(" ") < 0 && text.length >= 5;
  }

  function rstripStar(text) { return text.replace(/\*+$/, ""); }

  function formatTerm(text, provider, fieldMode) {
    var cleaned = clean(text);
    if (!cleaned) return "";
    var truncated = isTruncated(cleaned);
    var bare = truncated ? cleaned : rstripStar(cleaned);
    if (provider === "pubmed") {
      if (fieldMode === "title_abstract") return truncated ? cleaned + "[tiab]" : "\"" + bare + "\"[tiab]";
      return truncated ? cleaned : (bare.indexOf(" ") >= 0 ? "(" + bare + ")" : bare);
    }
    if (provider === "europepmc") {
      if (fieldMode === "title_abstract") return truncated ? "TITLE_ABS:" + cleaned : "TITLE_ABS:\"" + bare + "\"";
      return truncated ? cleaned : "\"" + bare + "\"";
    }
    if (provider === "openalex" || provider === "scielo") {
      if (provider === "scielo" && truncated) return cleaned.slice(0, -1) + "$";
      var word = rstripStar(cleaned);
      return word.indexOf(" ") >= 0 ? "\"" + word + "\"" : word;
    }
    if (provider === "bvs_lilacs") {
      if (truncated) return "tw:" + cleaned.slice(0, -1) + "$";
      return "tw:\"" + bare + "\"";
    }
    return bare;
  }

  function blockTerms(block, provider, includePt) {
    var regional = LINK_PROVIDERS.indexOf(provider) >= 0;
    var selected = [];
    block.terms.forEach(function (term) {
      if (term.enabled === false) return;
      if (term.lang === "pt" && !(regional || includePt)) return;
      selected.push(term.text);
    });
    if (regional) {
      var ptFirst = block.terms.filter(function (t) { return t.lang === "pt" && t.enabled !== false; }).map(function (t) { return t.text; });
      var others = selected.filter(function (text) { return ptFirst.indexOf(text) < 0; });
      selected = ptFirst.concat(others);
    }
    return selected;
  }

  function compileBoolean(blocks, provider, fieldMode, includePt) {
    var parts = [];
    blocks.forEach(function (block) {
      var formatted = [];
      blockTerms(block, provider, includePt).forEach(function (text) {
        var item = formatTerm(text, provider, fieldMode);
        if (item && formatted.indexOf(item) < 0) formatted.push(item);
      });
      if (provider === "pubmed") {
        (block.pubmed_filters || []).forEach(function (item) {
          if (formatted.indexOf(item) < 0) formatted.push(item);
        });
      }
      if (formatted.length) parts.push("(" + formatted.join(" OR ") + ")");
    });
    return parts.join(" AND ");
  }

  function crossrefKeywords(blocks) {
    var words = [];
    blocks.forEach(function (block) {
      var picked = block.terms.filter(function (t) { return t.lang !== "pt" && t.enabled !== false; }).slice(0, 2).map(function (t) { return t.text; });
      picked.forEach(function (text) {
        rstripStar(clean(text)).split(" ").forEach(function (raw) {
          var word = rstripStar(raw);
          var folded = words.map(casefold);
          if (word && folded.indexOf(casefold(word)) < 0) words.push(word);
        });
      });
    });
    return words.slice(0, MAX_CROSSREF_WORDS).join(" ");
  }

  /** options: { fieldMode, includePt, currentYear } */
  function compileQueries(plan, options) {
    var opts = options || {};
    var fieldMode = opts.fieldMode || "title_abstract";
    if (FIELD_MODES.indexOf(fieldMode) < 0) throw new Error("field_mode must be one of " + FIELD_MODES.join(", "));
    var includePt = Boolean(opts.includePt);
    var currentYear = opts.currentYear;
    var yearFrom = plan.year_from || null;
    var yearTo = plan.year_to || null;
    var enabled = (plan.blocks || []).filter(function (block) { return block.enabled; });
    var manual = plan.mode === "manual";
    var providers = {};

    function boolean(provider) {
      return manual ? String(plan.question || "") : compileBoolean(enabled, provider, fieldMode, includePt);
    }

    var pubmed = boolean("pubmed");
    if (pubmed && !manual && (yearFrom || yearTo)) pubmed += " AND (" + (yearFrom || 1800) + ":" + (yearTo || 3000) + "[dp])";
    providers.pubmed = {
      query: pubmed,
      params: { sort: "relevance" },
      dialect: manual ? "pubmed_manual" : "pubmed_" + fieldMode,
      site_url: pubmed ? "https://pubmed.ncbi.nlm.nih.gov/?" + queryString({ term: pubmed }) : "",
      notes: fieldMode === "broad" && !manual ? ["pubmed_automatic_term_mapping"] : []
    };

    var europepmc = boolean("europepmc");
    if (europepmc && !manual && (yearFrom || yearTo)) europepmc += " AND (PUB_YEAR:[" + (yearFrom || 1800) + " TO " + (yearTo || currentYear + 1) + "])";
    var epmcParams = fieldMode === "broad" && !manual ? { synonym: "true" } : {};
    providers.europepmc = {
      query: europepmc,
      params: epmcParams,
      dialect: manual ? "europepmc_manual" : "europepmc_" + fieldMode,
      site_url: europepmc ? "https://europepmc.org/search?" + queryString({ query: europepmc }) : "",
      notes: Object.keys(epmcParams).length ? ["europepmc_synonyms"] : []
    };

    var openalex = boolean("openalex");
    var openalexFilters = [];
    if (yearFrom) openalexFilters.push("from_publication_date:" + yearFrom + "-01-01");
    if (yearTo) openalexFilters.push("to_publication_date:" + yearTo + "-12-31");
    var openalexParams = openalexFilters.length ? { filter: openalexFilters.join(",") } : {};
    providers.openalex = {
      query: openalex,
      params: openalexParams,
      dialect: manual ? "openalex_manual" : "openalex_search_boolean",
      site_url: openalex ? "https://api.openalex.org/works?" + queryString(Object.assign({ search: openalex }, openalexParams)) : "",
      notes: ["openalex_no_truncation_fulltext"]
    };

    var crossref = manual ? String(plan.question || "") : crossrefKeywords(enabled);
    var crossrefFilters = [];
    if (yearFrom) crossrefFilters.push("from-pub-date:" + yearFrom);
    if (yearTo) crossrefFilters.push("until-pub-date:" + yearTo);
    var crossrefParams = crossrefFilters.length ? { filter: crossrefFilters.join(",") } : {};
    providers.crossref = {
      query: crossref,
      params: crossrefParams,
      dialect: manual ? "crossref_manual" : "crossref_relevance_keywords",
      site_url: crossref ? "https://api.crossref.org/works?" + queryString(Object.assign({ "query.bibliographic": crossref }, crossrefParams)) : "",
      notes: ["crossref_no_boolean"]
    };

    var bvs = boolean("bvs_lilacs");
    providers.bvs_lilacs = {
      query: bvs,
      params: {},
      dialect: manual ? "bvs_manual" : "bvs_tw_pt_en",
      site_url: bvs ? "https://pesquisa.bvsalud.org/portal/?" + queryString({ lang: "pt", q: bvs, "filter[db_cluster][]": "LILACS" }) : "",
      notes: yearFrom || yearTo ? ["link_only", "years_on_site"] : ["link_only"]
    };

    var scielo = boolean("scielo");
    providers.scielo = {
      query: scielo,
      params: {},
      dialect: manual ? "scielo_manual" : "scielo_boolean_pt_en",
      site_url: scielo ? "https://search.scielo.org/?" + queryString({ lang: "pt", q: scielo }) : "",
      notes: yearFrom || yearTo ? ["link_only", "years_on_site"] : ["link_only"]
    };

    return {
      field_mode: fieldMode,
      include_pt: includePt,
      manual: manual,
      logic: enabled.map(function (block) { return "(" + block.label_en + ")"; }).join(" AND "),
      providers: providers
    };
  }

  /** Canonical taxonomy terms per group, as the planner expects them. */
  function taxonomyTermsFromBundle(data) {
    var groups = {};
    data.taxonomy.groups.forEach(function (group) { groups[group.id] = group.terms; });
    return groups;
  }

  return {
    PLANNER_VERSION: PLANNER_VERSION,
    FIELD_MODES: FIELD_MODES,
    LIVE_PROVIDERS: LIVE_PROVIDERS,
    LINK_PROVIDERS: LINK_PROVIDERS,
    ROLES: ROLES,
    stem: stem,
    tokensOf: tokensOf,
    looksLikeBoolean: looksLikeBoolean,
    planQuestion: planQuestion,
    compileQueries: compileQueries,
    taxonomyTermsFromBundle: taxonomyTermsFromBundle
  };
});
