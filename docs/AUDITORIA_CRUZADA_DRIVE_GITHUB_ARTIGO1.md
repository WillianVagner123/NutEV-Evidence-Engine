# Auditoria cruzada: Google Drive × GitHub — Artigo 1 NutEV

**Data:** 13 de julho de 2026  
**Objetivo:** verificar a coerência entre as decisões de orientação, a tese, o protocolo do Artigo 1 e a implementação computacional do repositório `NUT-MEV_NEW`.

## 1. Materiais auditados

### Google Drive

- `ata_reuniao_2026_04_15.docx`;
- `Dissertacao`;
- `ARTIGO 1 — Protocolo de Revisao de Escopo (VERSAO COMPLETA)`;
- `NUTEV_ENGENHARIA_DE_BUSCA_E_PALAVRAS_CHAVE.md`;
- resumos preliminares das buscas 1, 2A e 2B.

### GitHub

- `README.md`;
- `config/keyword_taxonomy.json`;
- `config/nutev_ontology.json`;
- `config/evidence_lenses.json`;
- `config/official_sources_manifest.json`;
- `src/nutev/querypacks/`;
- `src/nutev/search/`;
- `src/nutev/analysis/`;
- `src/nutev/audit/`;
- `src/nutev/review/`;
- `docs/NUTEV_PILOT_REAL_PROTOCOL.md`;
- `docs/VALIDATION_REPORT.md`;
- `docs/NUTEV_REAL_RUN_READINESS_AND_LIMITATIONS.md`.

## 2. Conclusão executiva

O projeto possui boa coerência conceitual geral, mas ainda existem três objetos parcialmente sobrepostos:

1. uma revisão de escopo ampla sobre padrões alimentares, competências alimentares, comensalidade e implementação;
2. um mapeamento documental de guias alimentares e diretrizes de sociedades científicas;
3. uma revisão de intervenções dietéticas e desfechos clínicos.

A reunião de orientação de 15/04/2026 estabeleceu como prioridade imediata a Busca 1, sobre guias alimentares oficiais, e a Busca 2A, sobre documentos de sociedades científicas. A Busca 2B foi tratada como etapa posterior e ainda dependente de delimitação.

Entretanto, o protocolo mais recente do Artigo 1 incluiu simultaneamente estudos empíricos, revisões, diretrizes, documentos institucionais, padrões alimentares, food literacy, medicina culinária, comensalidade e implementação. Esse desenho é cientificamente interessante, mas amplo demais para ser executado com consistência em um único artigo inicial.

**Decisão recomendada:** o Artigo 1 deve ser uma revisão de escopo com análise documental e síntese temática de documentos normativos e orientadores. Seu corpus principal deve ser composto por:

- guias alimentares oficiais dirigidos à população adulta;
- documentos de organismos internacionais;
- diretrizes, consensos e scientific statements de sociedades clínicas selecionadas.

Ensaios clínicos, comparações de eficácia entre dietas e sínteses quantitativas devem permanecer fora do corpus principal do Artigo 1. A Busca 2B deve alimentar o desenvolvimento posterior do Protocolo NutEV ou constituir artigo complementar.

## 3. Escopo canônico recomendado para o Artigo 1

### Título provisório

**Domínios da Nutrição do Estilo de Vida em guias alimentares e diretrizes clínicas: revisão de escopo e análise documental para subsidiar o Protocolo NutEV**

Título em inglês:

**Lifestyle Nutrition Domains in Food-Based Dietary Guidelines and Clinical Nutrition Guidance: A Scoping Review and Documentary Analysis to Inform the NutEV Protocol**

### Pergunta principal

Quais recomendações e domínios alimentares, nutricionais, comportamentais, contextuais e de implementação estão presentes em guias alimentares oficiais e diretrizes clínicas relevantes, e como esses elementos podem subsidiar a arquitetura do Protocolo NutEV?

### PCC

- **População:** adultos e documentos de orientação dirigidos à população adulta, incluindo adultos com obesidade ou risco cardiometabólico quando o documento possuir finalidade clínica.
- **Conceito:** recomendações alimentares e nutricionais; qualidade da dieta; processamento; padrões alimentares; competências alimentares; comensalidade; viabilidade; contexto; adesão e implementação.
- **Contexto:** guias alimentares oficiais, documentos de organismos internacionais, diretrizes clínicas, consensos e scientific statements de sociedades científicas.

## 4. Critérios de elegibilidade recomendados

### Incluir

