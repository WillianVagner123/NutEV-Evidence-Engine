# NUT-EV / ARTIGO 1 — PROMPT MASTER DE FECHAMENTO

**Objetivo:** fechar tecnicamente o produto NutEV para o Artigo 1 e levar a revisão até o último ponto cientificamente permitido antes das decisões humanas que abrem PRESS/GF-10/freeze/busca formal/PRISMA.

**Pesquisador responsável:** Willian Vagner  
**Orientador:** Dr. Caio Reis  
**Workspace esperado:** `Doutorado — Willian Vagner`  
**Projeto esperado:** `Artigo 1`  
**ResearchApplication esperada:** `SCOPING_REVIEW`

> Este documento é um prompt operacional e científico. Ele não substitui
> `ARTICLE1_SEARCH_MASTER.md` nem `config/nutev/article1_search_master_v1.json`.
> O runtime e os arquivos canônicos vencem qualquer snapshot descrito aqui quando houver divergência.

---

## 0. REGRA-MÃE

Trabalhe em uma sequência única:

```text
PROVAR RUNTIME
→ FECHAR PRODUTO
→ PROVAR ACESSO AO A1
→ MATERIALIZAR FILAS / REVIEW SEM JULGAMENTO
→ CONSOLIDAR PRESS PREP
→ PARAR NOS GATES HUMANOS
→ REGISTRAR HANDOFF FINAL
```

Não reconstruir autenticação, tenancy, projetos, ResearchApplication, Review ou deploy se a capacidade já existir.

Não confundir:

- discovery com PRISMA;
- retrieval com inclusão;
- rota com elegibilidade;
- rank/Tier com qualidade;
- full text disponível com inclusão;
- ResearchApplication configurada com aprovação científica;
- acesso do orientador com aprovação metodológica.

---

## 1. ESTADO CIENTÍFICO INVARIANTE

Enquanto não houver decisão humana explícita e rastreável:

```text
Discovery = concluído
PRESS = PENDENTE / NÃO PASS
GF-10 = NÃO AUTORIZADO
Query freeze = PENDENTE
Formal provider search = NÃO EXECUTADA
Formal PRISMA search event = NÃO CRIADO
C4 = NÃO APROVADO
```

Nenhuma etapa técnica pode mudar isso.

Pergunta canônica:

> Quais parâmetros nutricionais, competências alimentares e contextos sociais da alimentação são atualmente recomendados, estruturados e utilizados por diretrizes e modelos operacionais para orientar avaliação, aconselhamento, prescrição e monitoramento alimentar aplicáveis à Medicina do Estilo de Vida?

---

# ETAPA 1 — FECHAMENTO DO PRODUTO / RUNTIME

## Entrada

- conta de Willian existente e ativa;
- workspace/projeto já materializados ou provisionáveis por ferramenta oficial;
- `SCOPING_REVIEW` ativa;
- produção em `NUTEV_AUTH_MODE=pilot`.

## Fazer

1. verificar `main` exata;
2. verificar SHA implantado;
3. confirmar:
   - conta ativa;
   - `PLATFORM_ADMIN` quando necessário para operação;
   - `WORKSPACE_OWNER`;
   - workspace correto;
   - projeto correto;
   - aplicação ativa;
   - `assembly_id=WILLIAN_DOCTORATE_A1`;
   - `d132_config_version=d132-v1`;
4. confirmar owner pins de A1 no processo real:
   - `NUTEV_A1_WORKSPACE_ID`;
   - `NUTEV_A1_PROJECT_ID`;
5. garantir persistência dos pins entre deploys;
6. fechar flakes de CI em vez de depender de reruns aleatórios;
7. executar os gates locais/CI necessários;
8. deploy exact-SHA;
9. provar produção depois do deploy.

## Saída obrigatória

```text
PRODUCT_RUNTIME = PASS
```

com evidência de:

- SHA main;
- SHA produção;
- health;
- auth mode;
- owner pins;
- aplicação A1;
- CI;
- browser gate;
- multitenant;
- recovery readiness.

