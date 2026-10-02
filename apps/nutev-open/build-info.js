/* Build identity of this page. The GitHub Pages workflow overwrites this file
 * with the published commit SHA; a local checkout keeps the "local" marker. */
(function (root) {
  "use strict";
  root.NUTEV_OPEN_BUILD = { commit: "local", built_at: "", source: "local checkout" };
})(typeof globalThis !== "undefined" ? globalThis : this);