- versão oficial e vigente do documento no momento da busca;
- documento dirigido à população adulta ou ao cuidado clínico de adultos;
- guia alimentar baseado em alimentos;
- diretriz clínica, consenso, position statement, scientific statement ou documento institucional com recomendações alimentares explícitas;
- publicação em português, inglês ou espanhol;
- texto completo acessível;
- origem institucional verificável.

### Excluir

- ensaios clínicos e estudos observacionais como unidade principal de análise;
- revisões sistemáticas usadas como substitutas do documento normativo original;
- materiais promocionais, comerciais ou opinativos sem método institucional;
- documentos exclusivamente pediátricos, gestacionais ou hospitalares;
- documentos sem recomendação alimentar identificável;
- versões antigas quando existir atualização substitutiva, salvo quando necessárias para análise histórica explicitamente planejada.

## 5. Estrutura analítica recomendada

A extração deve usar codificação dedutiva e indutiva. A estrutura inicial deve incluir:

1. qualidade global da dieta;
2. alimentos e grupos alimentares;
3. composição nutricional;
4. processamento e matriz alimentar;
5. padrões alimentares;
6. planejamento, compras e preparo;
7. food literacy e nutrition literacy;
8. competências culinárias;
9. comensalidade e contexto das refeições;
10. custo, acesso, tempo e viabilidade;
11. cultura e adaptação regional;
12. sustentabilidade;
13. adesão, barreiras e facilitadores;
14. implementação e comunicação;
15. articulação com outros pilares da Medicina do Estilo de Vida;
16. modificadores clínicos por condição.

Os códigos A/B/C/D do protocolo atual podem ser preservados como macrodomínios:

- **A:** qualidade e composição alimentar;
- **B:** literacia, competências e medicina culinária;
- **C:** comensalidade e contexto da refeição;
- **D:** adesão, viabilidade e implementação.

Contudo, a classificação combinatória `A`, `AB`, `AC`, `ABCD` deve ser tratada como uma variável de síntese, não como substituta da codificação temática detalhada.

## 6. Correspondência Drive × GitHub

| Requisito científico | Situação no Drive | Situação no GitHub | Decisão |
|---|---|---|---|
| Busca 1 — guias oficiais | Prioridade definida | `busca1` implementada | Manter como corpus principal |
| Busca 2A — diretrizes clínicas | Prioridade definida | `busca2a` implementada | Manter como lente clínica separada |
| Busca 2B — intervenções | Posterior e ainda ampla | `busca2b` extensa | Não integrar ao corpus principal do Artigo 1 |
| Framework comportamental | Produto posterior | `a3/artigo3_framework` implementado | Não usar como corpus principal |
| Food literacy e culinária | Presentes no protocolo | Bem cobertas na taxonomia | Manter como domínios de análise |
| Comensalidade | Presente no protocolo | Presente na taxonomia | Manter |
| Implementação | Presente no protocolo | Muito ampliada no código | Restringir ao que aparece nos documentos elegíveis |
| Países e origem oficial | Pedido do orientador | Manifesto ainda pequeno | Expandir de forma sistemática |
| Revisão humana | Prevista | Checklist e fila existentes | Tornar obrigatória e documentada |
| Recomendações finais | Não devem surgir no Artigo 1 | Sistema gera candidatas | Manter status apenas de candidata |

## 7. Divergências relevantes encontradas

### 7.1 “Obesidade não clínica”

A expressão aparece na pergunta da `busca1`, mas não é uma categoria suficientemente clara para elegibilidade documental. Guias populacionais normalmente não selecionam pessoas por diagnóstico. Recomenda-se substituir por “população adulta” e registrar obesidade/risco cardiometabólico como população ou contexto clínico somente quando aplicável.

### 7.2 Mistura de política pública com prática clínica

A ontologia genérica inclui política, taxação, rotulagem e alimentação escolar. A reunião de orientação determinou não aprofundar política pública, governo e impacto financeiro neste momento. Para o Artigo 1, esses conteúdos podem ser registrados como contexto, mas não devem comandar a pergunta principal.

### 7.3 Manifesto de fontes oficiais incompleto

O arquivo `official_sources_manifest.json` contém fontes de alta autoridade, porém não representa ainda um levantamento internacional sistemático de guias por país. A presença de uma fonte no manifesto não pode ser confundida com amostragem completa.

### 7.4 Busca 1 excessivamente bibliográfica

Um resumo preliminar registrou 1.235 resultados, dos quais apenas um era de fonte oficial. Isso indica que a execução anterior recuperou principalmente artigos indexados, embora o objetivo científico fosse mapear guias oficiais. A estratégia precisa separar:

- identificação do universo de guias por fontes oficiais e diretórios institucionais;
- busca bibliográfica complementar para localizar análises, versões e lacunas.

### 7.5 Período 2014–2026

Esse recorte aparece no protocolo, mas pode excluir guias oficiais vigentes publicados antes de 2014. Para documentos normativos, recomenda-se incluir a versão vigente independentemente do ano, registrando ano de publicação e situação de atualização. O filtro temporal pode ser mantido apenas para literatura bibliográfica complementar.

### 7.6 Avaliação crítica

O protocolo afirma que não realizará avaliação formal de risco de viés, enquanto a tese propõe AGREE II, AGREE-REX, AMSTAR 2, RoB 2, ROBINS-I e GRADE. Para o corpus documental recomendado:

- usar AGREE II ou instrumento equivalente para diretrizes clínicas, quando aplicável;
- usar uma ficha de autoridade, transparência, método e atualidade para guias alimentares e literatura institucional;
- não aplicar ferramentas de ensaios e revisões a documentos que não pertencem a esses desenhos.

## 8. Matriz mínima de extração

Campos obrigatórios:

- identificador único;
- título;
- país/região;
- instituição emissora;
- URL oficial;
- ano e versão;
- idioma;
- tipo documental;
- população-alvo;
- objetivo do documento;
- método declarado de elaboração;
- presença de revisão/consulta pública;
- recomendação ou trecho exato;
- localização da recomendação;
- domínio principal;
- subdomínio;
- força ou linguagem normativa empregada;
- grupo alimentar/nutriente/padrão associado;
- componente comportamental;
- componente contextual;
- barreira ou facilitador;
- modificador clínico;
- aplicabilidade ao NutEV;
- observação do revisor;
- decisão do segundo revisor;
- status de adjudicação.

## 9. Correspondência com os componentes do repositório

- identificação e recuperação: `src/nutev/search/`;
- construção de consultas: `src/nutev/querypacks/`;
- taxonomia: `config/keyword_taxonomy.json`;
- fontes prioritárias: `config/official_sources_manifest.json`;
- classificação: `src/nutev/analysis/`;
- extração de claims: `src/nutev/audit/`;
- revisão e adjudicação: `src/nutev/review/`;
- matrizes e exportações: `src/nutev/export/`;
- logs e rastreabilidade: `07_logs/`;
- documentos curados: `10_curated/`.

## 10. Piloto obrigatório antes da busca final

Executar piloto com 20–30 documentos, porém com composição controlada:

- 12–15 guias alimentares oficiais, cobrindo diferentes regiões;
- 8–10 diretrizes ou statements clínicos;
- 2–5 documentos de implementação diretamente ligados à orientação alimentar.

O piloto deve testar:

- elegibilidade;
- precisão da extração;
- cobertura dos domínios;
- localização das citações;
- classificação documental;
- utilidade das recomendações candidatas;
- necessidade de segundo revisor;
- conflitos entre documentos;
- tempo médio de curadoria.

O piloto não deve utilizar a `busca2b` ampla nem representar resultados definitivos da revisão.

## 11. Plano de execução do Artigo 1

### Fase 1 — congelamento metodológico

- aprovar título, pergunta PCC e critérios;
- definir organismos e sociedades elegíveis;
- fechar matriz de extração;
- decidir ferramenta de avaliação por tipo documental;
- registrar protocolo no OSF.

### Fase 2 — piloto

- selecionar 20–30 documentos;
- rodar o pipeline;
- revisar manualmente todos os documentos;
- calcular concordância e registrar alterações na taxonomia.

### Fase 3 — busca definitiva

- identificar guias oficiais vigentes;
- executar Busca 2A por sociedades e condições clínicas;
- documentar datas, URLs, termos e números recuperados;
- deduplicar versões e registrar atualizações.

### Fase 4 — análise

- codificação temática dedutiva e indutiva;
- dupla revisão de uma amostra ou do corpus, conforme recursos;
- análise de convergências, divergências e omissões;
- síntese separada entre lente populacional e lente clínica.

### Fase 5 — manuscrito

- PRISMA-ScR;
- tabela de documentos incluídos;
- mapa de domínios;
- comparação entre guias populacionais e diretrizes clínicas;
- matriz de implicações para o desenvolvimento posterior do Protocolo NutEV.

## 12. Regra de governança

O Artigo 1 produz um mapa documental e uma arquitetura de domínios. Ele não produz automaticamente recomendações clínicas finais, uma nova dieta ou um protocolo validado. Qualquer saída computacional deve permanecer identificada como classificação preliminar, claim extraído ou recomendação candidata, sujeita a revisão humana.