Não avançar com uma tela “aparentemente funcionando” se o runtime ainda divergir.

---

# ETAPA 2 — PROVAR AS SUPERFÍCIES DO ARTIGO 1

## Fazer

Com sessão autenticada de Willian e contexto correto:

1. `GET /api/article1/scientific-state` → deve retornar 200;
2. abrir D-132;
3. abrir Biblioteca;
4. abrir Human Review;
5. confirmar acesso às superfícies históricas A1;
6. confirmar B-NORM;
7. confirmar C-STRUCT;
8. confirmar vocabulary audit;
9. confirmar full-text/retrieval surfaces disponíveis;
10. registrar qualquer divergência runtime × arquivos estáticos.

## Não fazer

- não criar dados falsos para preencher tela;
- não inferir ownership por nomes/path;
- não ativar histórico sem owner binding inequívoco;
- não converter contagens históricas em triagem/PRISMA.

## Saída obrigatória

```text
ARTICLE1_SURFACES = PASS
```

ou um blocker técnico exato, reproduzível e rastreado.

---

# ETAPA 3 — SNAPSHOT CIENTÍFICO DE TRABALHO

Confirmar, sem promover esses números a PRISMA:

```text
Discovery bruto: 41.139
Únicos: 33.839
Aceitos estruturalmente: 33.067
Quarentena estrutural: 772

Tier A: 662
Retrieved: 504
Partial: 90
Not retrieved: 68
Retrieved + partial: 594/662 = 89,73%

B-NORM: 85
C-STRUCT: 316
União: 351
Overlap: 50
Unrouted: 311

Vocabulary audit:
B-NORM: 27 candidatos
C-STRUCT: 49 candidatos
```

Se o runtime não confirmar algum número, registrar a divergência e manter o valor apenas como snapshot histórico, nunca como runtime atual.

---

# ETAPA 4 — HUMAN REVIEW READY, SEM JULGAMENTO

## 4.1 Desenho cego S1–S6

Existe um desenho de precisão descrito para 150 registros, 25 por fatia, mas os arquivos S1–S6 não estão canonicamente materializados no runtime/repositório atual. Se esse desenho for mantido, o pacote deve ser regenerado de forma determinística e versionada antes de qualquer julgamento humano:

```text
S1 = B-NORM apenas por standard*
S2 = B-NORM apenas por recommendation*
S3 = o que BN-ALT-ti perderia
S4 = incremento de counsel(l)ing em C1
S5 = incremento exclusivo de C4 sobre C1–C3
S6 = incremento de eating competence
```

## Fazer

- após a regeneração, validar integridade dos 150 registros;
- confirmar reprodutibilidade/manifesto;
- garantir cegamento;
- remover/impedir rank, score, machine relevance e decisão do outro revisor;
- preparar dois revisores independentes;
- preparar adjudicação humana posterior;
- preservar denominadores;
- documentar cobertura de frame;
- manter explícito que S3 tem cobertura incompleta do frame (87,2%).

## Não fazer

Claude/automação NÃO decide Y/N/U e NÃO adjudica.

Pode criar infraestrutura de round, itens, atribuições e estado de pendência somente quando isso não cria uma decisão científica.

---

# ETAPA 5 — D-132

Confirmar o contrato:

```text
config = d132-v1
sample = 100
D02 = 25
D03 = 25
D04 = 25
D05 = 25
decisions = Y / N / U
revisores cegos independentes
adjudicação humana
```

Limitação a preservar:

- o D-132 atual é enviesado para recência como estimativa global de precisão;
- não usar a amostra atual para inferir precisão de todo o incremento.

Preparar duas opções para decisão humana:

```text
A) manter D-132 como exploratório / recency-biased
B) especificar D-132b aleatório/estratificado
```

Não implementar D-132b sem decisão humana explícita.

---

# ETAPA 6 — PRESS PREP: B-NORM

Dados de desenvolvimento já observados no PubMed:

