"""Dissertation/article export: turn a finished run into ready-to-use material.

Reads the pipeline outputs (knowledge base, claims, summaries) and writes a
``09_report/`` bundle: a consolidated Markdown report, an executive summary, a
data-driven evaluation of the articles, an "included studies" table, and a
reference list in BibTeX + RIS (for Word/Zotero/Mendeley/LaTeX).

Nothing here invents findings: it extracts, counts and organizes what the run
produced. Claims/recommendations are surfaced with the human-review caveat.
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip().startswith("["):
        try:
            v = ast.literal_eval(value)
            return v if isinstance(v, list) else []
        except Exception:
            return []
    return [value] if value not in (None, "", "nan") else []


def _first_author_surname(authors: str) -> str:
    if not authors or str(authors) in ("nan", "None"):
        return "Anon"
    first = re.split(r"[;,]", str(authors))[0].strip()
    token = first.split()[-1] if first else "Anon"
    return re.sub(r"[^A-Za-z]", "", token) or "Anon"


def _citation_key(rec: dict, used: set[str]) -> str:
    key = f"{_first_author_surname(rec.get('authors', ''))}{rec.get('year', '') or 'sd'}"
    key = re.sub(r"[^A-Za-z0-9]", "", key) or "ref"
    candidate, i = key, 1
    while candidate in used:
        i += 1
        candidate = f"{key}{chr(96 + i)}"
    used.add(candidate)
    return candidate


def _bibtex(records: list[dict]) -> str:
    used: set[str] = set()
    blocks = []
    for rec in records:
        key = _citation_key(rec, used)
        fields = {
            "title": str(rec.get("title", "") or "").replace("{", "(").replace("}", ")"),
            "author": str(rec.get("authors", "") or "").replace("{", "(").replace("}", ")") or "Autor desconhecido",
            "year": str(rec.get("year", "") or ""),
            "journal": str(rec.get("journal", "") or ""),
            "doi": str(rec.get("doi", "") or ""),
            "url": str(rec.get("url", "") or ""),
        }
        lines = [f"@article{{{key},"]
        lines += [f"  {k} = {{{v}}}," for k, v in fields.items() if v]
        lines.append("}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _ris(records: list[dict]) -> str:
    blocks = []
    for rec in records:
        lines = ["TY  - JOUR"]
        if rec.get("title"):
            lines.append(f"TI  - {rec['title']}")
        for author in re.split(r"\s*;\s*", str(rec.get("authors", "") or "")):
            if author.strip():
                lines.append(f"AU  - {author.strip()}")
        if rec.get("year"):
            lines.append(f"PY  - {rec['year']}")
        if rec.get("journal"):
            lines.append(f"JO  - {rec['journal']}")
        if rec.get("doi"):
            lines.append(f"DO  - {rec['doi']}")
        if rec.get("url"):
            lines.append(f"UR  - {rec['url']}")
        lines.append("ER  - ")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _top(counter: Counter, n: int = 10) -> list[tuple[str, int]]:
    return [(k, v) for k, v in counter.most_common(n) if k not in ("", "nan", "None", None)]


def build_dissertation_report(project_root: Path) -> dict:
    project_root = Path(project_root)
    corpus = _read_jsonl(project_root / "11_knowledge_base" / "corpus.jsonl")
    if not corpus:
        # fall back to the curated metadata if the KB wasn't built
        md = _read_csv(project_root / "02_metadata" / "metadata_master.csv")
        corpus = md.fillna("").to_dict("records") if not md.empty else []
    if not corpus:
        return {"available": False, "message": "Nenhum documento encontrado. Rode o pipeline primeiro (▶ Rodar pipeline)."}

    summary = _read_json(project_root / "07_logs" / "run_summary.json")
    claims = _read_csv(project_root / "06_tables" / "NUTEV_EVIDENCE_CLAIMS.csv")
    recs = _read_csv(project_root / "06_tables" / "NUTEV_RECOMMENDATION_CANDIDATES.csv")

    out_dir = project_root / "09_report"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def _write(name: str, text: str) -> None:
        (out_dir / name).write_text(text, encoding="utf-8")
        written.append(f"09_report/{name}")

    # --- references ---
    _write("referencias.bib", _bibtex(corpus))
    _write("referencias.ris", _ris(corpus))

    # --- included-studies / per-article evaluation table ---
    rows = [
        {
            "titulo": r.get("title", ""),
            "autores": r.get("authors", ""),
            "ano": r.get("year", ""),
            "periodico": r.get("journal", ""),
            "pais": "; ".join(str(x) for x in _as_list(r.get("countries"))),
            "tipo_evidencia": r.get("evidence_type", ""),
            "nivel_evidencia": r.get("evidence_tier", ""),
            "qualidade_periodico": r.get("journal_quality_score", ""),
            "citacoes": r.get("cited_by_count", ""),
            "relevancia": r.get("relevance_score", ""),
            "workstream": r.get("workstream", ""),
            "doi": r.get("doi", ""),
            "url": r.get("url", ""),
        }
        for r in corpus
    ]
    studies = pd.DataFrame(rows)
    studies.to_csv(out_dir / "estudos_incluidos.csv", index=False)
    written.append("09_report/estudos_incluidos.csv")
    try:
        studies.to_excel(out_dir / "estudos_incluidos.xlsx", index=False)
        written.append("09_report/estudos_incluidos.xlsx")
    except Exception:
        pass

    # --- aggregates for the evaluation ---
    tiers = Counter(str(r.get("evidence_tier", "") or "n/d") for r in corpus)
    etypes = Counter(str(r.get("evidence_type", "") or "n/d") for r in corpus)
    countries: Counter = Counter()
    domains: Counter = Counter()
    for r in corpus:
        for c in _as_list(r.get("countries")):
            countries[str(c)] += 1
        for d in _as_list(r.get("domains")):
            domains[str(d)] += 1
    years = [int(r["year"]) for r in corpus if str(r.get("year", "")).isdigit()]
    most_cited = sorted(
        [r for r in corpus if str(r.get("cited_by_count", "")).strip().isdigit()],
        key=lambda r: int(r["cited_by_count"]),
        reverse=True,
    )[:10]

    n_docs = summary.get("records", len(corpus))
    n_unique = summary.get("curated_unique_documents", len(corpus))
    claims_total = summary.get("evidence_claims_total", len(claims))
    claims_support = summary.get("evidence_claims_supported", 0)
    claims_review = summary.get("evidence_claims_needs_review", 0)
    recs_total = summary.get("recommendation_candidates_total", len(recs))
    conflicts = summary.get("conflicting_evidence_total", 0)
    gen_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def _bullets(pairs: list[tuple[str, int]]) -> str:
        return "\n".join(f"- {k}: {v}" for k, v in pairs) or "- (sem dados)"

    # --- executive summary ---
    _write(
        "RESUMO_EXECUTIVO.md",
        f"""# Resumo executivo — NutEV

