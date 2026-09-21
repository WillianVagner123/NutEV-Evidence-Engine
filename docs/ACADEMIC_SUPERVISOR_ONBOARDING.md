# NutEV — Onboarding do Professor Orientador

Status: **runbook operacional do produto hospedado**.

Este runbook descreve como dar acesso a um **professor orientador** usando o papel somente leitura `ACADEMIC_SUPERVISOR`, definido em [`MULTITENANT_WORKSPACE_PROJECT_ACCESS.md`](MULTITENANT_WORKSPACE_PROJECT_ACCESS.md).

Ele não cria estado científico, não infere elegibilidade e não representa aprovação do orientador.

## O que o papel concede

```text
APPLICATION_READ        leitura da aplicação de pesquisa do projeto
SEARCH_HISTORY_READ     leitura do histórico de buscas
EVIDENCE_LIBRARY_READ   leitura da Evidence Library
FULL_TEXT_ACCESS_READ   leitura dos descritores de texto completo ativos
PROJECT_BANK_READ       leitura do banco do projeto
HUMAN_REVIEW_READ       leitura dos registros de Revisão Humana
PROJECT_AUDIT_READ      leitura da trilha de auditoria do projeto
EXPORT                  somente com policy grant explícito
```

O papel **não** concede escrita, execução de busca, triagem, extração, adjudicação, gestão de revisão humana, gestão de membros, criação ou exclusão de projeto, nem qualquer papel global.

## Pré-requisitos

- runtime hospedado em `NUTEV_AUTH_MODE=pilot`;
- um `PLATFORM_ADMIN` ativo;
- o workspace de destino já existente e ativo;
- o e-mail institucional do orientador.

## Passo 1 — Solicitação de acesso

O orientador acessa `/login.html` → `/access-request.html` e envia nome completo, e-mail, instituição e uso científico pretendido.

Não existe auto-registro. A solicitação sozinha não cria conta, papel, membership ou acesso a dado científico.

## Passo 2 — Aprovação administrativa

O `PLATFORM_ADMIN` abre `/access-admin.html`, localiza a solicitação e aprova.

A aprovação emite um **convite de uso único**, válido por 72 horas por padrão. O link aparece apenas no momento da emissão ou rotação; copie-o e envie por um canal apropriado. Reaprovar rotaciona o convite e invalida o link anterior.

## Passo 3 — O orientador define a própria senha

O orientador abre o link (`/set-password.html?token=...`) e define a senha. A conta é criada nesse momento, com Argon2 e a política de senha canônica.

O operador nunca define a senha de outra pessoa. Não use `tools/provision_nutev_user.py` para o orientador: ele exige que o operador digite a senha e existe para identidades operacionais, não para onboarding governado.

Após este passo o orientador **já consegue fazer login**, mas ainda não enxerga nenhum workspace ou projeto. Isso é o comportamento fail-closed esperado.

## Passo 4 — Conceder o membership de supervisão

No host, dentro do container da aplicação:

```bash
docker compose --env-file deploy/hetzner/.env -f deploy/hetzner/compose.yaml exec -T nutev \
  python tools/grant_workspace_membership.py \
    --email "orientador@instituicao.br" \
    --workspace-slug "<slug-do-workspace>" \
    --role ACADEMIC_SUPERVISOR
```

Use `--workspace-id wsp_...` no lugar de `--workspace-slug` quando preferir o identificador opaco. O banco padrão vem de `NUTEV_AUTH_DB`.

A ferramenta emite JSON em stdout e é idempotente:

```json
{"status": "membership_granted", "changed": true, "role": "ACADEMIC_SUPERVISOR", "user_created": false, "password_created": false, "global_role_granted": false, "scientific_state_modified": false, "scientific_approval_created": false}
```

Rodar de novo devolve `already_granted` com `changed: false`.

### Códigos de saída

```text
0   membership_granted | already_granted
2   entrada inválida (e-mail malformado, papel não atribuível)
3   database_missing
4   user_not_found            (o orientador ainda não aceitou o convite)
5   user_not_active
6   workspace_not_found
7   owner_role_refused        (use o fluxo explícito de transferência de propriedade)
8   role_change_requires_explicit_flag
9   membership_refused | verification_failed
10  workspace_not_active
```

`user_not_found` quase sempre significa que o Passo 3 ainda não foi concluído.

Trocar o papel de um membership existente exige `--allow-role-change`. Sem a flag, a ferramenta recusa e não altera nada, para que uma mudança de privilégio nunca aconteça em silêncio.

`invited_by` fica nulo: uma concessão por CLI de operador não tem Principal autenticado convidando e não deve personificar um.

## Passo 5 — Confirmar

O orientador faz login novamente. O seletor de contexto passa a mostrar o workspace com o rótulo **Professor orientador**, e os projetos autorizados ficam visíveis.

## Revogar

```bash
python tools/grant_workspace_membership.py \
  --email "orientador@instituicao.br" \
  --workspace-slug "<slug-do-workspace>" \
  --role ACADEMIC_SUPERVISOR \
  --status suspended
```

Sessões são reconstruídas a cada requisição a partir do estado atual de membership, então a suspensão passa a valer nas requisições seguintes sem precisar de logout manual.

## Homologação provisória

Para validar ou demonstrar o acesso antes de tocar em produção, use o ambiente descartável de homologação.

```bash
export NUTEV_ENVIRONMENT=homologacao
python tools/seed_homologation_access.py --database /caminho/descartavel/homologacao.sqlite3
```

O seeder cria responsável, workspace, projeto e a conta do orientador já com `ACADEMIC_SUPERVISOR`, e imprime as senhas geradas **uma única vez** em stdout. São credenciais descartáveis de um banco descartável; nunca as reutilize em conta de produção.

Suba o servidor apontando para o banco de homologação (o comando exato vem no campo `serve_with` do recibo):

```bash
NUTEV_AUTH_MODE=pilot NUTEV_ENVIRONMENT=homologacao NUTEV_AUTH_DB=/caminho/descartavel/homologacao.sqlite3 python apps/nutev-web/secure_server.py --host 127.0.0.1 --port 8765
```

Abra `http://127.0.0.1:8765/login.html` e entre com o e-mail e a senha do orientador do recibo.

### Guardas contra produção

O seeder recusa, sem criar nada:

```text
2   NUTEV_ENVIRONMENT ausente ou de produção
    (a variável ausente conta como produção, porque o runtime assume produção por padrão)
3   caminho canônico de produção, ou o mesmo caminho de NUTEV_AUTH_DB
4   banco que é symlink
5   banco que já contém identidades (ele nunca altera identidade existente)
6   identidade recusada pela política de senha/e-mail
```

Para recomeçar, apague o arquivo de homologação e rode de novo. O seeder nunca sobrescreve identidades.

### O que a homologação não é

O ambiente é estado de tenancy e navegação. Não cria registro científico, busca, Evidence Library, revisão humana, PRISMA, PRESS ou GF-10, e não é evidência sobre o comportamento de produção — apenas sobre o caminho de acesso exercitado ali.

## Fronteira científica

Conceder supervisão é concessão de acesso. Não é aprovação do orientador e não cria elegibilidade, qualidade metodológica, risco de viés, certeza, recomendação, PRISMA, PRESS, GF-10 nem congelamento de consulta.

Um orientador com acesso de leitura que observa um artefato não torna esse artefato revisado, aprovado ou incluído. Qualquer julgamento humano continua exigindo registro explícito na camada de Revisão Humana.
