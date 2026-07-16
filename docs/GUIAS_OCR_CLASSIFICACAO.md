# Guias → OCR → classificação A/B/C/D → frases-chave

Fluxo único que **pega todos os guias** do manifesto (~140 países), **lê o texto**
(OCR quando o PDF é escaneado), **classifica** nos domínios A/B/C/D e **extrai as
frases-chave** (as sentenças que sustentam cada domínio) + os termos mais
frequentes de cada documento.

Tudo é **assistivo** e entra em revisão humana — o sistema sugere e mede, não
decide. Não fura paywall nem fabrica texto.

## Rodar (na sua máquina, com internet + tesseract instalado)

```bash
# 1) instalar com o extra de documentos (traz PyMuPDF + pytesseract p/ OCR)
pip install -e ".[documents]"

# 2) rodar o fluxo completo (baixa, OCR, classifica, frases-chave)
nutev guides --project-root SAIDA

# opções úteis:
#   --limit 20     -> processa só os 20 primeiros (teste rápido)
#   --offline      -> não baixa; só processa PDFs já em 03_corpus/03C_official_docs
#   --rate 1.0     -> 1s entre downloads (mais educado com os servidores)
```

> Windows: o `tesseract` precisa estar instalado (você já tem o 5.5.0). O
> renderizador de PDF é o **PyMuPDF** (vem no `pip install`, não precisa do
> poppler). Se ativar o venv der erro de permissão, use
> `.\.venv\Scripts\python.exe -m nutev guides --project-root SAIDA`.

## O que sai

| Arquivo | Conteúdo |
|---|---|
| `06_tables/NUTEV_GUIDES_CODED.csv` | **Uma linha por guia**: país, emissor, `sha256`, `fulltext_status`, se usou OCR, `profile` (ex.: `ABCD`), os 4 domínios, nº de frases-chave, termos frequentes e o bloco de frases-chave. |
| `10_curated/guides_coded.json` | Detalhe completo por guia, incluindo a **lista** de frases-chave (`{domain, actionable, sentence}`). |
| `07_logs/guides_summary.json` | Contagem: guias no manifesto, processados, com texto, quantos via OCR, total de frases-chave, distribuição por `profile`. |

O texto integral extraído/OCR fica em `04_ocr_text/` e `05_extraction/`.

## As frases-chave

Para cada domínio, o extrator pega as **sentenças verbatim** que contêm um termo
do domínio, priorizando as que também têm um **verbo de recomendação**
(`recommends`, `should`, `deve`, `recomenda`…) — a mesma regra de
"substantividade" da codificação. Exemplo real (guia sintético de teste):

```
[A] This national dietary guideline recommends increasing fruit and vegetable intake…
[B] Cooking skills and meal planning are encouraged to build food literacy…
[C] Families should share meals together to strengthen commensality and food culture.
[D] Health services must improve adherence and reduce barriers to implementation.
```

## Também no pipeline principal

O `nutev --project-root SAIDA` (busca1/2a/2b) agora também grava, por documento,
as colunas `track`, `profile`, `domain_A..D`, `n_key_phrases`, `top_terms` e
`key_phrases_text` no `02_metadata/article_data.csv` — a classificação e as
frases-chave aparecem na tabela principal, não só na camada curada.

## Limite honesto

Guias públicos: dá para pegar quase todos. O que estiver atrás de acesso
institucional continua marcado para você baixar pela biblioteca/VPN da UnB — o
sistema não fura paywall. A codificação A/B/C/D e as frases são **sugestões**
para o seu olho humano confirmar.
