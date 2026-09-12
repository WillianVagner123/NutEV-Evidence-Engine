# POP — Uso do NutEV Reference Engine

**Produto:** NutEV Reference Engine  
**Versão estável publicada:** 1.1.0  
**Plataforma operacional principal:** Windows  
**Python suportado:** 3.12 ou 3.13  
**Fluxo atual:** `SEARCH -> NORMALIZE -> DEDUPLICATE -> TRACEABILITY GATE -> RANK -> EXPORT -> AUDIT`  
**DOI v1.1.0:** `10.5281/zenodo.22726717`  
**Zenodo record:** `22726717`  
**DOI histórico v1.0.0:** `10.5281/zenodo.21998607`

## 1. Objetivo

Padronizar instalação, atualização, execução, verificação e interpretação do Reference Engine sem confundir ranking operacional com decisão científica.

O Engine coleta referências em múltiplas fontes, normaliza metadados, verifica integridade, aplica rastreabilidade/quarentena, deduplica, calcula prioridade explicável e exporta resultados auditáveis. Ele não deve inventar DOI, PMID, PMCID, URL, título ou outro dado para fazer um registro passar pelos guardrails.

## 2. Identidade de release

A tag `v1.1.0` é imutável e aponta para:

```text
49588233ad2828b8fcc6140398ab55aedf7c03ef
```

O GitHub Release e o arquivo Zenodo dessa versão estão publicados. Commits posteriores em `main` mantêm documentação e produto, mas não reescrevem o snapshot da release.

Antes de qualquer execução usada em pesquisa/auditoria, registre:

```bat
git rev-parse HEAD
```

## 3. Instalação e atualização

Primeira instalação:

```bat
cd %USERPROFILE%
git clone https://github.com/WillianVagner123/NutEV-Evidence-Engine.git
cd NutEV-Evidence-Engine
Iniciar-NutEV-Windows.bat
```

Atualização:

```bat
cd %USERPROFILE%\NutEV-Evidence-Engine
git checkout main
git pull --ff-only origin main
git rev-parse HEAD
```

O launcher cria `.venv` quando necessário e usa o pipeline suportado pelo repositório.

## 4. Execução padrão

```bat
Iniciar-NutEV-Windows.bat
```

Perfil profundo, quando realmente necessário:

```bat
set NUTEV_DEEP_COLLECTION=1
Iniciar-NutEV-Windows.bat
```

Depois, para limpar a variável na mesma sessão:

```bat
set NUTEV_DEEP_COLLECTION=
```

Limites maiores não significam busca exaustiva.

## 5. Critério de sucesso operacional

A execução deve terminar sem erro nas etapas de coleta/ranking e gerar, no mínimo:

```text
project_output_reference/reference_ranking/TOP_REFERENCIAS.md
project_output_reference/reference_ranking/reference_ranking.csv
project_output_reference/reference_ranking/reference_ranking.jsonl
project_output_reference/reference_ranking/reference_quarantine.jsonl
project_output_reference/reference_ranking/AUDIT_MANIFEST.json
project_output_reference/reference_ranking/latest.json
```

`COMPLETE_WITH_QUARANTINE` não é necessariamente falha: significa que registros sem rastreabilidade suficiente foram separados do ranking.

## 6. Integridade e rastreabilidade

Masters declarados devem possuir caminho e SHA-256 no manifesto. Divergência de hash deve interromper a execução; não ajuste o manifesto para esconder modificação de input.

A identidade/deduplicação usa o contrato canônico do Engine, com identificadores/URL/título normalizado conforme a implementação vigente. Isso é deduplicação determinística, não prova de equivalência intelectual entre versões/preprints/traduções.

Registros sem origem/rastreabilidade suficiente permanecem em quarentena. Corrija a informação na fonte ou na coleta com evidência verificável; não preencha por suposição.

## 7. Auditoria mínima

Preserve junto com o SHA do Git:

```text
07_logs/collect_everything/latest.json
07_logs/latin_native/latest.json
reference_ranking/latest.json
reference_ranking/AUDIT_MANIFEST.json
reference_ranking/reference_ranking.csv
reference_ranking/reference_ranking.jsonl
reference_ranking/reference_quarantine.jsonl
```

No `AUDIT_MANIFEST.json`, confirme status de auditoria, hashes/configurações de entrada e hashes dos outputs.

Hashes demonstram integridade relativa aos arquivos registrados; não certificam a verdade científica dos metadados externos.

## 8. Providers e falhas

O produto consulta somente providers realmente configurados/suportados. Estados `401`/`403`, indisponibilidade, rate limit ou credencial ausente devem ser registrados como falha/indisponibilidade/configuração ausente — nunca como “zero literatura”.

Scopus e Web of Science não são simulados sem acesso licenciado. Providers opcionais dependem de suas credenciais.

## 9. Interpretação do ranking

Score/faixa/rank são **prioridade operacional de leitura**. Não são, isoladamente:

- qualidade metodológica;
- elegibilidade científica;
- risco de viés;
- certeza da evidência;
- força de recomendação;
- decisão clínica.

O estado científico geral do produto continua `B — DEMOTE` enquanto não houver benchmark independente suficiente para promover essa conclusão.

## 10. Interrupção, retomada e outputs

Não apague `project_output_reference` ou checkpoints por padrão. Runs concluídos e seus manifests devem ser preservados quando fizerem parte de pesquisa/auditoria.

Código `130` normalmente representa interrupção por `Ctrl+C`; investigue antes de repetir ou remover estado.

Outputs científicos/operacionais não devem ser versionados no repositório público por padrão, especialmente quando contiverem dados privados, material protegido ou estado de projetos.

## 11. Evidência histórica

A execução Windows real de 18/08/2026 continua preservada como evidência histórica em:

[`archive/2026/VALIDATED_WINDOWS_RUN_2026-08-18.md`](archive/2026/VALIDATED_WINDOWS_RUN_2026-08-18.md)

Ela descreve o software/taxonomia daquele momento e **não** é baseline obrigatório da `main` atual.

## 12. Mudanças que exigem atualização de testes/documentação

Qualquer alteração de providers, consultas/limites, identidade/deduplicação, guardrails, taxonomia, pesos, outputs, manifestos ou interpretação científica deve atualizar testes e documentação e passar pelos gates normais antes do merge.

## Referências

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`AUDITABILITY_AND_GUARDRAILS.md`](AUDITABILITY_AND_GUARDRAILS.md)
- [`SEARCH_PROVIDERS.md`](SEARCH_PROVIDERS.md)
- [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md)
- [`RELEASE_NOTES_1_1_0.md`](RELEASE_NOTES_1_1_0.md)
- [`ZENODO_SETUP.md`](ZENODO_SETUP.md)
- [`../validation/SCIENTIFIC_VALIDATION_STATUS.md`](../validation/SCIENTIFIC_VALIDATION_STATUS.md)
