from __future__ import annotations
from pathlib import Path
import pandas as pd
from nutev.utils import write_text
from nutev.export.excel_writer import write_excel_sheet, write_excel_file


def _write_workbook_or_csv(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with pd.ExcelWriter(path) as writer:
            for name, frame in sheets.items():
                write_excel_sheet(writer, frame, name)
    except Exception:
        for name, frame in sheets.items():
            frame.to_csv(path.with_suffix(f".{name[:31]}.csv"), index=False, encoding="utf-8-sig")
        path.touch()

def write_qualification_outputs(master_rows: list[dict], q_items: list[dict], fw_items: list[dict], out_tables: Path, out_docs: Path) -> None:
    df = pd.DataFrame(master_rows)
    out_tables.mkdir(parents=True, exist_ok=True)
    out_docs.mkdir(parents=True, exist_ok=True)

    gaps = df.groupby("workstream").size().reset_index(name="n_docs")
    gaps["gap_flag"] = gaps["n_docs"].apply(lambda x: "alta" if x < 20 else "baixa")

    recs = df.sort_values("score", ascending=False).head(100)[["workstream", "title", "domains", "translation_potential"]].rename(columns={"title": "evidência_origem"})
    recs["regra_sugerida"] = "Aplicar recomendação alinhada ao domínio predominante"
    recs["tipo_de_regra"] = "recomendação alimentar"
    recs["nível_de_confiança"] = "médio"
    recs["precisa_supervisao"] = "sim"
    recs["observação"] = "heurístico"

    sheets = {"overview": df}
    for ws, sn in [("busca1", "artigo1_busca1"), ("busca2a", "artigo2_busca2a"), ("busca2b", "artigo2_busca2b"), ("a3", "artigo3_framework")]:
        sheets[sn] = df[df.workstream == ws]
    sheets.update({"documentos_prioritarios": df.sort_values("score", ascending=False).head(200), "lacunas_de_evidencia": gaps, "recomendacoes_operacionais": recs, "candidatos_questionario": pd.DataFrame(q_items), "componentes_framework": pd.DataFrame(fw_items)})
    _write_workbook_or_csv(out_tables / "NUTEV_QUALIFICACAO_MASTER.xlsx", sheets)

    write_excel_file(gaps, out_tables / "NUTEV_LACUNAS_DE_EVIDENCIA.xlsx")
    write_excel_file(recs, out_tables / "NUTEV_RECOMENDACOES_OPERACIONAIS.xlsx")
    write_excel_file(recs, out_tables / "NUTEV_PROTOCOL_RULES.xlsx")
    write_excel_file(gaps, out_tables / "NUTEV_EVIDENCE_GAPS.xlsx")

    map_sheets = {}
    for ws, sn in [("busca1", "artigo1"), ("busca2a", "artigo2a"), ("busca2b", "artigo2b"), ("a3", "artigo3")]:
        part = df[df.workstream == ws].copy()
        part["papel_na_tese"] = "fundamentação"
        part["potencial_de_uso"] = part["translation_potential"]
        map_sheets[sn] = part
    _write_workbook_or_csv(out_tables / "NUTEV_ARTICLE_EVIDENCE_MAP.xlsx", map_sheets)

    for ws in ["busca1", "busca2a", "busca2b", "a3"]:
        part = df[df.workstream == ws]
        txt = (
            f"# SUMMARY {ws.upper()}\n\n"
            f"- volume documental: {len(part)}\n"
            f"- principais fontes: {part['source'].value_counts().head(5).to_dict()}\n"
            f"- domínios frequentes: {part['domains'].value_counts().head(5).to_dict()}\n"
            f"- padrões dietéticos: {part['diet_pattern'].value_counts().head(5).to_dict()}\n"
            f"- tradução prática: {part['translation_potential'].value_counts().head(5).to_dict()}\n"
        )
        write_text(out_docs / f"NUTEV_SUMMARY_{ws.upper()}.md", txt)

    write_text(out_docs / "NUTEV_QUALIFICACAO_NOTES.md", "Notas automáticas de qualificação geradas do evidence master.")
    write_text(out_docs / "NUTEV_RESULTS_SNAPSHOT.md", f"Registros consolidados: {len(df)}")
    write_text(out_docs / "NUTEV_LIMITATIONS.md", "Limitações: dependência de APIs externas, OCR depende de Tesseract/poppler.")
    write_text(out_docs / "NUTEV_NEXT_STEPS.md", "Próximos passos: revisão humana, refinamento de regras e síntese final de tese.")