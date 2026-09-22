# NutEV — Operar o Artigo 1 do doutorado

Status: **guia humano do produto hospedado**.

Este guia descreve como o responsável pelo Artigo 1 e o professor orientador usam o NutEV no
dia a dia. Ele é o passo a passo de produto; os contratos que ele resume estão em
[`MULTITENANT_WORKSPACE_PROJECT_ACCESS.md`](MULTITENANT_WORKSPACE_PROJECT_ACCESS.md),
[`ACCESS_REQUEST_ONBOARDING.md`](ACCESS_REQUEST_ONBOARDING.md) e
[`ACADEMIC_SUPERVISOR_ONBOARDING.md`](ACADEMIC_SUPERVISOR_ONBOARDING.md), que continua sendo
o runbook de operador para a concessão por linha de comando.

Nada neste guia abre portão metodológico. Ler o estado do Artigo 1 não aprova PRESS, não
autoriza GF-10, não congela consultas, não executa busca formal e não cria PRISMA.

## O caminho completo

```text
Responsável
  login -> workspace do doutorado -> Artigo 1 -> aplicação de pesquisa
        -> acompanha estado científico, biblioteca, revisão, auditoria
        -> gerencia quem tem acesso

Orientador
  solicita acesso -> administrador aprova -> define a própria senha -> login
        -> responsável concede ACADEMIC_SUPERVISOR no workspace
        -> seleciona o workspace e o Artigo 1
        -> visão acadêmica somente leitura
```

Cada seta é um passo distinto. Em especial, **aprovar a solicitação de acesso não dá acesso a
workspace nenhum**: a conta nasce sem workspace, sem projeto e sem dado científico, e isso é o
comportamento fail-closed esperado.

## Parte 0 — Abrir o workspace pela primeira vez (operador)

Este passo acontece uma única vez, antes de tudo, e só depois de o responsável já ter conta
ativa pelo fluxo governado de convite.

```bash
python tools/provision_doctorate_article1.py \
  --owner-email "responsavel@instituicao.br" \
  --workspace-name "Doutorado — <nome>" \
  --workspace-slug "<slug-do-workspace>" \
  --project-name "Artigo 1" \
  --project-slug "artigo-1" \
  --project-type review \
  --article1-assembly
```

O comando cria o workspace, o projeto e a `ResearchApplication` de **Revisão de escopo**
(`SCOPING_REVIEW`), e devolve um recibo JSON com os identificadores. Com
`--article1-assembly`, ele também garante as chaves técnicas canônicas
`assembly_id=WILLIAN_DOCTORATE_A1` e `d132_config_version=<versão canônica do D-132>`.
Se a aplicação já existir e uma dessas chaves estiver ausente, o provisionador repara somente
essas chaves e preserva o restante da configuração privada. Se já existir valor conflitante,
ele falha fechado em vez de sobrescrever. Depois do reparo, uma nova execução é idempotente e
devolve `already_provisioned`.

O comando nunca cria usuário, nunca define senha, nunca concede papel global e nunca concede
acesso a terceiros. O banco padrão vem de `NUTEV_AUTH_DB`.

### Códigos de saída

```text
0   provisioned | already_provisioned
2   e-mail malformado
3   database_missing
4   owner_not_found     (o responsável ainda não tem conta ativa)
5   owner_not_active
6   workspace_refused
7   workspace_owned_by_another_identity
8   project_refused
9   application_refused
10  application_binding_conflict
```

### O passo humano que resta

Com os identificadores do recibo, o operador define os pins do Artigo 1 no ambiente:

```text
NUTEV_A1_WORKSPACE_ID=wsp_...
NUTEV_A1_PROJECT_ID=prj_...
```

Esses pins são o que expõe as superfícies do Artigo 1, e devem ser preenchidos **somente a
partir de evidência revisada de propriedade em runtime**. O comando os informa, mas não os
define: configurar a aplicação não cria propriedade científica.

## Parte 1 — O responsável pelo Artigo 1

