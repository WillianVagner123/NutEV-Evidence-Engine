# NutEV · Explorador Aberto de Evidências

Página pública, sem login e sem servidor, para buscar literatura de Medicina e Nutrição do Estilo de Vida e entender a qualidade do dado de cada registro: nível A/B/Q de rastreabilidade, completude dos metadados, eixos MEV/NEV, tipo documental e a conta completa da prioridade de leitura.

*Public, login-free, server-less page to search Lifestyle Medicine and Lifestyle Nutrition literature and understand each record's data quality with the same public rules as the NutEV Reference Engine.*

## Usar

- **Online:** a página é publicada pelo workflow `open-explorer-pages` no GitHub Pages.
- **Local:** abra `index.html` no Chrome/Edge, ou rode `python -m http.server 8000 --directory apps/nutev-open` e acesse `http://localhost:8000`.
- **Seus próprios resultados:** aba **Abrir arquivo** aceita `reference_ranking.jsonl`, `reference_ranking.csv`, `reference_quarantine.jsonl` ou um JSON exportado aqui. Tudo é processado no navegador.
- **Compartilhar:** o endereço da página guarda a busca (`#q=...&src=...&n=...`).

## Arquivos

| Arquivo | Papel |
| --- | --- |
| `core.js` | port fiel das regras do Engine (testado contra o Python) |
| `sources.js` | único arquivo com acesso à rede: Europe PMC, PubMed, OpenAlex, Crossref |
| `app.js` | interface |
| `i18n.js` | textos PT-BR / EN |
| `presentation.json` | rótulos de famílias MEV/NEV e rótulos EN dos eixos |
| `data/nutev-open-data.js` | **gerado** por `python tools/build_open_explorer_data.py` |
| `build-info.js` | identidade da publicação (sobrescrito no deploy) |

Ao mudar taxonomia, pesos ou rótulos, rode `python tools/build_open_explorer_data.py` e `PYTHONPATH=src python -m pytest -q nutev_tests/test_open_explorer.py`.

## Limites

O nível do dado e a ordenação descrevem rastreabilidade e organização técnica dos metadados. Não representam qualidade metodológica, elegibilidade, risco de viés, certeza da evidência, força de recomendação ou recomendação clínica. Scopus e Web of Science nunca são simulados. Contrato completo: [`docs/OPEN_EVIDENCE_EXPLORER.md`](../../docs/OPEN_EVIDENCE_EXPLORER.md).
