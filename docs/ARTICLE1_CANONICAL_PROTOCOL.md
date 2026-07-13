# Artigo 1 NutEV — Protocolo canônico e plano de execução

**Versão:** 2026-07-13-v1  
**Status:** pronto para piloto, pendente de aprovação acadêmica final  
**Autores do manuscrito:** Willian Vagner Dorneles Schneider; Caio Eduardo Gonçalves Reis; Luiza Mariana Brito Soares.

## 1. Título

### Português

**Domínios da Nutrição do Estilo de Vida em guias alimentares e diretrizes clínicas: revisão de escopo e análise documental para subsidiar o Protocolo NutEV**

### Inglês

**Lifestyle Nutrition Domains in Food-Based Dietary Guidelines and Clinical Nutrition Guidance: A Scoping Review and Documentary Analysis to Inform the NutEV Protocol**

## 2. Pergunta de pesquisa

Quais recomendações e domínios alimentares, nutricionais, comportamentais, contextuais e de implementação estão presentes em guias alimentares oficiais e diretrizes clínicas relevantes, e como esses elementos podem subsidiar a arquitetura do Protocolo NutEV?

## 3. Objetivo geral

Mapear, classificar e sintetizar recomendações e domínios relacionados à Nutrição do Estilo de Vida presentes em guias alimentares oficiais e diretrizes clínicas, produzindo uma base documental estruturada para o desenvolvimento posterior do Protocolo NutEV.

## 4. Desenho metodológico

- revisão de escopo;
- análise documental;
- síntese temática;
- apoio computacional auditável;
- seleção, codificação e adjudicação humanas.

O software não determina sozinho elegibilidade, qualidade metodológica ou recomendações finais.

## 5. Dois conjuntos documentais

### 5.1 Camada populacional — Busca 1

Corpus principal:

- guias alimentares nacionais oficiais;
- documentos oficiais de OMS, FAO e organismos supranacionais;
- recomendações governamentais dirigidas à população adulta;
- documentos de implementação diretamente vinculados a um guia alimentar elegível.

Finalidade analítica:

- identificar recomendações alimentares gerais;
- mapear qualidade e composição da dieta;
- identificar processamento, grupos alimentares e padrões alimentares;
- identificar competências alimentares, comensalidade e aspectos de implementação;
- comparar convergências, diferenças e ausências entre países ou regiões.

### 5.2 Camada clínica — Busca 2A

Corpus principal:

- clinical practice guidelines;
- consensos;
- scientific statements;
- position statements;
- documentos oficiais de sociedades científicas.

Condições inicialmente elegíveis:

- obesidade;
- diabetes tipo 2;
- hipertensão;
- dislipidemia;
- doença cardiovascular;
- síndrome metabólica;
- doença hepática esteatótica associada à disfunção metabólica.

Finalidade analítica:

- identificar modificadores clínicos das recomendações populacionais;
- registrar recomendações específicas por condição;
- mapear convergências e conflitos entre documentos clínicos;
- evitar misturar recomendação normativa com comparação de eficácia de intervenções.

## 6. Exclusões centrais

Não integrar ao corpus principal do Artigo 1:

- ensaios clínicos;
- estudos observacionais;
- estudos de intervenção como unidade principal;
- comparações de eficácia entre dietas;
- documentos comerciais;
- opinião sem endosso institucional;
- documentos sem origem verificável;
- versões substituídas quando houver edição vigente.

A Busca 2B e o framework `a3` permanecem disponíveis no projeto geral, mas não compõem a execução canônica do Artigo 1.

## 7. Regra temporal

Para guias e diretrizes oficiais, incluir a versão elegível vigente na data da busca, independentemente do ano de publicação. Limites temporais poderão ser aplicados apenas à literatura bibliográfica complementar, mediante justificativa explícita.

## 8. Domínios analíticos

- **A — Qualidade e composição alimentar:** energia, nutrientes, grupos alimentares, densidade nutricional, processamento, matriz alimentar e padrões alimentares.
- **B — Literacia e competências:** literacia alimentar e nutricional, habilidades culinárias, planejamento, compras, preparo, rotulagem e medicina culinária.
- **C — Comensalidade e contexto:** refeições compartilhadas, ambiente das refeições, cultura, rotina, tempo, acesso e organização doméstica.
- **D — Adesão e implementação:** aceitabilidade, viabilidade, barreiras, facilitadores, alcance, adoção, manutenção e sustentabilidade.

Os domínios funcionam como estrutura inicial. Novos temas podem emergir durante a análise documental e devem ser registrados em diário metodológico.

## 9. Extração mínima obrigatória

