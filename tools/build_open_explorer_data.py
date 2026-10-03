"""Build the browser data bundle for the Open Evidence Explorer.

The Open Evidence Explorer (``apps/nutev-open/``) runs entirely in the browser.
It must classify records with exactly the same canonical vocabulary, document
classes and scoring constants as the Reference Engine. This tool compiles those
canonical sources into ``apps/nutev-open/data/nutev-open-data.js`` so the
browser never maintains a second, hand-edited copy of the taxonomy.

Usage::

    python tools/build_open_explorer_data.py          # write the bundle
    python tools/build_open_explorer_data.py --check  # fail if the bundle drifted

The bundle intentionally contains no git commit, timestamp or private state, so
it only changes when the canonical configuration changes.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nutev.__version__ import __version__  # noqa: E402
from nutev.audit_guardrails import GUARDRAIL_POLICY_VERSION  # noqa: E402
from nutev.search.classification import _CLASS_PATTERNS  # noqa: E402
from nutev.search.document_classes import (  # noqa: E402
    CANONICAL_DOCUMENT_CLASS_LABELS,
    DOCUMENT_CLASS_ONTOLOGY_VERSION,
)
from nutev.search.question_planner import (  # noqa: E402
    PLANNER_VERSION,
    QUERY_VOCABULARY_FILENAME,
    load_query_vocabulary,
    validate_query_vocabulary,
)
from nutev.taxonomy import load_canonical_taxonomy, taxonomy_config_paths  # noqa: E402

CONFIG_DIR = ROOT / "config"
APP_DIR = ROOT / "apps" / "nutev-open"
PRESENTATION_PATH = APP_DIR / "presentation.json"
OUTPUT_PATH = APP_DIR / "data" / "nutev-open-data.js"
BUNDLE_SCHEMA_VERSION = 1

# Mirrors tools/rank_references.py::score_record. The Python/JavaScript parity
# test (nutev_tests/test_open_explorer.py) fails if either side drifts.
SCORING_CONSTANTS: dict[str, Any] = {
    "taxonomy": {
        "title": 6.0,
        "keywords": 4.0,
        "abstract": 2.0,
        "term_cap": 8.0,
        "max_terms_per_group": 4,
        "group_bonus": 3.0,
    },
    "focus": {"title": 10.0, "keywords": 6.0, "abstract": 4.0},
    "document_type_weights": [
        ["clinical practice guideline", 12.0],
        ["practice guideline", 11.0],
        ["guideline", 10.0],
        ["consensus statement", 9.0],
        ["consensus", 7.0],
        ["position statement", 8.0],
        ["scientific statement", 8.0],
        ["standards of care", 8.0],
        ["systematic review", 7.0],
        ["meta analysis", 7.0],
        ["framework", 5.0],
        ["recommendation", 4.0],
    ],
    "identifier": 2.0,
    "recency": [[5, 4.0], [10, 2.0]],
    "penalties": {"missing_title": -25.0, "missing_abstract": -1.0},
}

DOCUMENT_CLASS_LABELS_EN = {
    "evidence_synthesis": "Evidence synthesis",
    "guidance": "Guideline / guidance",
    "framework_implementation": "Framework / implementation",
    "primary_randomized": "Randomised trial",
    "primary_observational": "Observational study",
    "primary_qualitative": "Qualitative study",
    "review": "Review",
    "unclassified": "Unclassified",
}


class BundleError(RuntimeError):
    """Raised when canonical sources cannot be compiled deterministically."""


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _load_presentation() -> dict[str, Any]:
    data = json.loads(PRESENTATION_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BundleError("presentation.json must be an object")
    return data


def build_bundle() -> dict[str, Any]:
    taxonomy, metadata = load_canonical_taxonomy(CONFIG_DIR)
    if metadata.get("registry_mode") != "canonical":
        raise BundleError("The open explorer requires the canonical taxonomy registry")

    profile = json.loads((CONFIG_DIR / "reference_mode.json").read_text(encoding="utf-8"))
    guardrails = profile.get("guardrails") or {}
    if guardrails.get("document_type_scoring", "highest_weight_only") != "highest_weight_only":
        raise BundleError("Only document_type_scoring=highest_weight_only is supported")

    presentation = _load_presentation()
    families = presentation.get("families") or []
    labels_en = presentation.get("group_labels_en") or {}
    group_metadata = metadata.get("group_metadata") or {}

    groups: list[dict[str, Any]] = []
    for group_id, terms in taxonomy.items():
        family = [item for item in families if group_id.startswith(str(item.get("prefix")))]
        if len(family) != 1:
            raise BundleError(f"Group {group_id} must belong to exactly one presentation family")
        label_en = str(labels_en.get(group_id) or "").strip()
        if not label_en:
            raise BundleError(f"Missing English label for canonical group {group_id}")
        label_pt = str((group_metadata.get(group_id) or {}).get("label_pt") or "").strip()
        if not label_pt:
            raise BundleError(f"Missing label_pt in taxonomy_registry.json for {group_id}")
        groups.append(
            {
                "id": group_id,
                "dimension": group_id.split(".", 1)[0],
                "family": family[0]["id"],
                "label_pt": label_pt,
                "label_en": label_en,
                "terms": list(terms),
            }
        )

    stale = sorted(set(labels_en) - set(taxonomy))
    if stale:
        raise BundleError("presentation.json labels unknown groups: " + ", ".join(stale))

    query_vocabulary = load_query_vocabulary(CONFIG_DIR)
    validate_query_vocabulary(query_vocabulary, set(taxonomy))

    source_paths = [
        CONFIG_DIR / "reference_mode.json",
        CONFIG_DIR / QUERY_VOCABULARY_FILENAME,
        *taxonomy_config_paths(CONFIG_DIR),
    ]
    config_hashes = {_relative(path): _sha256(path) for path in source_paths}
    config_hashes[_relative(PRESENTATION_PATH)] = _sha256(PRESENTATION_PATH)

    registry = json.loads((CONFIG_DIR / "taxonomy_registry.json").read_text(encoding="utf-8"))

    bundle: dict[str, Any] = {
        "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
        "generated_by": "tools/build_open_explorer_data.py",
        "engine_version": __version__,
        "guardrail_policy_version": GUARDRAIL_POLICY_VERSION,
        "taxonomy_version": metadata["taxonomy_version"],
        "document_class_ontology_version": DOCUMENT_CLASS_ONTOLOGY_VERSION,
        "config_sha256": config_hashes,
        "taxonomy": {
            "primary_dimension_order": metadata["primary_dimension_order"],
            "dimensions": registry.get("dimensions") or {},
            "families": families,
            "groups": groups,
            "canonical_groups_loaded": metadata["canonical_groups_loaded"],
            "canonical_terms_total": metadata["canonical_terms_total"],
        },
        "document_classes": {
            "patterns": [[name, list(patterns)] for name, patterns in _CLASS_PATTERNS],
            "labels_pt": CANONICAL_DOCUMENT_CLASS_LABELS,
            "labels_en": DOCUMENT_CLASS_LABELS_EN,
        },
        "scoring": {
            **SCORING_CONSTANTS,
            "taxonomy_score_cap": float(guardrails.get("taxonomy_score_cap") or 0.0),
            "focus_score_cap": float(guardrails.get("focus_score_cap") or 0.0),
            "focus_keywords": list(profile.get("focus_keywords") or []),
            "provider_weights": {
                str(key): float(value)
                for key, value in (profile.get("provider_weights") or {}).items()
            },
        },
        "example_queries": list(presentation.get("example_queries") or []),
        "example_queries_en": list(presentation.get("example_queries_en") or []),
        "planner_version": PLANNER_VERSION,
        "query_vocabulary": query_vocabulary,
    }
    missing_en = sorted(set(CANONICAL_DOCUMENT_CLASS_LABELS) - set(DOCUMENT_CLASS_LABELS_EN))
    if missing_en:
        raise BundleError("Missing English document class labels: " + ", ".join(missing_en))
    payload = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    bundle["bundle_sha256"] = sha256(payload.encode("utf-8")).hexdigest()
    return bundle


def render_bundle(bundle: dict[str, Any]) -> str:
    body = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=1)
    return (
        "/* GENERATED FILE - do not edit by hand.\n"
        " * Source: config/taxonomy_registry.json, config/keyword_taxonomy*.json,\n"
        " * config/reference_mode.json, config/query_vocabulary.json,\n"
        " * src/nutev/search/classification.py and\n"
        " * apps/nutev-open/presentation.json.\n"
        " * Regenerate with: python tools/build_open_explorer_data.py\n"
        " */\n"
        "(function (root) {\n"
        "  \"use strict\";\n"
        f"  var data = {body};\n"
        "  if (typeof module === \"object\" && module.exports) { module.exports = data; }\n"
        "  root.NUTEV_OPEN_DATA = data;\n"
        "})(typeof globalThis !== \"undefined\" ? globalThis : this);\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit with status 1 if the committed bundle differs from canonical sources",
    )
    args = parser.parse_args(argv)

    rendered = render_bundle(build_bundle())
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.is_file() else ""
        if current != rendered:
            print(
                f"{_relative(OUTPUT_PATH)} is out of date. "
                "Run: python tools/build_open_explorer_data.py",
                file=sys.stderr,
            )
            return 1
        print(f"{_relative(OUTPUT_PATH)} matches canonical sources.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"wrote {_relative(OUTPUT_PATH)} ({len(rendered.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