### Entrar e escolher o contexto

1. Abra `/login.html` e entre com e-mail e senha.
2. No seletor de contexto no topo, escolha o **workspace do doutorado**.
3. Escolha o projeto **Artigo 1**.

A seleção é guardada na sessão do servidor, não no navegador. Selecionar não é autorização: a
cada requisição o NutEV revalida a associação ao workspace, o acesso ao projeto e a permissão.

Se a conta ainda não tiver workspace, a tela diz isso explicitamente em vez de abrir vazia.

### A tela do projeto

`/project.html` mostra, de cima para baixo:

- o projeto atual, o workspace, a aplicação de pesquisa e o seu papel;
- o **estado científico do Artigo 1**, quando o projeto é o Artigo 1 pinado no servidor;
- a **aplicação de pesquisa** (Revisão de escopo) e seus componentes;
- os módulos do fluxo: Biblioteca, buscas, Revisão humana, Exportações;
- **Acesso ao workspace**, com o atalho para gerenciar membros.

Cada área aparece conforme o papel. O NutEV prefere não desenhar uma ação proibida a desenhá-la
e recusá-la no clique — mas quem decide continua sendo o servidor, em toda requisição.

### Gerenciar quem tem acesso

Em `/members.html` (atalho **Gerenciar membros** na tela do projeto) o proprietário ou um
administrador do workspace pode:

1. ver quem tem acesso, com papel e situação;
2. conceder acesso a alguém pelo e-mail;
3. escolher o papel, incluindo **Professor orientador** (`ACADEMIC_SUPERVISOR`);
4. alterar o papel de quem já tem acesso, com confirmação explícita;
5. suspender, reativar ou remover o acesso.

Três limites valem sempre:

- a pessoa **precisa já ter conta ativa**. Esta tela concede acesso, nunca cria conta nem
  define senha de outra pessoa; quem não passou pelo convite aparece como não encontrada;
- **a propriedade do workspace não muda por aqui**. `WORKSPACE_OWNER` não pode ser atribuído,
  e o papel e a situação do proprietário atual não são editáveis nesta tela;
- alterar o papel de alguém nunca acontece em silêncio: a mudança exige confirmação.

Suspender vale já na requisição seguinte da pessoa. Não é preciso esperar logout, porque o
Principal é reconstruído a partir do estado atual de membership a cada requisição.

Papéis que **não** gerenciam membros: `ACADEMIC_SUPERVISOR`, `VIEWER`, `REVIEWER`,
`GUEST_REVIEWER`.

## Parte 2 — O professor orientador

### Receber acesso

1. **Solicitar**: em `/login.html` → `/access-request.html`, informar nome, e-mail,
   instituição e uso científico pretendido. Não existe auto-registro.
2. **Aprovação**: um `PLATFORM_ADMIN` aprova em `/access-admin.html`. A aprovação gera um
   **convite de uso único**, válido por 72 horas. O link aparece só no momento em que é
   emitido; o operador copia e envia por um canal apropriado.
3. **Senha**: o orientador abre `/set-password.html?token=...` e define a própria senha. O
   operador nunca define senha de outra pessoa.
4. **Membership**: o responsável pelo Artigo 1 concede `ACADEMIC_SUPERVISOR` no workspace, pela
   tela de membros ou pela CLI de operador do runbook.
5. **Entrar**: o orientador faz login, escolhe o workspace e abre o Artigo 1.

Entre os passos 3 e 4 o orientador consegue entrar, mas não vê workspace algum. Isso é o
esperado, não uma falha.

### O que o orientador vê

- o projeto **Artigo 1**, a aplicação de pesquisa e o rótulo **Professor orientador**;
- o **estado científico**: Discovery, PRESS, GF-10, congelamento de consulta, busca formal e
  PRISMA formal;
- a **Biblioteca** do projeto;
- o **histórico de buscas**;
- a **Revisão humana em leitura**: rounds, pendências e estado da adjudicação;
- a **trilha de auditoria** e as exportações do projeto.

