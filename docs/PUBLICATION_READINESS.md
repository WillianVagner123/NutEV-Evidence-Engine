# Publication readiness — NutEV 1.1.0

Status operacional: **PRODUCTION_ACCEPTED**.  
Status de publicação pública: **PENDING**.

A versão 1.1.0 está homologada e ativa em produção no SHA:

```text
e40dfd8c48cde824fa6053f9b077157f21bae698
```

O fechamento operacional confirmou os gates de produção, recovery e fail-closed descritos em `docs/releases/v1.1.0-production-closeout.md` e `docs/FINAL_SYSTEM_ACCEPTANCE.md`.

Isso não transforma automaticamente o software em uma versão publicamente arquivada. No momento deste documento, ainda faltam operações externas de publicação:

1. criar a tag imutável `v1.1.0` apontando exatamente para `e40dfd8c48cde824fa6053f9b077157f21bae698`;
2. criar o GitHub Release `v1.1.0` associado a essa tag;
3. anexar ou preservar artefatos auditados, release notes e hashes de distribuição;
4. publicar um novo registro no Zenodo ou repositório equivalente;
5. registrar o DOI real da versão 1.1.0 somente depois de emitido e verificado;
6. atualizar metadados finais que dependam desse DOI/data de publicação.

## Release anterior

A release pública estável anterior permanece:

- GitHub Release: `v1.0.0`;
- Zenodo: `https://zenodo.org/records/21998607`;
- DOI: `10.5281/zenodo.21998607`.

Esse DOI é específico do arquivo histórico da `v1.0.0` e **não deve ser reutilizado** para `v1.1.0`.

## Distribution scope

A distribuição `nutev-nutmev` wheel/sdist contém módulos Python reutilizáveis e CLI. Contas, bancos de dados, buscas privadas, configurações científicas privadas A1/A2 e backups não fazem parte da distribuição pública.

O website usa o checkout auditado do repositório e Docker; ele não é empacotado dentro do wheel.

## Gates já fechados

Para a produção 1.1.0, o fechamento registrou:

- 7/7 workflows aprovados no mesmo SHA;
- recovery readiness no Hetzner;
- capacidade suficiente para snapshots;
- três snapshots completos preservados;
- release ativo protegido;
- deploy exact-SHA `#1659` aprovado;
- NutEV 1.1.0 em produção;
- Caddy externo / 80–443 aprovado;
- `/search.html` e `/articles.html` respondendo `200`;
- superfícies privadas sem autenticação respondendo `401` / fail-closed;
- backup/restore real aprovado;
- 19.466 arquivos verificados;
- 33 bancos SQLite verificados;
- `production_overwritten=false`;
- auditor pós-deploy `#99` aprovado;
- auditor confirmando `read_only=true`, `scientific_state_modified=false`, `legacy_binding_performed=false`, `search_executed=false`;
- zero aplicações A1/A2 materializadas em produção, preservando o comportamento fail-closed.

## Reproducible package checks

Os controles de distribuição continuam definidos por:

- `PYTHONPATH=src python -m pytest -q nutev_tests`;
- `python -m build`;
- `python -m twine check dist/*`;
- `python tools/audit_public_package.py --dist dist --version 1.1.0 --output package_audit/distributions.json`;
- instalação limpa do wheel fora do checkout;
- `bash tools/run_container_release_gate.sh` para auditoria descartável de imagem, privacidade e recovery.

## Scientific boundary

A publicação do software não fecha os braços científicos.

- A1 continua dependente de aprovação acadêmica humana, verificador humano nominal e gates metodológicos formais.
- A2 continua dependente de proveniência real e Legacy Binding evidence revisada.
- O estado científico do Engine continua `B — DEMOTE` até que o protocolo de validação produza evidência observada suficiente para promoção.

Nenhum desses estados pode ser promovido por CI, deploy, release ou DOI.

## Publication decision rule

Use exatamente um dos seguintes estados:

```text
PRODUCTION_ACCEPTED / PUBLICATION_PENDING
```

enquanto tag/release/arquivo público ainda não existirem; e somente depois de verificação externa completa:

```text
RELEASED / PUBLISHED
```

Nunca registre DOI, data de publicação ou URL de release por antecipação.
