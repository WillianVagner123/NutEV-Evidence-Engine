"""Article-1 reproducible exports (§17): A/B/C/D matrix, PRISMA counts, dictionary.

Assembles the publication-facing artifacts from the coded rows + entity
registries + screening queue that other slices already produce:

- **A/B/C/D matrix** — one row per document with each domain's state and
  intensity (0–3), the central Article-1 result in wide form.
- **PRISMA-ScR counts** (+ a Mermaid diagram) — the identification / dedup /
  screening-readiness numbers, honestly labelled. Because two-reviewer screening
  happens with humans, the *included* count is left ``pending`` here — the
  pipeline never declares a final corpus (§5.5, §20).
- **Data dictionary** — what each output file/column means.

Everything is derived and reproducible; nothing is fabricated.
"""
from __future__ import annotations

import json
from pathlib import Path

from nutev.analysis.domain_states import DOMAINS


def abcd_matrix_rows(rows: list[dict]) -> list[dict]:
    """Wide document × A/B/C/D matrix with state + intensity per domain."""
    out: list[dict] = []
    for r in rows:
        item = {
            "name": r.get("name", ""),
            "country": r.get("country", r.get("reference_country", "")),
            "reference": r.get("reference", ""),
        }
        n_positive = 0
        for d in DOMAINS:
            state = r.get(f"domain_{d}_state", "NOT_ASSESSED")
            item[f"{d}_state"] = state
            item[f"{d}_intensity"] = r.get(f"domain_{d}_intensity", "")
            if state in {"RECOMMENDED", "OPERATIONALIZED"}:
                n_positive += 1
        item["n_domains_positive"] = n_positive
        out.append(item)
    return out


def prisma_counts(registries: dict, queue: list[dict]) -> dict:
    """PRISMA-ScR identification/screening-readiness counts (Article 1).

    ``included`` is intentionally ``"pending"`` — two human reviewers decide; the
    pipeline only reports what is identified and ready to screen.
    """
    ready = sum(1 for q in queue if q.get("screen_flag") == "ready_to_screen")
    no_text = sum(1 for q in queue if q.get("screen_flag") != "ready_to_screen")
    return {
        "identified_file_assets": len(registries.get("file_assets", [])),
        "unique_document_versions": len(registries.get("versions", [])),
        "document_families": len(registries.get("families", [])),
        "queued_for_screening": len(queue),
        "ready_to_screen": ready,
        "excluded_no_full_text_or_poor_ocr": no_text,
        "included": "pending",  # two-reviewer validation required (§13/§20)
        "note": "Counts are pre-screening. The final included corpus requires "
                "two-reviewer full-text validation and is not declared here.",
    }


def prisma_diagram_mermaid(counts: dict) -> str:
    """A reproducible Mermaid PRISMA-ScR flow (identification → screening)."""
    return "\n".join([
        "```mermaid",
        "flowchart TD",
        f'  A[Arquivos identificados: {counts["identified_file_assets"]}]'
        f' --> B[Versões únicas de documento: {counts["unique_document_versions"]}]',
        f'  B --> C[Famílias de documento: {counts["document_families"]}]',
        f'  B --> D[Prontos para triagem: {counts["ready_to_screen"]}]',
        f'  B --> E[Sem texto / OCR ruim: {counts["excluded_no_full_text_or_poor_ocr"]}]',
        '  D --> F[Triagem por 2 revisores: PENDENTE]',
        '  F --> G[Incluídos: PENDENTE validação humana]',
        "```",
    ])


_DATA_DICTIONARY = """# Dicionário de dados — saídas do `nutev guides`

> Toda codificação é **assistiva** (sugestão de máquina) e entra em revisão
> humana. Nada é decisão final ou avaliação de qualidade/risco de viés.

## Tabelas principais (`06_tables/`)
- **NUTEV_GUIDES_CODED.csv** — uma linha por guia: proveniência (`sha256`,
  `access_date`), OCR, domínios A/B/C/D (booleano + `*_state`/`*_intensity`),
  tipo/peso de documento, padrões nomeados, valores nutricionais, frases-chave.
- **NUTEV_GUIDES_EVIDENCE.csv** — 1 linha por tema detectado: trecho verbatim +
  família/subtema + referência.
- **NUTEV_GUIDES_DOMAIN_STATES.csv** — 1 linha por documento × domínio:
  `state` (NOT_ASSESSED/MENTIONED/RECOMMENDED/OPERATIONALIZED), `intensity` (0–3),
  `evidence`, `page`, `reference`, `coding_source=machine_suggestion`.
- **NUTEV_GUIDES_ABCD_MATRIX.csv** — matriz larga documento × A/B/C/D (estado +
  intensidade) — o resultado central do Artigo 1.
- **NUTEV_GUIDES_EVIDENCE_GEMS.csv** — riquezas ranqueadas (score 0–18 de valor
  **descritivo**), com trecho, página, referência e destino no manuscrito.
- **NUTEV_GUIDES_SCREENING_QUEUE.csv** — fila de triagem por 2 revisores;
  `screen_flag` separa docs sem texto/OCR ruim; `export_ready` só após validação.

## Registros de entidade (`07_logs/`)
- **file_asset_registry.csv** — arquivo físico (sha256) → versão/família.
- **document_version_registry.csv** — versão (edição/ano/idioma); `status`
  current/superseded.
- **document_family_registry.csv** — documento através das edições.
- **denominator_registry.csv** — contagens nomeadas (arquivos × versões ×
  famílias) para nunca somar denominadores incompatíveis.
- **prisma_counts.json** — contagens PRISMA-ScR (identificação/prontidão);
  `included = pending` (validação humana).

## Curadoria (`10_curated/`)
- **best_gems.md** — brief das melhores riquezas.
- **prisma_diagram.md** — diagrama PRISMA-ScR (Mermaid), reprodutível.
"""


def write_article1_exports(rows: list[dict], registries: dict, queue: list[dict], settings) -> dict:
    """Write the A/B/C/D matrix, PRISMA counts + diagram and the data dictionary."""
    from nutev.export.metadata_tables import write_simple_csv

    tables = settings.output_dirs["06_tables"]
    logs = settings.output_dirs["07_logs"]
    curated = settings.output_dirs["10_curated"]
    # 08_docs is the natural home for the dictionary; fall back to the curated dir
    # when a minimal settings object doesn't define it.
    docs = settings.output_dirs.get("08_docs", curated)

    matrix = abcd_matrix_rows(rows)
    write_simple_csv(matrix, tables / "NUTEV_GUIDES_ABCD_MATRIX.csv")

    counts = prisma_counts(registries, queue)
    (logs / "prisma_counts.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    (curated / "prisma_diagram.md").write_text(prisma_diagram_mermaid(counts), encoding="utf-8")

    Path(docs).mkdir(parents=True, exist_ok=True)
    (docs / "DATA_DICTIONARY.md").write_text(_DATA_DICTIONARY, encoding="utf-8")

    return {
        "abcd_matrix_rows": len(matrix),
        "prisma_counts": counts,
        "abcd_matrix_csv": str(tables / "NUTEV_GUIDES_ABCD_MATRIX.csv"),
        "prisma_counts_json": str(logs / "prisma_counts.json"),
        "data_dictionary": str(docs / "DATA_DICTIONARY.md"),
    }