- `standard*` responde por aproximadamente metade do B-NORM atual;
- há hipótese de ruído por usos genéricos de “standard”;
- uma alternativa mais específica, BN-ALT-ti, reduziu fortemente o volume e recuperou os known items normativos usados naquele teste;
- isso NÃO autoriza substituir a rota atual.

## Fazer

Depois da leitura humana S1/S2/S3:

- estimar precisão por fatia;
- registrar perdas relevantes;
- registrar known-item recovery;
- comparar sensibilidade/especificidade de forma descritiva;
- separar:
  - manter;
  - estreitar;
  - testar mais;
  - decisão humana necessária.

Nunca declarar “melhor estratégia” sem decisão metodológica humana.

---

# ETAPA 7 — PRESS PREP: C1–C4

## C1 — CARE PROCESS

Prioridade: incremento de counsel(l)ing e demais termos de care process.

Pergunta operacional:

> O incremento traz estruturas reais de avaliação/aconselhamento/prescrição/monitoramento, ou literatura genérica sem utilidade para a pergunta?

## C2 — COMPETENCY / LITERACY

Manter separados:

- food literacy;
- nutrition literacy;
- food skills;
- culinary skills;
- food agency;
- eating competence;
- professional competence.

Known items perdidos que voltam com termos específicos devem ser tratados como sinal de lacuna, não como autorização automática de inclusão de termo.

## C3 — IMPLEMENTATION

Distinguir implementação estruturada de uso genérico da palavra `implementation`.

Termo solto de alto ruído não entra automaticamente.

## C4 — SOCIAL CONTEXT

C4 continua candidato PRESS não aprovado.

A leitura humana deve responder se o grande incremento acrescenta material necessário ou majoritariamente ruído.

Separar ao menos:

- food environment;
- social determinants;
- social support;
- commensality/eating together;
- family meals;
- food culture;
- food insecurity;
- policy/monitoring.

---

# ETAPA 8 — KNOWN ITEMS

Usar o conjunto atual de 14 sentinelas como ferramenta de desenvolvimento, nunca como prova isolada de validade.

Dar atenção especial às perdas já identificadas:

```text
KI03 — eating competence
KI08 — physician/lifestyle medicine competencies
KI10 — food environments
KI13 — lifestyle medicine / healthy nutrition sem recuperação por variantes testadas
```

Para cada perda:

- confirmar metadados;
- confirmar rota esperada;
- testar por que perdeu;
- identificar bloco ausente;
- registrar custo de recuperação;
- classificar impacto;
- deixar decisão final humana.

---

# ETAPA 9 — MATRIZ CONCEITUAL

Manter matriz de trabalho sem transformar eixos em achados finais.

Eixos candidatos:

1. assessment;
2. dietary quality;
3. intake;
4. dietary pattern;
5. nutrition status;
6. food skills;
7. food literacy;
8. culinary competence;
9. counseling;
10. prescription;
11. goal setting;
12. monitoring;
13. follow-up;
14. behavior change;
15. food environment;
16. social determinants;
17. social support;
18. commensality/shared meals;
19. implementation;
20. professional competencies;
21. eating competence, se mantido como construto separado.

Sempre distinguir:

- relação explícita na fonte;
- interpretação provisória do time.

---

# ETAPA 10 — DECISÕES HUMANAS

## Para Willian

Operacionais/metodológicas que exigem decisão:

- quem serão os dois revisores;
- quem adjudica;
- se D-132 atual fica só exploratório;
- se haverá D-132b;
- quem valida sintaxe Scopus/WoS;
- quem será revisor PRESS independente;
- escopo de bases adicionais para PRESS.

## Para Dr. Caio Reis

Levar apenas decisões acadêmicas:

1. escopo de “parâmetros nutricionais”;
2. aprovação/rejeição/manutenção de C4;
3. `eating competence` dentro de competências alimentares;
4. trade-off B-NORM sensibilidade × especificidade;
5. uso de vocabulário controlado/publication types;
6. assimetria de campos entre PubMed/Scopus/WoS;
7. conjunto de sentinelas;
8. literatura cinzenta/FBDG/Guia Alimentar.

