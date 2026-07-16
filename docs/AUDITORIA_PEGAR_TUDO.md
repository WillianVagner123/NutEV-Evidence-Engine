# Auditoria "pegar tudo" — recuperação de texto integral (P1–P6)

Objetivo: capturar o **máximo recuperável** de texto integral nas duas camadas
(guias e diretrizes), com proveniência auditável, alimentando a extração e a
codificação A/B/C/D — **sem** furar paywall, fabricar texto ou desmontar a
governança científica.

Todas as decisões de inclusão, codificação e interpretação são **humanas**; o
sistema apenas sugere e mede.

## O que foi implementado (nativo em `src/nutev/`, testado)

| Fase | Módulo | O que faz |
|------|--------|-----------|
| **P1** | `acquire/recoverability.py` + `scripts/diagnose_recoverability.py` | Mede o **teto** de recuperável por workstream (DOI/PMID/PMCID/OA%) antes de baixar nada. `--online` confere OA no Unpaywall. Gera `07_logs/fulltext_recoverability.csv/.json` + bloco `recoverability` no `run_summary`. |
| **P2.1** | `acquire/guias_fetcher.py` | Baixa guias oficiais (Trilha 1) reusando o manifesto de ~120 países (`config/official_sources_countries.json`), com proveniência: `source_url`, `access_date` (UTC), `sha256`, emissor, tier AACODS, `fulltext_status`. |
| **P2.2** | `acquire/fulltext_resolver.py` | Resolve OA por diretriz: PMCID existente → DOI/Unpaywall → PMID/elink→PMC → `paywall`. Nunca fabrica nem fura paywall. |
| **P3** (já existia) + **P3+** | `extract/pdf_text.py` | OCR via PyMuPDF+tesseract; **novo**: detector de falha (saída curta / não-textual) + **retry a 400 DPI** (corrige as 4 falhas). |
| **P4** | `extract/smart_extract.py` | **Guard**: só grava `.txt` quando há texto útil — acabou o arquivo vazio de 11–33 bytes gravado em silêncio; a falha vai para o log. |
| **P5** (já existia, #915) | `analysis/article1_coding.py`, `export/article1_reports.py`, `review/human_review.py` | Codificação A/B/C/D assistiva (regra de substantividade), fila de revisão humana com concordância (kappa) e a **Matriz de Integração**. |
| **P6** | proveniência acima + bloco `fulltext_coverage` no `run_summary` | Campos auditáveis por documento; **o pipeline agora escreve automaticamente** `fulltext_coverage` (extraído × só-metadados por workstream) + o teto de recuperabilidade (OA × paywall) no `run_summary.json` e em `07_logs/fulltext_recoverability.csv/.json` — offline, sem rede. |
| **P7** | `pipelines/guides_pipeline.py` + `analysis/keyphrases.py` + `nutev guides` | Fluxo único **pegar todos os guias → OCR → classificar A/B/C/D → frases-chave**. Gera `NUTEV_GUIDES_CODED.csv`, `10_curated/guides_coded.json` e `07_logs/guides_summary.json`. As colunas de classificação e frases-chave também passam a sair no `article_data.csv` do pipeline principal. Ver `docs/GUIAS_OCR_CLASSIFICACAO.md`. |

> Rede: os módulos de aquisição têm a sessão HTTP **injetada** e são testados com
> mocks; as buscas reais rodam na sua máquina (com internet). Nada aqui contorna
> paywall ou ToS.

## Cobertura de full-text observada (run `project_output_final`)

Do `run_summary.json` do run completo (4 workstreams, 4.106 registros):

- **2.714** documentos únicos; **2.059 (75,9%) só metadados** (editoras bloqueiam).
- **310** com texto extraído (era 63 antes do OCR); **12** via OCR.
- Guias (busca1): quase todos recuperáveis (política pública). Diretrizes
  (busca2a/2b): só a **fração open-access** — o resto é acesso institucional.

O **P1 quantifica exatamente** essa fração (OA vs paywall por camada). Rode-o
**antes** de re-coletar para saber o teto real:

```bash
python scripts/diagnose_recoverability.py \
  --metadata project_output_final/02_metadata/article_data.csv \
  --outdir   project_output_final/07_logs
# adicione  --online --email SEU_EMAIL  para conferir OA real no Unpaywall
```

## O que EU (humano) preciso fazer manualmente

1. **Reinstalar e re-rodar** com o código atualizado (`pip install -e .`) para
   que a Matriz A/B/C/D e os campos novos apareçam na saída — o último run foi
   com código antigo (por isso mostra `a3` e não tem `domain_coverage`).
2. **Acesso institucional** aos paywalls: as diretrizes marcadas
   `fulltext_status = paywall` precisam ser obtidas pela sua biblioteca/VPN da
   UnB — o sistema não fura paywall.
3. **Guias FAO faltantes**: rodar `nutev verify-sources` (na máquina com internet)
   e corrigir os 404 do manifesto de países; completar guias que faltam.
4. **Curadoria/codificação humana**: confirmar a codificação A/B/C/D sugerida
   (a concordância humano×sistema/kappa é registrada em
   `human_review_decisions.csv`); remover falsos-positivos (ex.: a revista da OGE
   que entrou como "guia austríaco", docs de HIV como "guia sul-africano").
5. **`UNPAYWALL_EMAIL`** por variável de ambiente para o modo `--online` e o
   resolver.
6. **CITATION.cff / Zenodo**: inserir o DOI após o depósito (ver
   `docs/ZENODO_SETUP.md`) e o ORCID.
7. **Dependabot**: o config foi removido; feche os PRs antigos com
   `scripts/close_stale_prs.sh` (na sua máquina, com `gh`).

## Limite honesto

Guias dá para pegar quase todos (são públicos). **Diretrizes, só a fração
open-access** — o resto depende de acesso institucional. O P1 transforma isso de
promessa em número.
