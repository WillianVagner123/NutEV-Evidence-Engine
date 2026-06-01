from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_prisma_flow(
    all_rows: list[dict],
    download_manifest: list[dict],
    extraction_manifest: list[dict],
) -> dict:
    identified = len(all_rows)
    dedup_removed = max(
        0,
        identified - len({r.get("url") for r in all_rows if r.get("url")}),
    )
    triaged = identified - dedup_removed
    extracted = sum(
        1 for e in extraction_manifest if e.get("extraction_status") == "ok"
    )
    analyzed = sum(
        1 for r in all_rows if r.get("domains") or r.get("nutev_objects")
    )
    prioritized = sum(
        1 for r in all_rows if float(r.get("score", 0) or 0) >= 8
    )

    def cls(kind: str) -> int:
        return sum(
            1 for r in all_rows if kind in (r.get("nutev_objects", ""))
        )

    return {
        "registros_identificados": identified,
        "duplicados_removidos": dedup_removed,
        "registros_triados": triaged,
        "registros_excluidos": max(0, triaged - len(download_manifest)),
        "docs_texto_extraido": extracted,
        "docs_analisados": analyzed,
        "docs_priorizados": prioritized,
        "class_evidence_table": cls("evidence_table"),
        "class_protocol_rule": cls("protocol_rule"),
        "class_questionnaire_item_candidate": cls(
            "questionnaire_item_candidate"
        ),
        "class_framework_component": cls("framework_component"),
    }


def export_prisma(flow: dict, xlsx: Path, json_path: Path) -> None:
    xlsx.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        pd.DataFrame([flow]).to_excel(xlsx, index=False)
    except Exception:
        pd.DataFrame([flow]).to_csv(xlsx.with_suffix(".csv"), index=False, encoding="utf-8-sig")
        xlsx.touch()
    json_path.write_text(
        json.dumps(flow, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
