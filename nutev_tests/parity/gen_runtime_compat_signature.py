"""Generate the runtime_compat query-parity signature (Phase 0 harness).

Run in a FRESH process so the measurement is hermetic — immune to whatever other
tests did to the global patch/module state within a pytest session. Prints the
compact signature (per-workstream/provider SHA-256 + counts) as JSON.

Usage:
    # recompute and inspect
    python nutev_tests/parity/gen_runtime_compat_signature.py
    # regenerate the committed baseline (ONLY with an intentional, documented decision)
    python nutev_tests/parity/gen_runtime_compat_signature.py > \
        nutev_tests/parity/runtime_compat_query_baseline.json
"""
from __future__ import annotations

import hashlib
import json

WORKSTREAMS = ["busca1", "busca2a", "busca2b", "a3"]
PROVIDERS = ["pubmed", "europepmc", "openalex", "crossref"]

_COMMENT = (
    "Phase-0 parity baseline for the runtime_compat migration. Locks the exact "
    "generated queries (patches ON). Any phase that changes these digests changed "
    "scientific output and must be reviewed. Regenerate ONLY with an intentional, "
    "documented decision via gen_runtime_compat_signature.py."
)


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def build_signature() -> dict:
    from nutev.runtime_compat import apply

    apply()  # current (patched) behaviour — the thing the migration must preserve
    from nutev.querypacks.builders import build_querypack
    from nutev.querypacks.provider_queries import build_provider_querypack
    from nutev.settings import default_config_root, load_json

    taxonomy = load_json(default_config_root() / "keyword_taxonomy.json")
    general = build_querypack(taxonomy, WORKSTREAMS)
    provider = build_provider_querypack(
        taxonomy, WORKSTREAMS, {w: PROVIDERS for w in WORKSTREAMS}
    )
    return {
        "_comment": _COMMENT,
        "workstreams": WORKSTREAMS,
        "providers": PROVIDERS,
        "overall_sha256": _sha({"general": general, "provider": provider}),
        "general": {w: {"count": len(general[w]), "sha256": _sha(general[w])} for w in WORKSTREAMS},
        "provider": {
            w: {p: {"count": len(provider[w][p]), "sha256": _sha(provider[w][p])} for p in PROVIDERS}
            for w in WORKSTREAMS
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_signature(), ensure_ascii=False, indent=2, sort_keys=True))