Cada documento deverá registrar, no mínimo:

- identificador único;
- título;
- instituição emissora;
- país ou região;
- ano e versão;
- tipo documental;
- população-alvo;
- URL oficial;
- citação textual exata;
- página, seção ou localização do trecho;
- domínio analítico;
- grupo alimentar, nutriente ou padrão;
- dimensão de processamento;
- componente comportamental;
- componente contextual;
- barreira ou facilitador;
- modificador clínico;
- decisão do revisor 1;
- decisão do revisor 2;
- adjudicação.

Metadados isolados não sustentam recomendações. Toda interpretação relevante deve possuir lastro textual verificável.

## 10. Revisão humana

- triagem por dois revisores quando aplicável;
- registro explícito de exclusões;
- divergências encaminhadas a adjudicação;
- distinção entre trecho textual e inferência;
- registro das decisões em arquivo auditável;
- nenhuma `RecommendationCandidate` será tratada como recomendação final.

## 11. Piloto real

A primeira execução deverá utilizar 20 a 30 documentos do mesmo universo que será usado na pesquisa final:

- 12 a 15 guias alimentares oficiais;
- 8 a 10 documentos clínicos;
- 2 a 5 documentos de implementação diretamente relacionados aos documentos principais.

### Critérios de sucesso

- origem oficial confirmada;
- localização dos trechos recuperável;
- classificação documental correta;
- ambiguidades de codificação documentadas;
- decisões humanas persistidas;
- conflitos e insuficiência de evidência registrados;
- nenhuma promoção automática para recomendação final.

## 12. Execução computacional

### Piloto

```powershell
nutev `
  --project-root ./project_output_article1_pilot `
  --workstreams busca1 busca2a `
  --web-enabled

nutev pilot-report `
  --project-root ./project_output_article1_pilot

nutev dashboard `
  --project-root ./project_output_article1_pilot `
  --port 8501
```

### Execução final

A busca definitiva deverá ser executada somente após:

1. aprovação do protocolo;
2. validação do piloto;
3. congelamento dos critérios;
4. correção dos principais falsos positivos;
5. definição dos revisores;
6. registro da estratégia e da versão do código.

Pasta exclusiva:

```text
project_output_article1_final
```

Outputs brutos, curados e finais devem permanecer separados. A execução final não deve reutilizar a pasta do piloto.

## 13. Uso do NutEV Evidence Engine no artigo

### Texto sugerido — português

A identificação, recuperação, organização, deduplicação, classificação preliminar e extração estruturada dos documentos foi apoiada pelo NutEV Evidence Engine, um fluxo computacional de código aberto desenvolvido em Python para pesquisas em Nutrição do Estilo de Vida. O sistema foi utilizado como ferramenta operacional e de rastreabilidade, não realizando decisões autônomas de elegibilidade, avaliação metodológica ou formulação de recomendações. Todos os documentos, trechos extraídos, classificações temáticas e recomendações candidatas foram submetidos à revisão humana. O código-fonte, as configurações utilizadas, os registros de execução e a versão congelada da análise foram disponibilizados em repositório público.

### Suggested text — English

Document identification, retrieval, organization, deduplication, preliminary classification, and structured extraction were supported by the NutEV Evidence Engine, an open-source Python workflow developed for lifestyle nutrition research. The system was used as an operational and traceability tool and did not autonomously determine eligibility, methodological quality, or final recommendations. All documents, extracted passages, thematic classifications, and candidate recommendations underwent human review. The source code, analysis configurations, execution logs, and the frozen version used in this review were made publicly available.

## 14. Artefatos obrigatórios da versão publicada

- protocolo congelado;
- strings e fontes por base;
- manifesto de fontes oficiais;
- arquivo de configuração do Artigo 1;
- commit SHA utilizado;
- versão do software;
- data e hora da execução;
- log de falhas e tentativas;
- tabela de deduplicação;
- motivos de exclusão;
- matriz de extração;
- decisões humanas;
- diagrama PRISMA;
- dicionário de variáveis;
- documentação sobre uso de modelos de linguagem, quando houver.

## 15. Próximas etapas técnicas

1. integrar `config/article1_scope.json` ao CLI por um perfil explícito;
2. criar um comando de validação pré-execução;
3. rodar testes locais antes do piloto;
4. executar o piloto controlado;
5. revisar manualmente os resultados;
6. congelar a versão usada no manuscrito e arquivá-la com DOI.

Este protocolo substitui, para o Artigo 1, execuções amplas que misturem `busca1`, `busca2a`, `busca2b` e `a3` em um único corpus analítico.
