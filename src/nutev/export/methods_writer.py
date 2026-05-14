from __future__ import annotations
from pathlib import Path
from nutev.utils import write_text

def _method_doc(workstream: str) -> str:
    return f"""# NUTEV METHODS - {workstream.upper()}\n\n## objetivo\nExecutar captura local de evidências para {workstream}.\n\n## fontes consultadas\nOpenAlex, Europe PMC, PubMed e fontes oficiais do manifest.\n\n## lógica de querypacks\nQueries derivadas de config/keyword_taxonomy.json por workstream.\n\n## critérios de captura\nResultados dos providers + manifest oficial.\n\n## critérios de download\nFiltro por tipo/extensão e relevância de URL com deduplicação por URL/conteúdo.\n\n## lógica de OCR\nPDF: texto nativo primeiro; sem texto, OCR por página. Imagens: OCR direto.\n\n## regras de scoring\nScoring por keyword/source/workstream via config/scoring_rules.json.\n\n## análise por domínios\nRegras domain_rules_{workstream}.json quando aplicável.\n\n## outputs gerados\nTabelas 02_metadata, 05_extraction, 06_tables e logs 07_logs.\n\n## limitações reais\nDependência de disponibilidade de APIs e Tesseract/poppler local para OCR robusto.\n"""

def write_methods_docs(docs_dir: Path) -> None:
    for ws in ["busca1","busca2a","busca2b","a3"]:
        write_text(docs_dir / f"NUTEV_METHODS_{ws.upper()}.md", _method_doc(ws))
    write_text(docs_dir / "NUTEV_METHODS_MASTER.md", "\n\n".join(_method_doc(ws) for ws in ["busca1","busca2a","busca2b","a3"]))