Não sobrecarregar o orientador com bugs ou operação de servidor.

---

# ETAPA 11 — GATE PRESS

Só após:

- revisão humana suficiente das fatias;
- known items revisados;
- sintaxe por provider revisada;
- decisões humanas registradas;
- PRESS independente concluído quando definido;
- pendências críticas fechadas.

Então preparar uma decisão humana explícita:

```text
PRESS = PASS ou REVISE
```

Claude não atribui PASS sozinho.

Se REVISE:
- voltar às rotas/termos indicados;
- rerodar apenas os deltas necessários.

---

# ETAPA 12 — GF-10 / QUERY FREEZE / FORMAL SEARCH

Somente depois de `PRESS = PASS` humano:

1. registrar autorização explícita de GF-10;
2. congelar queries provider-specific;
3. versionar;
4. checksums;
5. registrar versões de provider/sintaxe;
6. executar buscas formais;
7. registrar eventos formais;
8. só então construir PRISMA formal.

Discovery anterior permanece discovery.

---

# ETAPA 13 — FECHAMENTO DE PRODUTO

Antes de declarar o produto fechado:

- nenhum workflow operacional temporário ativo;
- nenhuma senha/token no Git/log;
- PRs obsoletos fechados;
- PRs necessários mergeados;
- CI reproduzível;
- browser gate reproduzível;
- deploy exact-SHA;
- recovery readiness;
- production doctorate audit;
- owner/supervisor isolamento;
- owner pins persistentes;
- documentação de bootstrap;
- documentação de rollback;
- documentação de A1;
- estado científico mostrado corretamente;
- nenhum gate aberto por efeito colateral.

---

# ETAPA 14 — HANDOFF FINAL

Gerar/atualizar, sem sobrescrever canônicos indevidamente:

```text
ARTICLE1_CURRENT_STATE.md
ARTICLE1_PRESS_PREP_V02.md
ARTICLE1_QUERY_DELTA_PLAN.md
ARTICLE1_KNOWN_ITEMS.md
ARTICLE1_CONCEPT_MATRIX_V01.md
ARTICLE1_PENDING_HUMAN_DECISIONS.md
ARTICLE1_CLOSEOUT_REPORT.md
```

O relatório final deve ter:

```text
PRODUCT
main SHA
production SHA
auth mode
workspace/project/application
owner binding
CI/browser/recovery

ARTICLE 1
scientific-state endpoint
corpus/rotas
D-132
Human Review
full text
known items
delta tests
precision samples

SCIENTIFIC GATES
Discovery
PRESS
GF-10
freeze
formal search
PRISMA
C4

PENDING HUMAN DECISIONS
Willian
Dr. Caio Reis

NEXT ACTION
uma única próxima ação concreta
```

---

# CRITÉRIO DE “PROJETO FECHADO”

Existem dois fechamentos diferentes.

## PRODUTO FECHADO

Pode ser declarado quando:

```text
runtime estável
segurança/isolamento comprovados
A1 acessível
Review funcional
deploy/recovery reproduzíveis
owner pins persistentes
documentação operacional suficiente
nenhum blocker técnico conhecido aberto
```

## ARTIGO 1 FORMALMENTE PRONTO PARA BUSCA

Só pode ser declarado quando:

```text
PRESS humano = PASS
GF-10 autorizado
queries congeladas/versionadas
provider syntax validada
```

Esses dois estados não são equivalentes.

---

# REGRA DE EXECUÇÃO AUTÔNOMA

Não parar no primeiro defeito.

Para cada blocker técnico:

```text
reproduzir
→ causa raiz
→ teste que falha
→ correção mínima
→ teste focal
→ gates
→ merge
→ deploy
→ prova de produção
→ documentação
```

Para cada pendência científica:

```text
organizar evidência
→ quantificar
→ preparar comparação
→ registrar incerteza
→ entregar decisão humana
```

Nunca preencher uma lacuna científica com uma decisão automática.
