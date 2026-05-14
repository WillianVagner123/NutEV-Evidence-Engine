# NUTEV METHODS - BUSCA2A

## objetivo
Executar captura local de evidências para busca2a.

## fontes consultadas
OpenAlex, Europe PMC, PubMed e fontes oficiais do manifest.

## lógica de querypacks
Queries derivadas de config/keyword_taxonomy.json por workstream.

## critérios de captura
Resultados dos providers + manifest oficial.

## critérios de download
Filtro por tipo/extensão e relevância de URL com deduplicação por URL/conteúdo.

## lógica de OCR
PDF: texto nativo primeiro; sem texto, OCR por página. Imagens: OCR direto.

## regras de scoring
Scoring por keyword/source/workstream via config/scoring_rules.json.

## análise por domínios
Regras domain_rules_busca2a.json quando aplicável.

## outputs gerados
Tabelas 02_metadata, 05_extraction, 06_tables e logs 07_logs.

## limitações reais
Dependência de disponibilidade de APIs e Tesseract/poppler local para OCR robusto.
