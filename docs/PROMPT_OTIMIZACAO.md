# Prompt de otimização — NutEV Evidence Engine

Cole o bloco abaixo para um agente de código (Claude Code, etc.) quando quiser
"arrumar tudo e deixar otimizado". Ele é específico deste repositório e já traz
as restrições científicas para o agente não quebrar a governança.

---

```
CONTEXTO
Você vai otimizar o repositório NutEV Evidence Engine (motor de evidências de um
scoping review de nutrição, PhD/PPGNH-UnB). O artigo CITA este repositório, então
correção e reprodutibilidade valem mais que velocidade. Trabalhe SÓ na branch de
desenvolvimento indicada; NUNCA reescreva histórico nem force-push.

O fluxo principal do momento é o comando `nutev guides`:
  descobrir guias (FAO ao vivo ou manifesto) -> baixar (proveniência: sha256,
  data de acesso) -> extrair/OCR -> codificar A/B/C/D -> detecção temática rica
  com trechos-evidência -> frases-chave (página + referência) -> dedup fuzzy +
  clusters + heatmap -> salvar & continuar (checkpoint) -> paralelo por workers.

Módulos-chave:
- src/nutev/pipelines/guides_pipeline.py   (orquestra o fluxo)
- src/nutev/acquire/{fao_discovery,guias_fetcher,fulltext_resolver,recoverability}.py
- src/nutev/extract/{smart_extract,pdf_text,image_ocr}.py   (OCR)
- src/nutev/analysis/{article1_coding,thematic,keyphrases,references,corpus_report}.py
- src/nutev/export/metadata_tables.py, src/nutev/cli.py
- config/thematic_taxonomy.json  (taxonomia multilíngue, editável)
Testes em nutev_tests/. CI: ruff + pytest em Python 3.12/3.13.

OBJETIVO
Deixar o código mais rápido, mais limpo e mais robusto SEM mudar as saídas
científicas (mesmas colunas/valores para a mesma entrada), a menos que seja uma
correção de bug — e nesse caso documente o antes/depois.

RESTRIÇÕES INEGOCIÁVEIS
- Não furar paywall, não burlar ToS, não fabricar texto/dados/referências.
- Toda codificação (A/B/C/D, temas, doc_type) é ASSISTIVA e entra em revisão
  humana; nada vira recomendação clínica final automática.
- Segredos só por variável de ambiente. Não commitar .env, chaves, PDFs
  protegidos, dados pessoais/de paciente, nem saídas reais sem revisão.
- Toda chamada de rede deve ser injetada/mockável (sessão como parâmetro) e
  testada com mocks — o CI não tem internet.
- Manter a suíte verde em cada passo (rode `pytest -q` e `ruff check src nutev_tests`).
- Preservar o copyright © LearningCircuit e a governança científica existente.

TRABALHE EM FASES — um PR pequeno e verde por fase, com prova de paridade.

FASE 1 — Performance (medir antes de mexer)
- Perfilar `nutev guides` (offline, com um corpus de teste) e achar os gargalos
  reais: OCR (render+tesseract), parsing HTML, I/O de disco, serialização JSON.
- OCR: renderizar páginas sob demanda (gerador), não segurar todas as imagens na
  memória; considerar cache do texto extraído por sha256 do arquivo (pular
  re-OCR de um arquivo já lido); paralelizar por página só se valer a pena.
- Rede: reusar uma sessão com pool dimensionado aos workers; throttle por thread
  (não global). Backoff exponencial com jitter em falhas transitórias.
- Evitar recomputar: `load_taxonomy` e configs devem ser lidos uma vez (cache),
  não por documento. TF-IDF do relatório: reusar o vetor entre dedup e cluster.
- Prova: tempo antes/depois no mesmo corpus + mesma saída (diff das tabelas = 0).

FASE 2 — Robustez
- Todo `except Exception` amplo deve logar o motivo e nunca engolir silenciosamente
  um erro que muda a saída. Marcar caminhos "best-effort" vs "deve falhar".
- OCR: tratar PDFs corrompidos, páginas em branco, imagens CMYK/gray, PDFs enormes
  (limite de páginas configurável) sem travar o lote.
- Checkpoint: linha JSONL torta (interrupção) já é ignorada — garanta idempotência
  total e um teste de "matar no meio e retomar".
- Timeouts e limites de tamanho de download configuráveis; nada de download infinito.

FASE 3 — Limpeza / dívida técnica
- Rodar `ruff check src nutev_tests` e zerar F/E genuínos (import morto, var não
  usada, comparação a True/False, nome ambíguo). Não mexer em E402 intencional
  de shims.
- Centralizar utilitários repetidos (normalização de texto, slug, sha256, leitura
  segura de arquivo) em um único módulo em vez de cópias por arquivo.
- Tipos: adicionar type hints onde falta nas funções públicas; `mypy` opcional.
- Cada função pública precisa de um teste; cobrir os ramos de erro.

FASE 4 — "Rodar continuamente" (opcional, se pedirem)
- Modo de re-execução periódica que reusa o checkpoint e só processa guias novos
  ou alterados (comparar sha256/última modificação). Sem duplicar trabalho.
- Métricas por rodada no run_summary (novos, retomados, tempo, falhas).

ENTREGA
- Um PR por fase, título claro, corpo explicando o que mudou e a prova de paridade.
- Não abra PR sem eu pedir; se abrir, não invente credenciais no corpo.
- Ao final, um resumo curto: o que ficou mais rápido (números), o que foi limpo,
  e o que ainda depende de mim (acesso institucional a paywall, rodar com internet).
```

---

## Como usar

1. Copie o bloco entre as crases.
2. Cole no agente, junto com o nome da branch de desenvolvimento.
3. Peça uma fase por vez e revise cada PR antes de mergear.