### O que o orientador não pode fazer

O papel não concede — nem por tela, nem por chamada direta à API:

```text
executar busca            triagem              extração
adjudicação               gestão de revisão    gestão de membros
criação de projeto        exclusão de projeto  qualquer papel global
escrita na Biblioteca     configurar a aplicação
```

Essas recusas são do servidor. Botão escondido não é fronteira: a regressão de navegador com
dois atores chama esses endpoints com a sessão real do orientador e exige a recusa.

O orientador também não alcança outro workspace ou outro projeto, mesmo conhecendo o
identificador exato.

## Parte 3 — O estado científico do Artigo 1

A tela do projeto lê o estado da fonte canônica do repositório,
`config/nutev/article1_search_master_v1.json`. A interface não decide nenhum veredito: mostra o
que o master registra, e qualquer valor que ela não reconheça é exibido como portão fechado.

| Portão | Estado atual |
| --- | --- |
| Discovery | Concluído |
| PRESS | Pendente |
| GF-10 | Não autorizado |
| Congelamento de consulta | Pendente |
| Busca formal | Não executada |
| PRISMA formal | Não criado |

Os números do corpus de descoberta aparecem na área de detalhes, rotulados pelo que são:
contagens de descoberta e recuperação. **Não** são contagens PRISMA, triagem, inclusão nem
exclusão.

Para que o painel apareça, o projeto precisa ser o Artigo 1 pinado no servidor
(`NUTEV_A1_WORKSPACE_ID` e `NUTEV_A1_PROJECT_ID`). Esse pin é o mecanismo de vínculo que o
produto já usa para o material histórico do Artigo 1, e é um vínculo **de acesso**: ele não
adota decisões científicas, de triagem ou de PRISMA para o projeto. Sem os pins, o painel
simplesmente não aparece — fail-closed, sem inventar propriedade científica.

## Parte 4 — O que este acesso não é

```text
ter acesso ao Artigo 1   !=   aprovar PRESS
                         !=   autorizar GF-10
                         !=   congelar as consultas
                         !=   aprovar a busca formal
                         !=   criar PRISMA
                         !=   elegibilidade, qualidade metodológica,
                              risco de viés, certeza ou recomendação
```

Conceder supervisão é concessão de acesso, e não aprovação do orientador. Um orientador com
acesso de leitura que observa um artefato não torna esse artefato revisado, aprovado ou
incluído. Todo julgamento humano continua exigindo registro explícito na camada de Revisão
Humana.

Ser orientador também não concede poder de adjudicação. Se o orientador vier a atuar
formalmente como revisor ou adjudicador do Artigo 1, isso é uma atribuição separada e
explícita, nunca uma consequência da supervisão.

## Escopo do workspace

`ACADEMIC_SUPERVISOR` é um papel de **workspace**: quem o recebe lê todos os projetos daquele
workspace. Portanto o workspace do doutorado deve conter apenas projetos acadêmicos que o
orientador possa legitimamente acompanhar. Projetos clínicos, pessoais ou não relacionados
pertencem a outro workspace.

Um Artigo 2 pode entrar no mesmo workspace no futuro, se isso fizer sentido academicamente.

## Resolução de problemas

| Sintoma | Causa provável |
| --- | --- |
| "Nenhuma conta ativa com esse e-mail" ao conceder acesso | A pessoa ainda não concluiu o convite e a senha (passo 3). |
| O orientador entra e não vê workspace | O membership ainda não foi concedido (passo 4). |
| "Você não gerencia os membros deste workspace" | O papel atual não tem `MEMBERS_MANAGE`. |
| O painel de estado científico não aparece | O projeto não é o Artigo 1 pinado no servidor. |
| "A propriedade do workspace não muda por esta tela" | Houve tentativa de atribuir ou remover `WORKSPACE_OWNER`. |
| O orientador perdeu o acesso de repente | O membership foi suspenso ou removido; passa a valer na requisição seguinte. |
