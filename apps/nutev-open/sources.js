/*
 * NutEV Open Evidence Explorer — open bibliographic sources.
 *
 * Every request goes from the visitor's browser straight to the public API of
 * the source. There is no NutEV server in the middle, no login and no API key.
 * Failures, rate limits and partial responses stay explicit in the status of
 * each source; nothing is filled in, repaired or simulated.
 *
 * Normalizers mirror src/nutev/search/{europepmc,openalex,crossref,pubmed}.py.
 * Documented browser differences: Europe PMC uses resultType=core (abstracts,
 * author keywords), OpenAlex abstracts are rebuilt in reading order from the
 * inverted index and OpenAlex PMIDs are kept, HTML/JATS markup is removed from
 * titles and abstracts.
 */
(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.NutEVOpenSources = factory();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var TOOL = "nutev_open_explorer";
  var YEAR_RE = /\b(19|20)\d{2}\b/;

  var ENTITIES = { amp: "&", lt: "<", gt: ">", quot: "\"", apos: "'", nbsp: " " };
  var INLINE_TAGS = /<\/?(?:i|b|em|strong|sup|sub|u|sc|span|small|mml:[a-z]+|jats:(?:italic|bold|sup|sub|sc|underline|monospace))(?:\s[^>]*)?>/gi;

  function clean(value) {
    if (value === null || value === undefined) return "";
    return String(value).trim();
  }

  function decodeEntities(text) {
    return text.replace(/&(#x[0-9a-f]+|#[0-9]+|[a-z]+);/gi, function (match, code) {
      if (code[0] === "#") {
        var point = code[1] === "x" || code[1] === "X" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
        try { return String.fromCodePoint(point); } catch (error) { return match; }
      }
      var named = ENTITIES[code.toLowerCase()];
      return named === undefined ? match : named;
    });
  }

  /** Remove HTML/JATS markup so titles and abstracts are plain text. */
  function plainText(value) {
    var text = clean(value);
    if (!text) return "";
    text = text.replace(INLINE_TAGS, "").replace(/<[^>]*>/g, " ");
    return decodeEntities(text).replace(/\s+/g, " ").trim();
  }

  function extractYear() {
    for (var i = 0; i < arguments.length; i += 1) {
      var match = YEAR_RE.exec(clean(arguments[i]));
      if (match) return match[0];
    }
    return "";
  }

  function lastPathSegment(value) {
    var text = clean(value);
    return text ? text.split("/").pop() : "";
  }

  function stamp(row, query, retrievedAt) {
    row.query = query;
    row.provider_query = query;
    row.retrieved_at = retrievedAt;
    return row;
  }

  // ------------------------------------------------------------------ Europe PMC

  function normalizeEuropePmcPmcid(value) {
    var raw = clean(value);
    if (!raw) return "";
    if (raw.toUpperCase().indexOf("PMC") === 0) return raw.toUpperCase();
    if (/^\d+$/.test(raw)) return "PMC" + raw;
    return raw;
  }

  function pickEuropePmcUrl(item) {
    var pmcid = normalizeEuropePmcPmcid(item.pmcid);
    if (pmcid) return "https://pmc.ncbi.nlm.nih.gov/articles/" + pmcid + "/";
    var fullText = item.fullTextUrlList || {};
    var entries = fullText && typeof fullText === "object" ? fullText.fullTextUrl || [] : [];
    if (!Array.isArray(entries)) entries = [entries];
    var best = "";
    for (var i = 0; i < entries.length; i += 1) {
      var url = clean(entries[i] && entries[i].url);
      if (!url) continue;
      if (!best) best = url;
      var lower = url.toLowerCase();
      if (lower.slice(-4) === ".pdf" || lower.indexOf("/pdf") >= 0) return url;
      if (lower.indexOf("pmc.ncbi.nlm.nih.gov") >= 0) return url;
    }
    if (best) return best;
    var doi = clean(item.doi).replace(/^doi:/, "").trim();
    if (doi) return "https://doi.org/" + doi;
    var pmid = clean(item.pmid);
    if (pmid) return "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/";
    return "";
  }

  function europePmcArticleType(item) {
    if (item.pubType) return clean(item.pubType);
    var list = item.pubTypeList && item.pubTypeList.pubType;
    if (Array.isArray(list)) return list.map(clean).filter(Boolean).join("; ");
    return clean(list || item.resultType);
  }

  function normalizeEuropePmc(item, query, retrievedAt) {
    var journalInfo = item.journalInfo || {};
    var keywords = (item.keywordList && item.keywordList.keyword) || [];
    return stamp({
      source: "europepmc",
      source_provider: "europepmc",
      title: plainText(item.title),
      abstract: plainText(item.abstractText),
      doi: clean(item.doi),
      pmid: clean(item.pmid),
      pmcid: normalizeEuropePmcPmcid(item.pmcid),
      url: pickEuropePmcUrl(item),
      journal: clean(item.journalTitle || (journalInfo.journal || {}).title),
      year: extractYear(item.pubYear, journalInfo.yearOfPublication, item.firstPublicationDate, item.electronicPublicationDate, item.firstIndexDate),
      publication_date: clean(item.firstPublicationDate) || clean(item.electronicPublicationDate) || clean(item.firstIndexDate),
      article_type: europePmcArticleType(item),
      authors: clean(item.authorString),
      keywords: Array.isArray(keywords) ? keywords.map(clean).filter(Boolean).join("; ") : clean(keywords),
      is_open_access: clean(item.isOpenAccess).toLowerCase(),
      metadata_status: "europepmc_search"
    }, query, retrievedAt);
  }

  function europePmcUrl(query, limit) {
    return "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + new URLSearchParams({
      query: query, format: "json", resultType: "core", pageSize: String(limit)
    }).toString();
  }

  // ------------------------------------------------------------------ OpenAlex

  function rebuildAbstract(index) {
    if (!index || typeof index !== "object") return "";
    var words = [];
    Object.keys(index).forEach(function (word) {
      (index[word] || []).forEach(function (position) { words[position] = word; });
    });
    return words.filter(function (word) { return word !== undefined; }).join(" ");
  }

  function pickOpenAlexUrl(item) {
    var primary = item.primary_location || {};
    var bestOa = item.best_oa_location || {};
    var candidates = [primary.pdf_url, primary.landing_page_url, bestOa.pdf_url, bestOa.landing_page_url, item.doi, item.id];
    for (var i = 0; i < candidates.length; i += 1) {
      if (candidates[i]) return candidates[i];
    }
    return "";
  }

  function normalizeOpenAlex(item, query, retrievedAt) {
    var ids = item.ids || {};
    var primary = item.primary_location || {};
    var openAccess = item.open_access || {};
    return stamp({
      source: "openalex",
      source_provider: "openalex",
      title: plainText(item.display_name || item.title),
      abstract: plainText(rebuildAbstract(item.abstract_inverted_index)),
      doi: clean(item.doi),
      pmid: lastPathSegment(ids.pmid),
      pmcid: lastPathSegment(ids.pmcid),
      url: pickOpenAlexUrl(item),
      journal: clean((primary.source || {}).display_name),
      year: clean(item.publication_year),
      publication_date: clean(item.publication_date),
      article_type: clean(item.type),
      authors: Array.isArray(item.authorships)
        ? item.authorships.slice(0, 12).map(function (a) { return clean((a.author || {}).display_name); }).join("; ")
        : "",
      keywords: Array.isArray(item.keywords)
        ? item.keywords.map(function (k) { return clean(k && (k.display_name || k.keyword)); }).filter(Boolean).join("; ")
        : "",
      is_open_access: String(Boolean(openAccess.is_oa)),
      oa_url: clean(openAccess.oa_url),
      metadata_status: "openalex_search"
    }, query, retrievedAt);
  }

  function openAlexUrl(query, limit) {
    return "https://api.openalex.org/works?" + new URLSearchParams({
      search: query, "per-page": String(limit)
    }).toString();
  }

  // ------------------------------------------------------------------ Crossref

  function pickCrossrefUrl(item) {
    var links = item.link || [];
    for (var i = 0; i < links.length; i += 1) {
      var link = links[i] || {};
      var href = link.URL || link.url;
      var type = String(link["content-type"] || "").toLowerCase();
      if (href && (type.indexOf("pdf") >= 0 || String(href).toLowerCase().slice(-4) === ".pdf")) return href;
    }
    if (item.DOI) return "https://doi.org/" + item.DOI;
    var resource = (item.resource || {}).primary || {};
    if (resource.URL) return resource.URL;
    return item.URL || "";
  }

  function crossrefDateParts(item) {
    var source = item["published-print"] || item["published-online"] || item.issued || {};
    var parts = (source["date-parts"] || [[]])[0] || [];
    return parts.filter(function (part) { return part !== null && part !== undefined; });
  }

  function normalizeCrossref(item, query, retrievedAt) {
    var titles = item.title || [""];
    var parts = crossrefDateParts(item);
    var container = item["container-title"];
    return stamp({
      source: "crossref",
      source_provider: "crossref",
      title: plainText(Array.isArray(titles) ? titles[0] : titles),
      abstract: plainText(item.abstract),
      doi: clean(item.DOI),
      pmid: "",
      pmcid: "",
      url: pickCrossrefUrl(item),
      journal: Array.isArray(container) ? clean(container[0]) : "",
      year: parts.length ? clean(parts[0]) : "",
      publication_date: parts.join("-"),
      article_type: clean(item.type),
      authors: Array.isArray(item.author)
        ? item.author.slice(0, 12).map(function (a) {
          return (clean(a.given) + " " + clean(a.family)).trim() || clean(a.name);
        }).join("; ")
        : "",
      metadata_status: "crossref_search"
    }, query, retrievedAt);
  }

  function crossrefUrl(query, limit) {
    return "https://api.crossref.org/works?" + new URLSearchParams({
      query: query,
      rows: String(limit),
      select: "DOI,title,abstract,author,container-title,type,URL,link,published-print,published-online,issued"
    }).toString();
  }

  // ------------------------------------------------------------------ PubMed (E-utilities)

  var PUBMED_DOI_RE = /(10\.\d{4,9}\/[-._;()/:A-Z0-9]+)/i;
  var PMCID_RE = /\bPMC\s*([0-9]+)\b/i;

  function cleanPubMedDoi(value) {
    if (!value) return "";
    var raw = String(value).trim()
      .replace(/https?:\/\/(?:dx\.)?doi\.org\//ig, " ")
      .replace("doi.org/", " ").replace("dx.doi.org/", " ")
      .replace("DOI:", " ").replace("doi:", " ");
    var match = PUBMED_DOI_RE.exec(raw);
    return match ? match[1].replace(/[ .;,)\]}]+$/, "") : "";
  }

  function cleanPubMedPmcid(value) {
    var raw = clean(value);
    if (!raw) return "";
    var match = PMCID_RE.exec(raw);
    if (match) return "PMC" + match[1];
    if (/^\d+$/.test(raw)) return "PMC" + raw;
    return raw.toLowerCase().indexOf("pmc") === 0 ? raw.toUpperCase() : raw;
  }

  function pickArticleId(item, types) {
    var ids = item.articleids || [];
    for (var i = 0; i < ids.length; i += 1) {
      var entry = ids[i] || {};
      if (types.indexOf(String(entry.idtype || "").toLowerCase()) >= 0 && entry.value) return String(entry.value).trim();
    }
    return "";
  }

  function pubMedAuthors(item) {
    var names = (item.authors || []).filter(function (a) { return a && a.name; }).map(function (a) { return String(a.name); });
    if (names.length > 12) return names.slice(0, 12).join("; ") + "; +" + (names.length - 12) + " more";
    return names.join("; ");
  }

  function normalizePubMedSummary(item, pmid, abstract, query, retrievedAt) {
    var doi = cleanPubMedDoi(pickArticleId(item, ["doi"])) || cleanPubMedDoi(item.elocationid);
    var pmcid = cleanPubMedPmcid(pickArticleId(item, ["pmc", "pmcid"]));
    var pubdate = item.pubdate || item.epubdate || "";
    var url = pmcid
      ? "https://pmc.ncbi.nlm.nih.gov/articles/" + pmcid + "/"
      : doi ? "https://doi.org/" + doi : "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/";
    return stamp({
      source: "pubmed",
      source_provider: "pubmed",
      title: plainText(item.title),
      abstract: plainText(abstract || ""),
      doi: doi,
      pmid: String(pmid),
      pmcid: pmcid,
      url: url,
      journal: clean(item.fulljournalname || item.source),
      year: extractYear(item.pubdate, item.epubdate, pubdate),
      publication_date: clean(pubdate),
      article_type: (item.pubtype || []).join("; "),
      authors: pubMedAuthors(item),
      metadata_status: "pubmed_esummary"
    }, query, retrievedAt);
  }

  /** Parse efetch XML into {pmid: abstract}. Needs a DOMParser implementation. */
  function pubMedAbstracts(xmlText, DOMParserImpl) {
    var out = {};
    if (!xmlText || !DOMParserImpl) return out;
    var doc = new DOMParserImpl().parseFromString(xmlText, "application/xml");
    if (doc.getElementsByTagName("parsererror").length) return out;
    var articles = doc.getElementsByTagName("PubmedArticle");
    for (var i = 0; i < articles.length; i += 1) {
      var pmidNode = articles[i].getElementsByTagName("PMID")[0];
      var pmid = pmidNode ? pmidNode.textContent.trim() : "";
      if (!pmid) continue;
      var parts = [];
      var nodes = articles[i].getElementsByTagName("AbstractText");
      for (var j = 0; j < nodes.length; j += 1) {
        var text = nodes[j].textContent.trim();
        if (text) parts.push(text);
      }
      if (parts.length) out[pmid] = parts.join("\n");
    }
    return out;
  }

  function eutils(endpoint, params) {
    return "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint + "?" +
      new URLSearchParams(Object.assign({ tool: TOOL }, params)).toString();
  }

  // ------------------------------------------------------------------ registry

  var SOURCES = [
    { id: "europepmc", label: "Europe PMC", home: "https://europepmc.org/", defaultOn: true },
    { id: "pubmed", label: "PubMed", home: "https://pubmed.ncbi.nlm.nih.gov/", defaultOn: true },
    { id: "openalex", label: "OpenAlex", home: "https://openalex.org/", defaultOn: true },
    { id: "crossref", label: "Crossref", home: "https://www.crossref.org/", defaultOn: true }
  ];

  /** Sources the Reference Engine knows about but this browser surface does not query. */
  var NOT_QUERIED = [
    { id: "scopus_wos", label: "Scopus / Web of Science", reason: "licensed" },
    { id: "lilacs_scielo", label: "LILACS/BVS, SciELO, DOAJ, Semantic Scholar", reason: "engine_only" }
  ];

  // ------------------------------------------------------------------ fetching

  function SourceError(kind, message, httpStatus) {
    this.name = "SourceError";
    this.kind = kind;
    this.message = message;
    this.httpStatus = httpStatus || null;
  }
  SourceError.prototype = Object.create(Error.prototype);

  function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  async function request(url, options) {
    var fetchImpl = options.fetch;
    var attempts = 2;
    var lastError = null;
    for (var attempt = 1; attempt <= attempts; attempt += 1) {
      var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
      var timer = controller ? setTimeout(function () { controller.abort(); }, options.timeoutMs || 25000) : null;
      try {
        var response = await fetchImpl(url, { signal: controller ? controller.signal : undefined, headers: { Accept: options.accept || "application/json" } });
        if (timer) clearTimeout(timer);
        if (response.status === 429 || response.status >= 500) {
          lastError = new SourceError(response.status === 429 ? "rate_limited" : "http_error", "HTTP " + response.status, response.status);
          if (attempt < attempts) { await sleep(1500 * attempt); continue; }
          throw lastError;
        }
        if (!response.ok) throw new SourceError("http_error", "HTTP " + response.status, response.status);
        return options.text ? await response.text() : await response.json();
      } catch (error) {
        if (timer) clearTimeout(timer);
        if (error instanceof SourceError) throw error;
        var kind = error && error.name === "AbortError" ? "timeout" : "network_error";
        lastError = new SourceError(kind, error && error.message ? error.message : String(error));
        if (attempt < attempts) { await sleep(1000 * attempt); continue; }
        throw lastError;
      }
    }
    throw lastError;
  }

  async function searchEuropePmc(query, limit, options) {
    var retrievedAt = new Date().toISOString();
    var data = await request(europePmcUrl(query, limit), options);
    var items = ((data || {}).resultList || {}).result || [];
    return {
      total_found: typeof data.hitCount === "number" ? data.hitCount : null,
      rows: items.map(function (item) { return normalizeEuropePmc(item, query, retrievedAt); })
    };
  }

  async function searchOpenAlex(query, limit, options) {
    var retrievedAt = new Date().toISOString();
    var data = await request(openAlexUrl(query, limit), options);
    return {
      total_found: ((data || {}).meta || {}).count ?? null,
      rows: ((data || {}).results || []).map(function (item) { return normalizeOpenAlex(item, query, retrievedAt); })
    };
  }

  async function searchCrossref(query, limit, options) {
    var retrievedAt = new Date().toISOString();
    var data = await request(crossrefUrl(query, limit), options);
    var message = (data || {}).message || {};
    return {
      total_found: message["total-results"] ?? null,
      rows: (message.items || []).map(function (item) { return normalizeCrossref(item, query, retrievedAt); })
    };
  }

  async function searchPubMed(query, limit, options) {
    var retrievedAt = new Date().toISOString();
    var search = await request(eutils("esearch.fcgi", { db: "pubmed", term: query, retmode: "json", retmax: String(limit) }), options);
    var result = (search || {}).esearchresult || {};
    var ids = result.idlist || [];
    var notes = [];
    if (!ids.length) return { total_found: Number(result.count || 0), rows: [], notes: notes };
    await sleep(350);
    var summary = await request(eutils("esummary.fcgi", { db: "pubmed", id: ids.join(","), retmode: "json" }), options);
    var abstracts = {};
    try {
      await sleep(350);
      var xml = await request(eutils("efetch.fcgi", { db: "pubmed", id: ids.join(","), rettype: "abstract", retmode: "xml" }), Object.assign({}, options, { text: true, accept: "application/xml" }));
      abstracts = pubMedAbstracts(xml, options.DOMParser);
    } catch (error) {
      notes.push("abstracts_unavailable");
    }
    var docs = (summary || {}).result || {};
    var uids = docs.uids || ids;
    return {
      total_found: Number(result.count || 0),
      notes: notes,
      rows: uids.filter(function (uid) { return docs[uid] && !docs[uid].error; }).map(function (uid) {
        return normalizePubMedSummary(docs[uid], uid, abstracts[uid], query, retrievedAt);
      })
    };
  }

  var SEARCHERS = { europepmc: searchEuropePmc, openalex: searchOpenAlex, crossref: searchCrossref, pubmed: searchPubMed };

  /**
   * Query the selected sources in parallel. Resolves with one status entry per
   * source; never rejects because a single source failed.
   */
  async function searchSources(query, sourceIds, limit, options) {
    var opts = Object.assign({ fetch: typeof fetch !== "undefined" ? fetch.bind(globalThis) : null }, options || {});
    var jobs = sourceIds.map(async function (id) {
      var started = Date.now();
      try {
        var result = await SEARCHERS[id](query, limit, opts);
        var status = {
          source: id,
          status: "ok",
          total_found: result.total_found,
          returned: result.rows.length,
          notes: result.notes || [],
          elapsed_ms: Date.now() - started
        };
        if (opts.onSource) opts.onSource(status);
        return { status: status, rows: result.rows };
      } catch (error) {
        var failed = {
          source: id,
          status: "error",
          error_kind: error && error.kind ? error.kind : "network_error",
          error: error && error.message ? error.message : String(error),
          http_status: error && error.httpStatus ? error.httpStatus : null,
          returned: 0,
          elapsed_ms: Date.now() - started
        };
        if (opts.onSource) opts.onSource(failed);
        return { status: failed, rows: [] };
      }
    });
    var settled = await Promise.all(jobs);
    return {
      statuses: settled.map(function (item) { return item.status; }),
      rows: settled.reduce(function (all, item) { return all.concat(item.rows); }, [])
    };
  }

  return {
    SOURCES: SOURCES,
    NOT_QUERIED: NOT_QUERIED,
    plainText: plainText,
    rebuildAbstract: rebuildAbstract,
    normalizeEuropePmc: normalizeEuropePmc,
    normalizeOpenAlex: normalizeOpenAlex,
    normalizeCrossref: normalizeCrossref,
    normalizePubMedSummary: normalizePubMedSummary,
    pubMedAbstracts: pubMedAbstracts,
    europePmcUrl: europePmcUrl,
    openAlexUrl: openAlexUrl,
    crossrefUrl: crossrefUrl,
    searchSources: searchSources
  };
});
