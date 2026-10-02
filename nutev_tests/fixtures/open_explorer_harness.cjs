// Runs the Open Evidence Explorer browser modules under Node for parity tests.
// Input (stdin JSON): { rows, nowYear, probes, api }
// Output (stdout JSON): normalized probe values, pipeline output and adapter output.
"use strict";

const path = require("path");
const root = path.resolve(__dirname, "..", "..", "apps", "nutev-open");
const core = require(path.join(root, "core.js"));
const sources = require(path.join(root, "sources.js"));
const data = require(path.join(root, "data", "nutev-open-data.js"));

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  const request = JSON.parse(input);
  const probes = request.probes || {};
  const map = (values, fn) => (values || []).map((value) => fn(value));
  const result = {
    probes: {
      doi: map(probes.doi, core.normalizeDoi),
      pmid: map(probes.pmid, core.normalizePmid),
      pmcid: map(probes.pmcid, core.normalizePmcid),
      url: map(probes.url, core.normalizeUrl),
      title: map(probes.title, core.normalizeTitle),
      norm: map(probes.norm, core.norm),
      identity: map(probes.identity, core.canonicalIdentity),
      traceability: map(probes.traceability, (row) => {
        const out = core.recordTraceability(row);
        return [out.traceability, out.reasons];
      }),
      document_class: map(probes.document_class, (row) => {
        const out = core.documentClass(row, data);
        return [out.document_class, out.confidence, out.signals];
      }),
    },
  };
  if (request.rows) {
    const pipeline = core.runPipeline(request.rows, data, { nowYear: request.nowYear });
    result.pipeline = {
      quarantined: pipeline.quarantined.map((row) => [row.title || "", row.audit_traceability, row.audit_reasons]),
      ranked: pipeline.ranked,
      stats: pipeline.stats,
    };
  }
  if (request.api) {
    const api = request.api;
    result.api = {
      europepmc: (api.europepmc || []).map((item) => sources.normalizeEuropePmc(item, "q", "t")),
      openalex: (api.openalex || []).map((item) => sources.normalizeOpenAlex(item, "q", "t")),
      crossref: (api.crossref || []).map((item) => sources.normalizeCrossref(item, "q", "t")),
      pubmed: (api.pubmed || []).map((item) => sources.normalizePubMedSummary(item, item.uid, item._abstract || "", "q", "t")),
      urls: {
        europepmc: sources.europePmcUrl("diet & health", 25),
        openalex: sources.openAlexUrl("diet & health", 25),
        crossref: sources.crossrefUrl("diet & health", 25),
      },
    };
  }
  process.stdout.write(JSON.stringify(result));
});
