/* Build identity of this page. The Hetzner image build (deploy/hetzner/Dockerfile)
 * and the on-demand GitHub Pages workflow overwrite this file with the published
 * commit SHA; a local checkout keeps the "local" marker. */
(function (root) {
  "use strict";
  root.NUTEV_OPEN_BUILD = { commit: "local", built_at: "", source: "local checkout" };
})(typeof globalThis !== "undefined" ? globalThis : this);
