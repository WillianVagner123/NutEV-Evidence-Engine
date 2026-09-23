# Article 1 / NutEV — Closeout Report

**Status do documento:** em fechamento ativo. Atualizar o bloco de produção após a última promoção exact-SHA.

## 1. Produto

### Fechado/implementado

- autenticação pilot multiusuário;
- conta de Willian materializada;
- workspace `Doutorado — Willian Vagner`;
- projeto `Artigo 1`;
- `SCOPING_REVIEW`;
- `WORKSPACE_OWNER`;
- Application binding A1;
- `assembly_id=WILLIAN_DOCTORATE_A1`;
- `d132_config_version=d132-v1`;
- server-managed owner pins;
- persistência protegida dos pins entre releases (#1310);
- seleção de contexto no primeiro login;
- browser gate estabilizado para context reload (#1311);
- recuperação/snapshot com volume científico protegido.

### Ainda em fechamento técnico

- SHA final de produção precisa coincidir com a última main de fechamento;
- production doctorate audit deve provar A1 ready após a última promoção;
- remover workflows operacionais one-shot restantes;
- revisar/fechar PRs antigos superados;
- estabilizar o último race de browser logout, se ainda aberto;
- incorporar o Prompt Master e o audit fail-closed.

## 2. Article 1

### Canônico

```text
status = DISCOVERY_CLOSED_FORMAL_SEARCH_PENDING_PRESS_FREEZE
PRESS = NOT_YET_RECORDED_AS_PASS
GF-10 = false
query_freeze_complete = false
formal_provider_search_executed = false
prisma_search_event_emitted = false
C4 = PRESS_ONLY_CANDIDATE_NOT_APPROVED
```

### Discovery snapshot

- 41.139 raw;
- 33.839 unique;
- 33.067 accepted structural;
- 772 structural quarantine;
- Tier A 662;
- retrieved/partial 594 = 89,73%;
- B-NORM 85;
- C-STRUCT 316;
- route union 351;
- overlap 50;
- unrouted 311.

### D-132

Fonte canônica persistida: 100 registros, 25 em D02–D05.  
Decisões: Y/N/U, dois revisores independentes, adjudicação humana.  
Sem efeito automático em gates.

### S1–S6

Descrito em snapshot DEVELOPMENT de 22/09, mas **não materializado** no runtime/repo atual. Não considerar os 150 registros como pacote existente. Se aprovado, regenerar com protocolo versionado.

## 3. Produto fechado vs Artigo pronto para busca formal

### PRODUCT CLOSED

Requer:

- main final implantada;
- health/version comprovados;
- A1 owner pins persistentes;
- audit de produção PASS;
- browser/CI/recovery reproduzíveis;
- nenhuma falha técnica aberta bloqueante.

### ARTICLE 1 READY FOR FORMAL SEARCH

Requer adicionalmente:

- PRESS humano = PASS;
- C4 decidido;
- provider-native syntax validada;
- known-item/sentinel review satisfatória;
- GF-10 autorizado;
- queries congeladas/versionadas.

Até isso ocorrer:

```text
PRODUCT may be CLOSED
ARTICLE1 FORMAL SEARCH remains HUMAN-GATED
```

## 4. Próxima ação

1. concluir promoção técnica final;
2. provar `/api/article1/scientific-state = 200`;
3. confirmar/materializar round D-132 sem emitir reviewers ainda;
4. selecionar revisores humanos;
5. decidir protocolo de precisão S1–S6/D-132b;
6. executar revisão humana;
7. levar decisões metodológicas ao PRESS/Dr. Caio.