_Gerado em {gen_at}. **Material de apoio: nenhuma recomendação é final sem revisão humana.**_

- Documentos recuperados: **{n_docs}** ({n_unique} únicos após curadoria)
- Afirmações de evidência (claims): **{claims_total}** ({claims_support} apoiadas · {claims_review} para revisão)
- Recomendações candidatas: **{recs_total}**
- Conflitos de evidência: **{conflicts}**
- Período coberto: **{min(years) if years else 'n/d'}–{max(years) if years else 'n/d'}**
- Países (top): {', '.join(f'{k} ({v})' for k, v in _top(countries, 5)) or 'n/d'}

Arquivos: `estudos_incluidos.xlsx`, `referencias.bib`/`.ris`, `RELATORIO_DISSERTACAO.md`.
""",
    )

    # --- main dissertation report ---
    top_cited_md = "\n".join(
        f"{i}. {r.get('title','(sem título)')} ({r.get('year','s.d.')}) — {r.get('cited_by_count','0')} citações"
        for i, r in enumerate(most_cited, 1)
    ) or "- (sem dados de citação)"

    supported_claims = claims[claims.get("claim_status").astype(str).str.contains("support", case=False, na=False)] if "claim_status" in claims.columns else pd.DataFrame()
    sample_claims = "\n".join(
        f"- **{row.get('title','')[:90]}** ({row.get('year','')}): {str(row.get('claim_text',''))[:240]}"
        for _, row in supported_claims.head(10).iterrows()
    ) or "- (nenhum claim apoiado destacado; veja `06_tables/NUTEV_EVIDENCE_CLAIMS.csv`)"

    _write(
        "RELATORIO_DISSERTACAO.md",
        f"""# Revisão de evidências NutEV — relatório para dissertação/artigos

