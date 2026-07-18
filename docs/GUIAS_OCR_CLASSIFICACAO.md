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
#   --discover-fao -> descobre TODOS os países AO VIVO no site da FAO
#                     (nome oficial + ano + os PDFs reais de cada guia),
#                     em vez do manifesto fixo. É o "pegar todos" de verdade.
#   --workers 8    -> 8 guias em paralelo (mais rápido; padrão 4)
#   --limit 20     -> processa só os 20 primeiros (teste rápido)
#   --offline      -> não baixa; só processa PDFs já em 03_corpus/03C_official_docs
#   --rate 1.0     -> 1s entre downloads por worker (mais educado com os servidores)
#   --report       -> gera o relatório de corpus (dedup fuzzy + clusters + heatmap)
#   --fresh        -> ignora o checkpoint e refaz tudo do zero
```

### Relatório de corpus (`--report`)

Precisa das dependências opcionais: `pip install -e ".[report]"` (scikit-learn +
matplotlib). Com `--report`, além das tabelas normais, o comando gera:

- **`NUTEV_GUIDES_REPORT.xlsx`** — abas: `DOCUMENTS` (com `cluster_id`,
  `dedup_group`, `dedup_is_duplicate_of`), `DUPLICATES` (pares parecidos com o
  score de similaridade) e `THEME_BY_CLUSTER` (média A/B/C/D por cluster).
- **`NUTEV_GUIDES_THEME_HEATMAP.png`** — mapa de calor dos domínios por cluster.

O que ele faz: **dedup por conteúdo** (TF-IDF + cosseno — pega traduções e
reedições que o dedup por identificador não pega) e **clusterização temática**
(KMeans). Sem as dependências instaladas, ele é **pulado com um aviso** (não
quebra o resto). Tudo assistivo, sob revisão humana.

### Descoberta FAO ao vivo (`--discover-fao`)

Sem essa flag, o comando usa o **manifesto fixo** de países. Com
`--discover-fao`, ele **rastreia o registro FBDG da FAO na hora**: acha *todos*
os países, lê **nome oficial** e **ano de publicação**, e pega os **arquivos de
download reais** de cada guia (um "source" por PDF). Depois cada arquivo passa
pelo mesmo fluxo: OCR → A/B/C/D → frases-chave → referência → checkpoint.

```bash
nutev guides --project-root SAIDA --discover-fao --workers 8
```

### Salvar & continuar (checkpoint)

Cada guia é gravado no **checkpoint** (`07_logs/guides_checkpoint.jsonl`) assim
que termina. Se a execução parar no meio (queda de rede, você fechou o terminal),
**é só rodar o mesmo comando de novo** — ele retoma de onde parou, sem
re-baixar nem re-OCR o que já foi feito. Para recomeçar do zero, use `--fresh`.

### Mais rápido

- **Paralelo**: `--workers N` baixa e faz OCR de N guias ao mesmo tempo (o
  tesseract roda como subprocesso, então as threads realmente paralelizam).
- **Não repete trabalho**: o checkpoint faz a re-execução pular o que já está
  pronto; PDFs com texto nativo nem passam pelo OCR.

> Windows: o `tesseract` precisa estar instalado (você já tem o 5.5.0). O
> renderizador de PDF é o **PyMuPDF** (vem no `pip install`, não precisa do
> poppler). Se ativar o venv der erro de permissão, use
> `.\.venv\Scripts\python.exe -m nutev guides --project-root SAIDA`.

### OCR (agora bem melhor)

O OCR antes rodava **só em inglês, sem preparo de imagem** — péssimo para guias em
português/espanhol. Agora:

- **multilíngue** por padrão (`por+eng+spa`); troque com a variável de ambiente
  `NUTEV_OCR_LANG` (ex.: `por+eng+spa+fra+ita`). Os pacotes de idioma precisam
  estar instalados no tesseract (ex.: `tesseract-ocr-por`); se faltar, cai para
  inglês em vez de falhar;
- **prepara a imagem** (tons de cinza + autocontraste + amplia páginas de baixa
  resolução) e renderiza a **300 DPI** (repetindo a 450 se sair fraco);
- usa engine LSTM (`--oem 1 --psm 3`), configurável por `NUTEV_OCR_CONFIG`.

> Windows — instalar o idioma português no tesseract: baixe `por.traineddata`
> de `github.com/tesseract-ocr/tessdata` e coloque em
> `C:\Program Files\Tesseract-OCR\tessdata\`.

## O que sai

| Arquivo | Conteúdo |
|---|---|
| `06_tables/NUTEV_GUIDES_CODED.csv` | **Uma linha por guia**: país, emissor, `sha256`, `fulltext_status`, se usou OCR, `profile` (ex.: `ABCD`), os 4 domínios, nº de frases-chave, termos frequentes e o bloco de frases-chave. |
| `10_curated/guides_coded.json` | Detalhe completo por guia, incluindo a **lista** de frases-chave (`{domain, actionable, sentence}`). |
| `07_logs/guides_summary.json` | Contagem: guias no manifesto, processados, com texto, quantos via OCR, total de frases-chave, distribuição por `profile`. |

O texto integral extraído/OCR fica em `04_ocr_text/` e `05_extraction/`.

## As frases-chave — com a referência e a página

Para cada domínio, o extrator pega as **sentenças verbatim** que contêm um termo
do domínio, priorizando as que também têm um **verbo de recomendação**
(`recommends`, `should`, `deve`, `recomenda`…) — a mesma regra de
"substantividade" da codificação.

Cada frase carrega **a referência em si** (não só o texto): a **citação** do
documento-fonte + a **página** onde a frase aparece + o `source_url` + o
`sha256` do arquivo arquivado. Assim toda frase é citável e rastreável:

```
[A] (p.12) O guia recomenda aumentar o consumo de frutas e hortaliças…
    ↳ referência: Ministério da Saúde. Guia Alimentar para a População Brasileira.
      Brazil. 2014. Disponível em: https://… . Acesso em: 2026-07-16. SHA-256: ab12…
```

A citação completa sai na coluna `reference` da tabela e em cada item de
`key_phrases` no `guides_coded.json` (`{domain, actionable, sentence, page,
reference, source_url, sha256}`).

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
