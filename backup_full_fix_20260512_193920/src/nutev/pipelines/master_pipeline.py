from __future__ import annotations
from pathlib import Path
import pandas as pd
from nutev.settings import NutevSettings, load_json
from nutev.querypacks.builders import build_querypack
from nutev.search.openalex import search_openalex
from nutev.search.europepmc import search_europepmc
from nutev.search.pubmed import search_pubmed
from nutev.search.official_sources import manifest_sources
from nutev.analysis.relevance import score_record
from nutev.analysis import domains_busca1, domains_busca2a, domains_busca2b
from nutev.analysis.article3_framework import build_framework_signals
from nutev.analysis.synthesis import build_master_rows, build_questionnaire_candidates, build_framework_components, write_synthesis_outputs
from nutev.analysis.prisma import build_prisma_flow, export_prisma
from nutev.download.downloader import download_records
from nutev.extract.smart_extract import extract_document
from nutev.export.metadata_tables import write_metadata_csv, write_simple_csv
from nutev.export.rayyan import write_rayyan
from nutev.export.excel_writer import write_analysis_xlsx
from nutev.export.logs import write_run_summary
from nutev.export.methods_writer import write_methods_docs
from nutev.export.qualification_writer import write_qualification_outputs


def run_pipeline(settings: NutevSettings, workstreams: list[str], logger) -> dict[str, int]:
    taxonomy = load_json(settings.config_root / "keyword_taxonomy.json")
    scoring = load_json(settings.config_root / "scoring_rules.json")
    sources = load_json(settings.config_root / "official_sources_manifest.json")
    qpack = build_querypack(taxonomy, workstreams)

    all_rows, extraction_manifest, all_manifest = [], [], []
    total_downloads = total_failed = total_ocr = 0

    for ws, queries in qpack.items():
        logger.info("workstream=%s queries_geradas=%d", ws, len(queries))
        rows = []

        max_queries = min(len(queries), 12)
        for q in queries[:max_queries]:
            try:
                rows += search_openalex(q)
            except Exception as e:
                logger.warning("openalex falhou ws=%s query=%s erro=%s", ws, q, e)

            try:
                rows += search_europepmc(q)
            except Exception as e:
                logger.warning("europepmc falhou ws=%s query=%s erro=%s", ws, q, e)

            try:
                rows += search_pubmed(q)
            except Exception as e:
                logger.warning("pubmed falhou ws=%s query=%s erro=%s", ws, q, e)

        rows += manifest_sources(sources, ws)

        for r in rows:
            r["workstream"] = ws

        rows = [score_record(r, scoring, ws) for r in rows]

        manifest, failed = download_records(
            rows,
            settings.output_dirs["03B_public_downloads"],
            settings.output_dirs["03C_official_docs"],
            logger,
        )

        all_manifest += manifest
        total_downloads += len(manifest)
        total_failed += len(failed)

        write_simple_csv(all_manifest, settings.project_root / "03_corpus" / "download_manifest.csv")
        write_simple_csv(failed, settings.project_root / "03_corpus" / "failed_downloads.csv")

        ext_by_url = {}
        for m in manifest:
            e = extract_document(
                Path(m["path"]),
                settings.output_dirs["04_ocr_text"],
                settings.output_dirs["05_extraction"],
                logger,
            )
            extraction_manifest.append(e)
            total_ocr += int(e.get("used_ocr", False))
            if isinstance(m.get("url"), str):
                ext_by_url[m["url"]] = e

        for r in rows:
            url_key = r.get("url")
            if not isinstance(url_key, str):
                url_key = ""
            e = ext_by_url.get(url_key, {})
            r["file_path"] = e.get("file", "")
            r["ocr_status"] = "used" if e.get("used_ocr") else "not_used"
            r["extraction_status"] = e.get("extraction_status", "missing")
            if e.get("text_path"):
                r["extracted_text"] = Path(e["text_path"]).read_text(encoding="utf-8", errors="ignore")

        if ws == "busca1":
            rows = domains_busca1.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca1.json"))
        elif ws == "busca2a":
            rows = domains_busca2a.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca2a.json"))
        elif ws == "busca2b":
            rows = domains_busca2b.apply_domain_rules(rows, load_json(settings.config_root / "domain_rules_busca2b.json"))
        elif ws in {"a3", "artigo3_framework"}:
            rows = build_framework_signals(rows)

        write_analysis_xlsx(rows, settings.output_dirs["06_tables"] / f"analysis_{ws}.xlsx")
        all_rows += rows

    write_metadata_csv(all_rows, settings.output_dirs["02_metadata"] / "metadata_master.csv")
    write_rayyan(all_rows, settings.output_dirs["02_metadata"] / "rayyan_ready.csv")
    write_simple_csv(extraction_manifest, settings.output_dirs["05_extraction"] / "extraction_manifest.csv")

    master = build_master_rows(all_rows)
    write_synthesis_outputs(master, settings.output_dirs["06_tables"])

    q_items = build_questionnaire_candidates(master)
    fw_items = build_framework_components(master)

    pd.DataFrame(q_items).to_excel(settings.output_dirs["06_tables"] / "NUTEV_QUESTIONNAIRE_ITEM_CANDIDATES.xlsx", index=False)
    pd.DataFrame(fw_items).to_excel(settings.output_dirs["06_tables"] / "NUTEV_FRAMEWORK_COMPONENTS.xlsx", index=False)

    write_qualification_outputs(master, q_items, fw_items, settings.output_dirs["06_tables"], settings.output_dirs["08_docs"])
    write_methods_docs(settings.output_dirs["08_docs"])

    prisma = build_prisma_flow(master, all_manifest, extraction_manifest)
    export_prisma(prisma, settings.output_dirs["06_tables"] / "NUTEV_PRISMA_FLOW.xlsx", settings.output_dirs["07_logs"] / "prisma_flow.json")

    summary = {
        "workstreams": workstreams,
        "records": len(all_rows),
        "downloads_ok": total_downloads,
        "downloads_failed": total_failed,
        "ocr_docs": total_ocr,
    }
    write_run_summary(settings.output_dirs["07_logs"] / "run_summary.json", summary)
    (settings.output_dirs["07_logs"] / "run_summary_pretty.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in summary.items()),
        encoding="utf-8",
    )
    return summary