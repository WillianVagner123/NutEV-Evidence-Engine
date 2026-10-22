# NUT-EV — buscas exploratórias com retenção curta

Objetivo: a pessoa pesquisa, encontra referências e guarda explicitamente o que interessa; não usar o volume persistente como histórico infinito de buscas exploratórias.

## Controles disponibilizados
- O Explorador Aberto (/aberto/) já busca diretamente do navegador sem gerar um corpus persistente no servidor.
- No produto autenticado, resultados de buscas rápidas ainda são persistidos pelo motor e precisam ser tratados como snapshots temporários.
- `python tools/prune_interactive_searches.py` faz **apenas inventário**.
- `python tools/prune_interactive_searches.py --days 2 --apply` apaga exclusivamente diretórios `15_web_searches/web_*/result.json` cuja busca declara `interactive_bounded`, expirados há mais de 2 dias. Não remove buscas de revisão, registros globais, decisões ou arquivos do artigo.
- A limpeza não altera `registry/`, `scientific/`, `agent_context/`, caches de texto completo, volumes Docker ou snapshots. Assim, **não é uma limpeza total**.
- Colocar em agendamento depois da inspeção do primeiro dry-run, com execução pelo usuário/processo dono do volume. Não executar no deploy ou no startup sem avaliação.

## Próximo trabalho obrigatório
Eliminar gravação redundante de `07_logs/web_search/latest.json` para buscas exploratórias, reduzir retenção de runs no catálogo sem perder IDs necessários às Placements e inserir expiração automática em buscas comuns e cache OCR com controle de referências. Auditar volume real antes de remover qualquer arquivo antigo. Nunca aplicar `docker volume prune` ao volume científico.
