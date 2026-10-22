# NUT-EV — Retenção de buscas exploratórias

## Resultado do ajuste
O fluxo de **Busca rápida** (`interactive_bounded`) agora é tratado como efêmero:
- uma única cópia `15_web_searches/web_*/result.json` fica disponível por **48 horas** (configurável);
- deixa de produzir a cópia completa adicional `07_logs/web_search/latest.json`;
- não dispara downloads automáticos de PDF nem OCR; o usuário ainda recebe título, resumo, classificação, identificadores e links dos provedores;
- um worker inicia com o servidor hospedado e, a cada seis horas, exclui apenas snapshots de buscas rápidas expiradas, não modificadas recentemente;
- cópias históricas de `latest.json` geradas por buscas rápidas antigas também expiram.

**O que não desaparece:** metadados bibliográficos globais e seus IDs continuam no Registry porque a biblioteca do workspace ainda precisa de identidade canônica para salvar um artigo escolhido. Isso é pequeno comparado a PDFs, mas não equivale a ausência absoluta de registro no servidor. Para busca totalmente sem gravação no servidor, o Explorador Aberto em `/aberto/` faz a consulta diretamente do navegador.

## Preservação científica
A rotina **nunca toca**:
- `registry/`, `scientific/`, `agent_context/`, estudos A1/A2, placements, decisões, histórico formal, manifests, dados de extração;
- `16_search_full_text_cache/` (PDFs e textos históricos), ainda sujeito a inventário e decisão separada;
- Docker volumes, imagens, backups e snapshots de recuperação.

Consultas `exact_review_*`, `structured_review_*` e `global_exhaustive` seguem persistentes e auditáveis. O status científico/PRISMA não é alterado. No login piloto, as buscas continuam vinculadas a workspace/projeto.

## Configuração da hospedagem
```env
NUTEV_AUTO_CLEAN_QUICK_SEARCH=1
NUTEV_TEMP_SEARCH_RETENTION_DAYS=2
NUTEV_TEMP_SEARCH_CLEANUP_HOURS=6
```

A limpeza automática ocorre apenas no processo `secure_server.py` enquanto o serviço estiver executando. Pode ser desligada com `NUTEV_AUTO_CLEAN_QUICK_SEARCH=0`. A primeira passagem ocorre no startup, e as próximas ocorrem a cada seis horas.

O comando manual pode gerar só inventário ou executar limpeza:
```bash
python tools/prune_interactive_searches.py --root /app/project_output_reference
python tools/prune_interactive_searches.py --root /app/project_output_reference --days 2 --apply
```

A limpeza exige correspondência entre ID da pasta, modo declarado e timestamps da busca/arquivo, e recusa symlinks e formatos desconhecidos. Resultado JSON informa contagem e bytes removidos. No cenário de `--apply`, a deleção dos snapshots temporários é irreversível, mas não afeta os registros científicos descritos acima.

## Auditoria do espaço real
A implementação em GitHub **não demonstra quanto espaço há no servidor**, nem que a PR já foi publicada. Para quantificar, execute no servidor:
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
docker exec <CONTÊINER_NUTEV> python tools/nutev_storage_inventory.py --root /app/project_output_reference
```

Verifique os maiores grupos antes de qualquer redução dos caches históricos de PDF/OCR. Não execute `docker volume prune` nem `docker system prune --volumes` neste ambiente. Backups e decisões científicas não são cache.