_Gerado automaticamente em {gen_at}._
> ⚠️ Este é material de **apoio** extraído da coleta automatizada. Os claims e
> recomendações são **candidatos** e exigem **validação humana** antes de uso final.

## 1. Métodos (resumo)
Busca multilíngue e multibase (workstreams: {', '.join(summary.get('workstreams', []) or ['n/d'])}).
O fluxo PRISMA, a estratégia de busca completa, o protocolo (PROSPERO) e o guia de
risco de viés estão em `08_docs/` e `06_tables/NUTEV_PRISMA2020_FLOW.csv`.

- Provedores consultados: {summary.get('providers_started', 'n/d')} execuções de consulta;
  resultados por base em `11_knowledge_base/summary/by_venue.csv`.
- Downloads de texto completo: {summary.get('downloads_ok', 0)} ok / {summary.get('downloads_failed', 0)} apenas metadados.

## 2. Resultados quantitativos
- **Documentos:** {n_docs} (únicos: {n_unique})
- **Claims:** {claims_total} — {claims_support} apoiados, {claims_review} para revisão
- **Recomendações candidatas:** {recs_total} · **Conflitos:** {conflicts}
- **Período:** {min(years) if years else 'n/d'}–{max(years) if years else 'n/d'}

### Por nível de evidência
{_bullets(_top(tiers))}

### Por tipo de evidência
{_bullets(_top(etypes))}

### Por país (top 10)
{_bullets(_top(countries))}

### Por domínio temático (top 10)
{_bullets(_top(domains))}

## 3. Avaliação dos artigos
- **Cobertura:** {len(corpus)} registros únicos analisados, abrangendo {len(countries)} países e
  {len([y for y in set(years)])} anos distintos.
- **Maturidade da evidência:** ver distribuição por nível acima (níveis `a1_*` indicam proxies de
  alta qualidade; revise manualmente os limítrofes).
- **Mais citados (proxy de impacto):**
{top_cited_md}
- **Qualidade de periódico:** coluna `qualidade_periodico` em `estudos_incluidos.xlsx`
  (pontuação por revista); cruze com a lista de periódicos predatórios em
  `config/predatory_journals.json` antes de incluir.

## 4. Claims apoiados (amostra — confirmar citação no texto-fonte)
{sample_claims}

## 5. Recomendações candidatas
{recs_total} candidata(s) em `06_tables/NUTEV_RECOMENDACOES_OPERACIONAIS.xlsx`.
**Não use sem revisão humana** (rastreabilidade em `06_tables/NUTEV_CLAIM_EVALUATIONS.csv`).

## 6. Lacunas e conflitos
- Conflitos de evidência: {conflicts} (`06_tables/NUTEV_CONFLICTS.csv`).
- Lacunas: `06_tables/NUTEV_LACUNAS_DE_EVIDENCIA.xlsx`.

## 7. Como citar / inserir na dissertação
- **Referências:** importe `09_report/referencias.ris` no Zotero/Mendeley/EndNote, ou
  use `referencias.bib` no LaTeX/Overleaf.
- **Tabela de estudos incluídos:** `09_report/estudos_incluidos.xlsx` (cole no Word/planilha).
- **Tabelas de resultados:** prontas em `06_tables/` (PRISMA, evidências, domínios, top documentos).
- **Métodos:** texto-base em `08_docs/NUTEV_METHODS_MASTER.md`.
""",
    )

    return {
        "available": True,
        "written": written,
        "n_documents": len(corpus),
        "n_references": len(corpus),
        "report_dir": "09_report",
    }
