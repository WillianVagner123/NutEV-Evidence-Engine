/*
 * NutEV Open Evidence Explorer — classification core.
 *
 * Faithful browser port of the Reference Engine contracts:
 *   - src/nutev/reference_identity.py   (identifier normalization, identity, dedupe)
 *   - src/nutev/audit_guardrails.py     (traceability classes A/B/Q)
 *   - src/nutev/taxonomy.py             (_norm)
 *   - tools/rank_references.py          (score_record, ordering, taxonomy ranks)
 *   - src/nutev/search/classification.py (document class)
 *
 * Parity with Python is enforced by nutev_tests/test_open_explorer.py.
 * Nothing here judges methodological quality, eligibility, risk of bias,
 * certainty or recommendation strength.
 */
(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.NutEVOpenCore = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  // ---------------------------------------------------------------- Python-like helpers

  var PY_WHITESPACE = "\\t\\n\\x0b\\x0c\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
  var PY_STRIP_RE = new RegExp("^[" + PY_WHITESPACE + "]+|[" + PY_WHITESPACE + "]+$", "g");
  var PY_SPACE_RE = new RegExp("[" + PY_WHITESPACE + "]+", "g");

  function truthy(value) {
    if (value === null || value === undefined || value === false) return false;
    if (value === 0 || value === "" || (typeof value === "number" && isNaN(value))) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value).length > 0;
    return true;
  }

  /** Python `a or b` semantics. */
  function pyOr() {
    for (var i = 0; i < arguments.length; i += 1) {
      if (truthy(arguments[i])) return arguments[i];
    }
    return arguments.length ? arguments[arguments.length - 1] : undefined;
  }

  function pyRepr(value) {
    if (typeof value === "string") return "'" + value + "'";
    return pyText(value);
  }

  /** Python `str(value or "")`. */
  function pyText(value) {
    if (!truthy(value)) return "";
    if (value === true) return "True";
    if (Array.isArray(value)) return "[" + value.map(pyRepr).join(", ") + "]";
    if (typeof value === "object") {
      return "{" + Object.keys(value).map(function (key) {
        return pyRepr(key) + ": " + pyRepr(value[key]);
      }).join(", ") + "}";
    }
    return String(value);
  }

  function pyStrip(text) {
    return String(text).replace(PY_STRIP_RE, "");
  }

  function casefold(text) {
    return String(text).toLowerCase().replace(/ß/g, "ss").replace(/ſ/g, "s");
  }

  function stripMarks(text) {
    return text.replace(/\p{Mn}/gu, "");
  }

  function codePointLength(text) {
    var count = 0;
    for (var ch of String(text)) { count += ch ? 1 : 0; }
    return count;
  }

  function cmp(a, b) {
    return a < b ? -1 : a > b ? 1 : 0;
  }

  function cmpTuple(left, right) {
    for (var i = 0; i < Math.min(left.length, right.length); i += 1) {
      var result = cmp(left[i], right[i]);
      if (result) return result;
    }
    return left.length - right.length;
  }

  function round2(value) {
    return Math.round(value * 100) / 100;
  }

  // ---------------------------------------------------------------- text normalization

  /** src/nutev/taxonomy.py::_norm and tools/rank_references.py::_norm */
  function norm(value) {
    var text = stripMarks(casefold(pyText(value)).normalize("NFKD"));
    text = text.replace(/[^a-z0-9]+/g, " ");
    return pyStrip(text.replace(PY_SPACE_RE, " "));
  }

  /** src/nutev/search/classification.py::_normalized (keeps punctuation) */
  function normalizedLoose(value) {
    var text = stripMarks(casefold(pyText(value)).normalize("NFKD"));
    return pyStrip(text.replace(PY_SPACE_RE, " "));
  }

  // ---------------------------------------------------------------- identifiers

  var DOI_RE = /^10\.\d{4,9}\/\S+$/i;
  var PMID_RE = /^[0-9]{1,9}$/;
  var PMCID_RE = /^PMC[0-9]+$/i;
  var DOI_PREFIXES = ["https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"];

  function normalizeDoi(value) {
    var raw = pyStrip(pyText(value));
    if (!raw) return "";
    var lowered = casefold(raw);
    for (var i = 0; i < DOI_PREFIXES.length; i += 1) {
      if (lowered.indexOf(DOI_PREFIXES[i]) === 0) {
        raw = pyStrip(raw.slice(DOI_PREFIXES[i].length));
        break;
      }
    }
    raw = raw.replace(/[ .;,)\]}]+$/, "");
    if (!DOI_RE.test(raw)) return "";
    return casefold(raw);
  }

  function normalizePmid(value) {
    var raw = pyStrip(pyText(value));
    return raw && PMID_RE.test(raw) ? raw : "";
  }

  function normalizePmcid(value) {
    var raw = pyStrip(pyText(value));
    return raw && PMCID_RE.test(raw) ? raw.toUpperCase() : "";
  }

  var SCHEME_CHARS_RE = /^[A-Za-z0-9+\-.]+$/;
  var C0_OR_SPACE_RE = /^[\x00-\x20]+/;

  /** urllib.parse.urlsplit subset used by normalize_url; throws like Python on bad netlocs. */
  function urlsplit(input) {
    var url = String(input).replace(C0_OR_SPACE_RE, "").replace(/[\t\r\n]/g, "");
    var scheme = "";
    var netloc = "";
    var query = "";
    var colon = url.indexOf(":");
    if (colon > 0 && /^[A-Za-z]$/.test(url[0]) && SCHEME_CHARS_RE.test(url.slice(0, colon))) {
      scheme = url.slice(0, colon).toLowerCase();
      url = url.slice(colon + 1);
    }
    if (url.slice(0, 2) === "//") {
      var delim = url.length;
      ["/", "?", "#"].forEach(function (ch) {
        var found = url.indexOf(ch, 2);
        if (found >= 0) delim = Math.min(delim, found);
      });
      netloc = url.slice(2, delim);
      url = url.slice(delim);
      var open = netloc.indexOf("[") >= 0;
      var close = netloc.indexOf("]") >= 0;
      if (open !== close) throw new Error("Invalid IPv6 URL");
      if (open && close) {
        var host = netloc.slice(netloc.indexOf("[") + 1, netloc.indexOf("]"));
        if (!/^(v[0-9a-f]+\..+|[0-9a-f:.]+(%.+)?)$/i.test(host)) throw new Error("Invalid IPv6 URL");
      }
    }
    var hash = url.indexOf("#");
    if (hash >= 0) url = url.slice(0, hash);
    var question = url.indexOf("?");
    if (question >= 0) {
      query = url.slice(question + 1);
      url = url.slice(0, question);
    }
    if (/[^\x00-\x7f]/.test(netloc)) {
      var bare = netloc.replace(/[@:#?]/g, "");
      var nfkc = bare.normalize("NFKC");
      if (bare !== nfkc && /[\/?#@:]/.test(nfkc)) throw new Error("netloc contains invalid characters");
    }
    return { scheme: scheme, netloc: netloc, path: url, query: query };
  }

  function normalizeUrl(value) {
    var raw = pyStrip(pyText(value));
    if (!raw) return "";
    var parts;
    try {
      parts = urlsplit(raw);
    } catch (error) {
      return "";
    }
    var scheme = casefold(parts.scheme);
    if ((scheme !== "http" && scheme !== "https") || !parts.netloc) return "";
    var host = casefold(parts.netloc);
    if (host.indexOf("www.") === 0) host = host.slice(4);
    var path = parts.path.replace(/\/+$/, "") || "/";
    if (path.charAt(0) !== "/") path = "/" + path;
    return scheme + "://" + host + path + (parts.query ? "?" + parts.query : "");
  }

  function normalizeTitle(value) {
    var text = pyStrip(casefold(pyText(value).normalize("NFKC")));
    return text.replace(PY_SPACE_RE, " ");
  }

  function rowDoi(row) { return pyOr(row.doi, row.doi_normalized); }
  function rowPmid(row) { return pyOr(row.pmid, row.pmid_normalized); }
  function rowUrl(row) { return pyOr(row.url, row.url_normalized); }

  function validIdentifierKind(row) {
    if (normalizeDoi(rowDoi(row))) return "doi";
    if (normalizePmid(rowPmid(row))) return "pmid";
    if (normalizePmcid(row.pmcid)) return "pmcid";
    return "";
  }

  function canonicalIdentity(row) {
    var doi = normalizeDoi(rowDoi(row));
    if (doi) return "doi:" + doi;
    var pmid = normalizePmid(rowPmid(row));
    if (pmid) return "pmid:" + pmid;
    var url = normalizeUrl(rowUrl(row));
    if (url) return "url:" + casefold(url);
    var title = normalizeTitle(row.title);
    return title ? "title:" + title : "";
  }

  // ---------------------------------------------------------------- traceability (A/B/Q)

  var GUARDRAIL_POLICY_VERSION = "2026-08-18.2";

  function recordTraceability(row) {
    var provider = pyStrip(pyText(pyOr(row.source_provider, row.source)));
    var title = pyStrip(pyText(row.title));
    var reasons = [];
    if (!provider) reasons.push("missing_provider");
    if (!title) reasons.push("missing_title");
    if (reasons.length) return { traceability: "Q_INCOMPLETE_ORIGIN", reasons: reasons };

    var doiValue = rowDoi(row);
    var pmidValue = rowPmid(row);
    var pmcidValue = row.pmcid;
    var invalid = [];
    if (truthy(doiValue)) {
      if (normalizeDoi(doiValue)) return { traceability: "A_IDENTIFIER", reasons: ["doi"] };
      invalid.push("invalid_doi");
    }
    if (truthy(pmidValue)) {
      if (normalizePmid(pmidValue)) return { traceability: "A_IDENTIFIER", reasons: ["pmid"] };
      invalid.push("invalid_pmid");
    }
    if (truthy(pmcidValue)) {
      if (normalizePmcid(pmcidValue)) return { traceability: "A_IDENTIFIER", reasons: ["pmcid"] };
      invalid.push("invalid_pmcid");
    }
    if (normalizeUrl(rowUrl(row))) {
      return { traceability: "B_TRACEABLE_URL", reasons: ["url"].concat(invalid) };
    }
    if (invalid.length) return { traceability: "Q_INVALID_IDENTIFIER", reasons: invalid };
    return { traceability: "Q_UNTRACEABLE", reasons: ["no_valid_identifier_or_http_url"] };
  }

  function annotateRecord(row) {
    var result = recordTraceability(row);
    var annotated = Object.assign({}, row);
    annotated.audit_policy_version = GUARDRAIL_POLICY_VERSION;
    annotated.audit_traceability = result.traceability;
    annotated.audit_quarantined = result.traceability.indexOf("Q_") === 0;
    annotated.audit_reasons = result.reasons;
    return annotated;
  }

  // ---------------------------------------------------------------- dedupe (exact aliases)

  function exactIdentityAliases(row) {
    var aliases = [];
    function addFrom(value) {
      var doi = normalizeDoi(rowDoi(value));
      var pmid = normalizePmid(rowPmid(value));
      var pmcid = normalizePmcid(value.pmcid);
      var url = normalizeUrl(rowUrl(value));
      if (doi) aliases.push("doi:" + doi);
      if (pmid) aliases.push("pmid:" + pmid);
      if (pmcid) aliases.push("pmcid:" + casefold(pmcid));
      if (url) aliases.push("url:" + casefold(url));
    }
    addFrom(row);
    if (Array.isArray(row.source_manifestations)) {
      row.source_manifestations.forEach(function (item) {
        if (item && typeof item === "object" && !Array.isArray(item)) addFrom(item);
      });
    }
    if (aliases.length) return Array.from(new Set(aliases));
    var title = normalizeTitle(row.title);
    return title ? ["title:" + title] : [];
  }

  function providerName(row) {
    return pyStrip(pyText(pyOr(row.source_provider, row.provider, row.source)));
  }

  var MANIFESTATION_KEYS = ["provider", "source", "doi", "pmid", "pmcid", "url", "provider_query", "query_dialect", "retrieved_at"];

  function manifestation(row) {
    var item = {
      provider: providerName(row),
      source: pyStrip(pyText(row.source)),
      doi: normalizeDoi(rowDoi(row)),
      pmid: normalizePmid(rowPmid(row)),
      pmcid: normalizePmcid(row.pmcid),
      url: normalizeUrl(rowUrl(row)),
      provider_query: pyStrip(pyText(pyOr(row.provider_query, row.query))),
      query_dialect: pyStrip(pyText(row.query_dialect)),
      retrieved_at: pyStrip(pyText(pyOr(row.interactive_retrieved_at, row.retrieved_at)))
    };
    var out = {};
    MANIFESTATION_KEYS.forEach(function (key) { if (item[key]) out[key] = item[key]; });
    return out;
  }

  function manifestationKey(item) {
    return JSON.stringify(MANIFESTATION_KEYS.map(function (key) { return item[key] || ""; }));
  }

  function observedProvenance(rows) {
    var providers = new Set();
    var manifestations = new Map();
    rows.forEach(function (row) {
      if (Array.isArray(row.source_providers)) {
        row.source_providers.forEach(function (value) {
          var text = pyStrip(String(value));
          if (text) providers.add(text);
        });
      }
      if (Array.isArray(row.source_manifestations)) {
        row.source_manifestations.forEach(function (value) {
          if (!value || typeof value !== "object" || Array.isArray(value)) return;
          var normalized = manifestation(value);
          if (Object.keys(normalized).length) {
            if (normalized.provider) providers.add(normalized.provider);
            manifestations.set(manifestationKey(normalized), normalized);
          }
        });
      }
      var own = manifestation(row);
      if (Object.keys(own).length) {
        if (own.provider) providers.add(own.provider);
        manifestations.set(manifestationKey(own), own);
      }
    });
    var orderedProviders = Array.from(providers).sort(function (a, b) {
      return cmp(casefold(a), casefold(b));
    });
    var orderedManifestations = Array.from(manifestations.values()).sort(function (a, b) {
      function key(item) {
        return [casefold(item.provider || ""), item.doi || "", item.pmid || "", item.url || "", item.provider_query || ""];
      }
      return cmpTuple(key(a), key(b));
    });
    return { providers: orderedProviders, manifestations: orderedManifestations };
  }

  function withProvenance(record, observed) {
    var enriched = Object.assign({}, record);
    var provenance = observedProvenance([record].concat(observed || []));
    if (provenance.providers.length) enriched.source_providers = provenance.providers;
    if (provenance.manifestations.length) enriched.source_manifestations = provenance.manifestations;
    return enriched;
  }

  function strongIdentifiers(row) {
    var values = { doi: new Set(), pmid: new Set(), pmcid: new Set() };
    function addFrom(value) {
      var doi = normalizeDoi(rowDoi(value));
      var pmid = normalizePmid(rowPmid(value));
      var pmcid = normalizePmcid(value.pmcid);
      if (doi) values.doi.add(doi);
      if (pmid) values.pmid.add(pmid);
      if (pmcid) values.pmcid.add(pmcid);
    }
    addFrom(row);
    if (Array.isArray(row.source_manifestations)) {
      row.source_manifestations.forEach(function (item) {
        if (item && typeof item === "object" && !Array.isArray(item)) addFrom(item);
      });
    }
    return values;
  }

  function strongIdentityConflict(left, right) {
    var a = strongIdentifiers(left);
    var b = strongIdentifiers(right);
    return ["doi", "pmid", "pmcid"].some(function (kind) {
      if (!a[kind].size || !b[kind].size) return false;
      for (var value of a[kind]) { if (b[kind].has(value)) return false; }
      return true;
    });
  }

  function descriptiveText(row) {
    return pyText(pyOr(row.abstract, row.summary, row.snippet));
  }

  function mergeDescriptive(left, right) {
    var winner = codePointLength(descriptiveText(right)) > codePointLength(descriptiveText(left)) ? right : left;
    return withProvenance(Object.assign({}, winner), [left, right]);
  }

  function freshGroupKey(base, groups) {
    if (!groups.has(base)) return base;
    var index = 2;
    while (groups.has(base + "#conflict-" + index)) index += 1;
    return base + "#conflict-" + index;
  }

  function dedupeRecords(rows) {
    var groups = new Map();
    var aliasToGroups = new Map();
    var unkeyed = [];
    rows.forEach(function (raw) {
      var row = Object.assign({}, raw);
      var aliases = exactIdentityAliases(row);
      var canonical = canonicalIdentity(row) || (aliases.length ? aliases[0] : "");
      if (!aliases.length || !canonical) {
        unkeyed.push(withProvenance(row));
        return;
      }
      var candidateKeys = new Set();
      aliases.forEach(function (alias) {
        (aliasToGroups.get(alias) || new Set()).forEach(function (key) { candidateKeys.add(key); });
      });
      var candidates = Array.from(candidateKeys).filter(function (key) {
        return groups.has(key) && !strongIdentityConflict(groups.get(key), row);
      }).sort(cmp);
      var ambiguous = false;
      for (var i = 0; i < candidates.length && !ambiguous; i += 1) {
        for (var j = i + 1; j < candidates.length; j += 1) {
          if (strongIdentityConflict(groups.get(candidates[i]), groups.get(candidates[j]))) {
            ambiguous = true;
            break;
          }
        }
      }
      if (ambiguous) candidates = [];
      function mapAlias(alias, key) {
        if (!aliasToGroups.has(alias)) aliasToGroups.set(alias, new Set());
        aliasToGroups.get(alias).add(key);
      }
      if (!candidates.length) {
        var groupKey = freshGroupKey(canonical, groups);
        groups.set(groupKey, withProvenance(row));
        aliases.forEach(function (alias) { mapAlias(alias, groupKey); });
        return;
      }
      var target = candidates[0];
      var merged = groups.get(target);
      candidates.slice(1).forEach(function (other) {
        merged = mergeDescriptive(merged, groups.get(other));
        groups.delete(other);
        aliasToGroups.forEach(function (mapped) {
          if (mapped.has(other)) {
            mapped.delete(other);
            mapped.add(target);
          }
        });
      });
      merged = mergeDescriptive(merged, row);
      groups.set(target, merged);
      aliases.forEach(function (alias) { mapAlias(alias, target); });
    });
    return Array.from(groups.values()).concat(unkeyed);
  }

  function publicationTypeText(row) {
    return norm(pyOr(row.article_type, row.publication_type, row.type, row.work_type));
  }

  function isPreprint(row) {
    var type = publicationTypeText(row);
    var venue = norm(pyOr(row.journal, row.venue, row.container_title, row.source_name));
    return type.indexOf("preprint") >= 0 ||
      venue.indexOf("medrxiv") >= 0 ||
      venue.indexOf("biorxiv") >= 0 ||
      venue.indexOf("research square") >= 0 ||
      venue.indexOf("ssrn") >= 0;
  }

  function isBookChapter(row) {
    var type = publicationTypeText(row);
    return type.indexOf("book chapter") >= 0 ||
      type.indexOf("book chapter") >= 0 ||
      type.indexOf("bookchapter") >= 0 ||
      type.indexOf("chapter") === 0;
  }

  function firstAuthorKey(row) {
    var text = norm(row.authors);
    if (!text) return "";
    return text.split(/\s*(?:;|,|\band\b|\be\b)\s*/)[0].trim();
  }

  function preprintTitleKey(row) {
    var title = norm(row.title)
      .replace(/\bpreprint\b/g, " ")
      .replace(/\bversion\s+\d+\b/g, " ")
      .replace(/\bv\d+\b/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return title.length >= 32 ? title : "";
  }

  function mergePreprintPublication(preprint, published) {
    var merged = Object.assign({}, published);
    var preAbstract = descriptiveText(preprint);
    var pubAbstract = descriptiveText(published);
    if (codePointLength(preAbstract) > codePointLength(pubAbstract)) {
      if (preprint.abstract) merged.abstract = preprint.abstract;
      else if (preprint.summary) merged.summary = preprint.summary;
      else if (preprint.snippet) merged.snippet = preprint.snippet;
    }
    merged.preprint_publication_merged = true;
    return withProvenance(merged, [published, preprint]);
  }

  function dedupePreprintPublished(rows, nowYear) {
    var groups = new Map();
    var output = [];
    rows.forEach(function (row) {
      var key = preprintTitleKey(row);
      if (!key) { output.push(row); return; }
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(row);
    });
    groups.forEach(function (items) {
      if (items.length < 2) { output.push(items[0]); return; }
      var preprints = items.filter(isPreprint);
      var published = items.filter(function (row) { return !isPreprint(row); });
      if (!preprints.length || !published.length) {
        items.forEach(function (row) { output.push(row); });
        return;
      }
      var used = new Set();
      published.forEach(function (pub) {
        var pubAuthor = firstAuthorKey(pub);
        var pubYear = extractYear(pub, nowYear);
        var matchIndex = preprints.findIndex(function (pre, index) {
          if (used.has(index)) return false;
          var preAuthor = firstAuthorKey(pre);
          if (pubAuthor && preAuthor && pubAuthor !== preAuthor) return false;
          var preYear = extractYear(pre, nowYear);
          if (pubYear && preYear && Math.abs(pubYear - preYear) > 2) return false;
          return true;
        });
        if (matchIndex < 0) { output.push(pub); return; }
        used.add(matchIndex);
        output.push(mergePreprintPublication(preprints[matchIndex], pub));
      });
      preprints.forEach(function (pre, index) { if (!used.has(index)) output.push(pre); });
    });
    return output;
  }

  // ---------------------------------------------------------------- scoring (rank_references.py)

  function extractYear(row, nowYear) {
    var keys = ["year", "publication_year", "published_year", "publication_date", "date"];
    var re = /(?<![\p{L}\p{N}_])(19|20)\d{2}(?![\p{L}\p{N}_])/u;
    for (var i = 0; i < keys.length; i += 1) {
      var match = re.exec(pyText(row[keys[i]]));
      if (match) {
        var year = parseInt(match[0], 10);
        if (year >= 1900 && year <= nowYear + 1) return year;
      }
    }
    return null;
  }

  function providerBonus(provider, weights) {
    var normalized = norm(provider);
    var best = 0;
    Object.keys(weights).forEach(function (token) {
      if (normalized.indexOf(norm(token)) >= 0) best = Math.max(best, Number(weights[token]));
    });
    return best;
  }

  function orderedTaxonomyGroups(groupScores) {
    return Object.keys(groupScores).sort(function (a, b) {
      return (groupScores[b] - groupScores[a]) || cmp(a, b);
    });
  }

  function selectPrimaryTaxonomy(groupScores, order) {
    var ordered = orderedTaxonomyGroups(groupScores);
    if (!ordered.length) return { primary: "", secondary: [], dimensions: [] };
    var dimensions = [];
    ordered.forEach(function (group) {
      var dimension = group.split(".")[0];
      if (dimensions.indexOf(dimension) < 0) dimensions.push(dimension);
    });
    var primary = "";
    for (var i = 0; i < (order || []).length && !primary; i += 1) {
      primary = ordered.find(function (group) { return group.split(".")[0] === order[i]; }) || "";
    }
    if (!primary) primary = ordered[0];
    return {
      primary: primary,
      secondary: ordered.filter(function (group) { return group !== primary; }),
      dimensions: dimensions
    };
  }

  function documentTypeWeights(data) {
    return data.scoring.document_type_weights;
  }

  var QUESTION_RANKING_VERSION = "nutev-open-question-ranking-v1";
  var QUESTION_MISSING_PENALTY = 20;
  var QUESTION_MAX_SCORE = 50;
  var TAXONOMY_FINAL_CAP = 30;
  var DOCUMENT_CLASS_POINTS = {
    evidence_synthesis: 12,
    primary_randomized: 12,
    review: 8,
    primary_observational: 6,
    primary_qualitative: 5,
    guidance: 4,
    framework_implementation: 2,
    unclassified: 0
  };

  function questionRankingPolicy(data) {
    var scoring = (data && data.scoring) || {};
    var recencyMax = (scoring.recency || []).reduce(function (best, pair) {
      return Math.max(best, Number(pair && pair[1] || 0));
    }, 0);
    return {
      version: QUESTION_RANKING_VERSION,
      components: [
        { key: "question_answer", label_pt: "Responde à pergunta", max: QUESTION_MAX_SCORE, missing_penalty: QUESTION_MISSING_PENALTY },
        { key: "taxonomy", label_pt: "Temas NutEV", max: TAXONOMY_FINAL_CAP },
        { key: "document_type", label_pt: "Formato do estudo", max: 12 },
        { key: "identifier", label_pt: "Identificador verificável", max: Number(scoring.identifier || 0) },
        { key: "recency", label_pt: "Recência", max: recencyMax },
        { key: "penalties", label_pt: "Metadados ausentes", max: 0 },
        { key: "provider", label_pt: "Fonte", max: 0 },
        { key: "focus_keywords", label_pt: "Palavras-foco fixas", max: 0 }
      ],
      guardrail: "A ordem mede aderência à pergunta e prioridade de leitura. Não avalia qualidade metodológica, risco de viés, certeza ou recomendação."
    };
  }

  function cleanQuestionTerm(value) {
    return norm(value).replace(/\*/g, "").trim();
  }

  function containsQuestionTerm(text, rawTerm) {
    var term = cleanQuestionTerm(rawTerm);
    if (!term) return false;
    if (String(rawTerm || "").indexOf("*") >= 0 && term.indexOf(" ") < 0) {
      return text.split(" ").some(function (token) { return token.indexOf(term) === 0; });
    }
    return (" " + text + " ").indexOf(" " + term + " ") >= 0;
  }

  function evaluateQuestionParts(row, parts) {
    var title = norm(row.title);
    var abstract = norm(pyOr(row.abstract, row.summary, row.snippet));
    var evaluated = (parts || []).map(function (part, index) {
      var terms = (part.terms || []).map(function (term) {
        return typeof term === "string" ? term : pyText(term && term.text);
      }).filter(Boolean);
      var titleHits = terms.filter(function (term) { return containsQuestionTerm(title, term); });
      var abstractHits = terms.filter(function (term) {
        return titleHits.indexOf(term) < 0 && containsQuestionTerm(abstract, term);
      });
      return {
        id: pyText(part.id || part.key || ("part_" + (index + 1))),
        label: pyText(part.label || part.label_pt || part.label_en || ("Parte " + (index + 1))),
        role: pyText(part.role || ""),
        terms: terms.slice(0, 30),
        title_hits: titleHits.slice(0, 8),
        abstract_hits: abstractHits.slice(0, 8),
        matched: Boolean(titleHits.length || abstractHits.length)
      };
    });
    var matched = evaluated.filter(function (part) { return part.matched; }).length;
    return {
      parts: evaluated,
      matched: matched,
      total: evaluated.length,
      missing: evaluated.filter(function (part) { return !part.matched; }).map(function (part) { return part.label; }),
      all_parts: Boolean(evaluated.length) && matched === evaluated.length
    };
  }

  function questionScore(match) {
    if (!match || !match.total) return 0;
    var perPart = QUESTION_MAX_SCORE / match.total;
    var missing = match.total - match.matched;
    return round2((match.matched * perPart) - (missing * QUESTION_MISSING_PENALTY));
  }

  function finalDocumentTypeScore(row, data) {
    var cls = documentClass(row, data).document_class;
    return Number(DOCUMENT_CLASS_POINTS[cls] || 0);
  }

  function applyQuestionConditionedRanking(scored, parts, data) {
    var legacyBreakdown = Object.assign({}, scored.score_breakdown || {});
    var match = evaluateQuestionParts(scored, parts);
    var breakdown = {
      question_answer: questionScore(match),
      taxonomy: Math.min(TAXONOMY_FINAL_CAP, Math.max(0, Number(legacyBreakdown.taxonomy || 0))),
      focus_keywords: 0,
      document_type: finalDocumentTypeScore(scored, data),
      provider: 0,
      identifier: Number(legacyBreakdown.identifier || 0),
      recency: Number(legacyBreakdown.recency || 0),
      penalties: Number(legacyBreakdown.penalties || 0)
    };
    var finalScore = breakdown.question_answer + breakdown.taxonomy + breakdown.document_type +
      breakdown.identifier + breakdown.recency + breakdown.penalties;
    return Object.assign({}, scored, {
      legacy_reference_score: scored.reference_score,
      legacy_score_breakdown: legacyBreakdown,
      nutev_priority_score: scored.reference_score,
      reference_score: round2(finalScore),
      score_breakdown: breakdown,
      question_match: match,
      ranking_policy_version: QUESTION_RANKING_VERSION
    });
  }

  /**
   * Port of tools/rank_references.py::score_record. Returns the computed fields
   * merged over the input row (the Python version additionally filters input
   * fields to its public allowlist).
   */
  function scoreRecord(row, data, nowYear) {
    var scoring = data.scoring;
    var tax = scoring.taxonomy;
    var title = norm(row.title);
    var abstract = norm(pyOr(row.abstract, row.summary, row.snippet));
    var keywords = norm(pyOr(row.keywords, row.keyword, row.subjects));
    var provider = pyText(pyOr(row.source_provider, row.source));

    var matchedTerms = [];
    var groupScores = {};
    var groupTerms = {};
    var taxonomyRaw = 0;
    data.taxonomy.groups.forEach(function (group) {
      var hits = [];
      var groupScore = 0;
      for (var i = 0; i < group.terms.length; i += 1) {
        var term = group.terms[i];
        var termScore = 0;
        if (title.indexOf(term) >= 0) termScore += tax.title;
        if (keywords.indexOf(term) >= 0) termScore += tax.keywords;
        if (abstract.indexOf(term) >= 0) termScore += tax.abstract;
        if (termScore) {
          groupScore += Math.min(termScore, tax.term_cap);
          hits.push(term);
          if (hits.length >= tax.max_terms_per_group) break;
        }
      }
      if (hits.length) {
        groupScore += tax.group_bonus;
        taxonomyRaw += groupScore;
        groupScores[group.id] = round2(groupScore);
        groupTerms[group.id] = hits;
        matchedTerms = matchedTerms.concat(hits);
      }
    });
    var taxonomyScore = Math.min(taxonomyRaw, Math.max(0, scoring.taxonomy_score_cap || 0));
    var primary = selectPrimaryTaxonomy(groupScores, data.taxonomy.primary_dimension_order);
    var matchedGroups = orderedTaxonomyGroups(groupScores);

    var focusHits = [];
    var focusRaw = 0;
    scoring.focus_keywords.forEach(function (raw) {
      var term = norm(raw);
      if (!term) return;
      var hit = false;
      if (title.indexOf(term) >= 0) { focusRaw += scoring.focus.title; hit = true; }
      if (keywords.indexOf(term) >= 0) { focusRaw += scoring.focus.keywords; hit = true; }
      if (abstract.indexOf(term) >= 0) { focusRaw += scoring.focus.abstract; hit = true; }
      if (hit) focusHits.push(raw);
    });
    var focusScore = Math.min(focusRaw, Math.max(0, scoring.focus_score_cap || 0));

    var weights = documentTypeWeights(data);
    var typeHits = [];
    var documentTypeApplied = "";
    var documentScore = 0;
    weights.forEach(function (pair) {
      if (title.indexOf(pair[0]) >= 0) {
        typeHits.push(pair[0]);
        if (pair[1] > documentScore) {
          documentScore = pair[1];
          documentTypeApplied = pair[0];
        }
      }
    });

    var providerScore = providerBonus(provider, scoring.provider_weights);
    var identifierScore = validIdentifierKind(row) ? scoring.identifier : 0;
    var year = extractYear(row, nowYear);
    var recencyScore = 0;
    if (year) {
      var age = nowYear - year;
      for (var r = 0; r < scoring.recency.length; r += 1) {
        if (age <= scoring.recency[r][0]) {
          recencyScore = scoring.recency[r][1];
          break;
        }
      }
    }
    var penalties = 0;
    if (!title) penalties += scoring.penalties.missing_title;
    if (!abstract) penalties += scoring.penalties.missing_abstract;

    var score = taxonomyScore + focusScore + documentScore + providerScore + identifierScore + recencyScore + penalties;
    return Object.assign({}, row, {
      reference_score: round2(score),
      score_breakdown: {
        taxonomy: round2(taxonomyScore),
        taxonomy_raw_before_cap: round2(taxonomyRaw),
        focus_keywords: round2(focusScore),
        focus_raw_before_cap: round2(focusRaw),
        document_type: round2(documentScore),
        provider: round2(providerScore),
        identifier: round2(identifierScore),
        recency: round2(recencyScore),
        penalties: round2(penalties)
      },
      taxonomy_primary: primary.primary,
      taxonomy_secondary: primary.secondary.slice(0, 12),
      taxonomy_dimensions: primary.dimensions,
      taxonomy_groups: matchedGroups.slice(0, 20),
      taxonomy_group_scores: groupScores,
      taxonomy_group_terms: groupTerms,
      matched_terms: Array.from(new Set(matchedTerms)).sort(cmp).slice(0, 40),
      focus_keyword_hits: focusHits.slice(0, 20),
      document_type_hits: typeHits,
      document_type_applied: documentTypeApplied,
      reference_year: year,
      reference_provider: provider
    });
  }

  function sortRanked(rows) {
    return rows.sort(function (a, b) {
      return (Number(b.reference_score || 0) - Number(a.reference_score || 0)) ||
        (Number(b.reference_year || 0) - Number(a.reference_year || 0)) ||
        cmp(pyText(a.title), pyText(b.title));
    });
  }

  function assignTaxonomyRanks(rows) {
    var byGroup = {};
    rows.forEach(function (row) {
      (row.taxonomy_groups || []).forEach(function (group) {
        if (typeof group === "string" && group) (byGroup[group] = byGroup[group] || []).push(row);
      });
      row.taxonomy_ranks = {};
    });
    Object.keys(byGroup).sort(cmp).forEach(function (group) {
      byGroup[group].sort(function (a, b) {
        function groupScore(row) { return Number((row.taxonomy_group_scores || {})[group] || 0); }
        return (groupScore(b) - groupScore(a)) ||
          (Number(b.reference_score || 0) - Number(a.reference_score || 0)) ||
          (Number(b.reference_year || 0) - Number(a.reference_year || 0)) ||
          cmp(pyText(a.title), pyText(b.title));
      }).forEach(function (row, index) {
        row.taxonomy_ranks[group] = index + 1;
      });
    });
    rows.forEach(function (row) {
      row.taxonomy_primary_rank = row.taxonomy_primary ? row.taxonomy_ranks[row.taxonomy_primary] || null : null;
    });
  }

  // ---------------------------------------------------------------- document class (classification.py)

  function documentClass(row, data) {
    var articleType = normalizedLoose(pyOr(row.article_type, row.publication_type, row.type));
    var title = normalizedLoose(row.title);
    var abstract = normalizedLoose(pyOr(row.abstract, row.summary, row.snippet));
    var patterns = data.document_classes.patterns;
    var i;
    var j;
    for (i = 0; i < patterns.length; i += 1) {
      for (j = 0; j < patterns[i][1].length; j += 1) {
        if (articleType.indexOf(patterns[i][1][j]) >= 0) {
          return {
            document_class: patterns[i][0],
            confidence: "high",
            basis: "provider_article_type",
            signals: [{ field: "article_type", value: patterns[i][1][j] }]
          };
        }
      }
    }
    for (i = 0; i < patterns.length; i += 1) {
      var signals = [];
      for (j = 0; j < patterns[i][1].length; j += 1) {
        var pattern = patterns[i][1][j];
        if (title.indexOf(pattern) >= 0) signals.push({ field: "title", value: pattern });
        else if (abstract.indexOf(pattern) >= 0) signals.push({ field: "abstract", value: pattern });
      }
      if (signals.length) {
        return {
          document_class: patterns[i][0],
          confidence: "medium",
          basis: "title_abstract_text_signals",
          signals: signals.slice(0, 3)
        };
      }
    }
    return { document_class: "unclassified", confidence: "low", basis: "insufficient_signal", signals: [] };
  }

  // ---------------------------------------------------------------- metadata completeness (descriptive)

  var COMPLETENESS_FIELDS = ["title", "abstract", "year", "authors", "journal", "identifier"];

  function completeness(row, nowYear) {
    var present = {
      title: Boolean(norm(row.title)),
      abstract: Boolean(norm(pyOr(row.abstract, row.summary, row.snippet))),
      year: Boolean(extractYear(row, nowYear)),
      authors: Boolean(pyStrip(pyText(row.authors))),
      journal: Boolean(pyStrip(pyText(row.journal))),
      identifier: Boolean(validIdentifierKind(row))
    };
    var count = COMPLETENESS_FIELDS.filter(function (key) { return present[key]; }).length;
    return { fields: present, present: count, total: COMPLETENESS_FIELDS.length };
  }

  // ---------------------------------------------------------------- pipeline

  /**
   * SEARCH output -> TRACEABILITY GATE -> DEDUPLICATE -> CLASSIFY -> RANK.
   * Quarantined rows never enter the ranking (require_traceable_origin=true),
   * but they stay visible with their reasons.
   */
  function runPipeline(rawRows, data, options) {
    var nowYear = (options && options.nowYear) || new Date().getFullYear();
    var annotated = rawRows.map(annotateRecord);
    var eligible = annotated.filter(function (row) { return !row.audit_quarantined; });
    var quarantined = annotated.filter(function (row) { return row.audit_quarantined; });
    var exactUnique = dedupeRecords(eligible);
    var unique = dedupePreprintPublished(exactUnique, nowYear);
    var questionParts = options && Array.isArray(options.questionParts) ? options.questionParts : [];
    var ranked = sortRanked(unique.map(function (row) {
      var scored = scoreRecord(row, data, nowYear);
      return questionParts.length ? applyQuestionConditionedRanking(scored, questionParts, data) : scored;
    }));
    ranked.forEach(function (row, index) {
      row.reference_rank = index + 1;
      row.document_classification = documentClass(row, data);
      row.metadata_completeness = completeness(row, nowYear);
    });
    assignTaxonomyRanks(ranked);
    var quarantineView = quarantined.map(function (row) {
      var scored = scoreRecord(row, data, nowYear);
      return Object.assign({}, row, {
        taxonomy_primary: scored.taxonomy_primary,
        taxonomy_groups: scored.taxonomy_groups,
        taxonomy_group_terms: scored.taxonomy_group_terms,
        document_classification: documentClass(row, data),
        metadata_completeness: completeness(row, nowYear)
      });
    });
    return {
      annotated: annotated,
      ranked: ranked,
      quarantined: quarantineView,
      stats: summarize(annotated, ranked, quarantineView, data)
    };
  }

  function bump(map, key, by) {
    map[key] = (map[key] || 0) + (by || 1);
  }

  function traceabilityLevel(code) {
    if (code === "A_IDENTIFIER") return "A";
    if (code === "B_TRACEABLE_URL") return "B";
    return "Q";
  }

  function summarize(annotated, ranked, quarantined, data) {
    var bySource = {};
    annotated.forEach(function (row) {
      var source = providerName(row) || "(sem fonte)";
      var entry = bySource[source] = bySource[source] || { rows: 0, A: 0, B: 0, Q: 0 };
      entry.rows += 1;
      entry[traceabilityLevel(row.audit_traceability)] += 1;
    });

    var groupIndex = {};
    data.taxonomy.groups.forEach(function (group) { groupIndex[group.id] = group; });
    var byGroup = {};
    var levels = { A: 0, B: 0, Q: 0 };
    var classified = 0;
    var docClasses = {};
    var years = {};
    var fieldCounts = {};
    COMPLETENESS_FIELDS.forEach(function (field) { fieldCounts[field] = 0; });
    var works = ranked.concat(quarantined);
    works.forEach(function (row) {
      var level = traceabilityLevel(row.audit_traceability);
      levels[level] += 1;
      var groups = row.taxonomy_groups || [];
      if (groups.length) classified += 1;
      groups.forEach(function (group) {
        var entry = byGroup[group] = byGroup[group] || { group: group, family: (groupIndex[group] || {}).family, works: 0, A: 0, B: 0, Q: 0, with_abstract: 0, primary: 0 };
        entry.works += 1;
        entry[level] += 1;
        if (row.metadata_completeness && row.metadata_completeness.fields.abstract) entry.with_abstract += 1;
        if (row.taxonomy_primary === group) entry.primary += 1;
      });
      bump(docClasses, (row.document_classification || {}).document_class || "unclassified");
      var year = row.reference_year || null;
      if (year) bump(years, String(year));
      if (row.metadata_completeness) {
        COMPLETENESS_FIELDS.forEach(function (field) {
          if (row.metadata_completeness.fields[field]) fieldCounts[field] += 1;
        });
      }
    });
    return {
      retrieved_rows: annotated.length,
      unique_ranked: ranked.length,
      quarantined: quarantined.length,
      duplicates_merged: annotated.length - quarantined.length - ranked.length,
      preprint_publication_merged: ranked.filter(function (row) { return row.preprint_publication_merged; }).length,
      works: works.length,
      levels: levels,
      classified: classified,
      by_source: bySource,
      by_group: byGroup,
      document_classes: docClasses,
      years: years,
      completeness_fields: fieldCounts
    };
  }

  return {
    GUARDRAIL_POLICY_VERSION: GUARDRAIL_POLICY_VERSION,
    COMPLETENESS_FIELDS: COMPLETENESS_FIELDS,
    truthy: truthy,
    pyOr: pyOr,
    pyText: pyText,
    norm: norm,
    normalizedLoose: normalizedLoose,
    normalizeDoi: normalizeDoi,
    normalizePmid: normalizePmid,
    normalizePmcid: normalizePmcid,
    normalizeUrl: normalizeUrl,
    normalizeTitle: normalizeTitle,
    validIdentifierKind: validIdentifierKind,
    canonicalIdentity: canonicalIdentity,
    recordTraceability: recordTraceability,
    annotateRecord: annotateRecord,
    dedupeRecords: dedupeRecords,
    dedupePreprintPublished: dedupePreprintPublished,
    isPreprint: isPreprint,
    isBookChapter: isBookChapter,
    evaluateQuestionParts: evaluateQuestionParts,
    questionRankingPolicy: questionRankingPolicy,
    extractYear: extractYear,
    scoreRecord: scoreRecord,
    sortRanked: sortRanked,
    assignTaxonomyRanks: assignTaxonomyRanks,
    documentClass: documentClass,
    completeness: completeness,
    traceabilityLevel: traceabilityLevel,
    runPipeline: runPipeline,
    summarize: summarize
  };
});
