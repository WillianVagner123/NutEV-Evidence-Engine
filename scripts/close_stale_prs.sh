#!/usr/bin/env bash
#
# close_stale_prs.sh — batch-close stale Dependabot pull requests.
#
# WHY: a repository cited in an academic article should not show hundreds of
# open bot PRs (it reads as abandoned). After tightening .github/dependabot.yml
# to grouped, monthly, capped updates, this script closes the backlog of old
# Dependabot PRs in one pass. Dependabot will re-open a single grouped PR on its
# next monthly run if updates are still pending.
#
# SAFETY:
#   - Only touches PRs authored by "app/dependabot" (never your own PRs).
#   - DRY-RUN by default: it prints what it WOULD close and changes nothing.
#     Set APPLY=1 to actually close them.
#   - Requires the GitHub CLI `gh` authenticated with repo scope (`gh auth login`).
#
# USAGE:
#   Dry run (safe, default):   ./scripts/close_stale_prs.sh
#   Actually close them:       APPLY=1 ./scripts/close_stale_prs.sh
#   Different repo:            REPO=owner/name APPLY=1 ./scripts/close_stale_prs.sh
#
set -euo pipefail

REPO="${REPO:-WillianVagner123/NutEV-Evidence-Engine}"
APPLY="${APPLY:-0}"
COMMENT="Fechado em lote: a configuração do Dependabot foi ajustada para \
atualizações agrupadas e mensais (ver .github/dependabot.yml). Se ainda houver \
atualização pendente, o Dependabot reabrirá um único PR agrupado."

command -v gh >/dev/null 2>&1 || { echo "ERRO: gh CLI não encontrado. Instale em https://cli.github.com/"; exit 1; }

echo "Repositório: $REPO"
echo "Buscando PRs abertos do Dependabot..."

# List open PRs authored by Dependabot (number + title), newline-delimited.
mapfile -t PRS < <(gh pr list --repo "$REPO" --state open --author "app/dependabot" \
  --limit 1000 --json number,title --jq '.[] | "\(.number)\t\(.title)"')

count="${#PRS[@]}"
echo "Encontrados $count PR(s) do Dependabot."

if [[ "$count" -eq 0 ]]; then
  echo "Nada a fazer."
  exit 0
fi

if [[ "$APPLY" != "1" ]]; then
  echo
  echo "--- DRY RUN (nada será fechado). Estes seriam fechados: ---"
  for line in "${PRS[@]}"; do
    printf '  #%s\n' "$line"
  done
  echo
  echo "Para fechar de verdade, rode:  APPLY=1 ./scripts/close_stale_prs.sh"
  exit 0
fi

for line in "${PRS[@]}"; do
  num="${line%%$'\t'*}"
  echo "Fechando PR #$num ..."
  gh pr close "$num" --repo "$REPO" --comment "$COMMENT" --delete-branch || \
    echo "  (aviso: não foi possível fechar #$num; continuando)"
done

echo "Concluído: $count PR(s) processado(s)."
