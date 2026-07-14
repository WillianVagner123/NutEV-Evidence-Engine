#!/usr/bin/env bash
#
# close_stale_prs.sh — batch-close the open PR backlog so a cited repository
# does not look abandoned under a wall of open PRs.
#
# It closes, in one pass:
#   1. all DRAFT pull requests authored by the repo owner (agent-generated
#      querypack/term-expansion experiments); and
#   2. all Dependabot pull requests.
# Branches are KEPT by default (reversible — reopen or cherry-pick later).
#
# SAFETY:
#   - Only touches (a) your own DRAFT PRs and (b) Dependabot PRs. Never your own
#     non-draft PRs.
#   - DRY-RUN by default: prints what it WOULD close and changes nothing.
#     Set APPLY=1 to actually close.
#   - Branches are preserved unless you set DELETE_BRANCHES=1.
#   - Requires the GitHub CLI `gh` authenticated with repo scope (`gh auth login`).
#
# USAGE:
#   Dry run (safe, default):     ./scripts/close_stale_prs.sh
#   Actually close (keep branches):  APPLY=1 ./scripts/close_stale_prs.sh
#   Close AND delete branches:   APPLY=1 DELETE_BRANCHES=1 ./scripts/close_stale_prs.sh
#   Different owner/repo:        REPO=owner/name OWNER=owner APPLY=1 ./scripts/close_stale_prs.sh
#
set -euo pipefail

REPO="${REPO:-WillianVagner123/NutEV-Evidence-Engine}"
OWNER="${OWNER:-WillianVagner123}"
APPLY="${APPLY:-0}"
DELETE_BRANCHES="${DELETE_BRANCHES:-0}"
COMMENT="Fechado em lote na limpeza do repositório (preparação para citação). \
Rascunho de expansão de querypack não finalizado; os termos efetivamente usados \
já estão na branch main. A branch foi mantida — este PR pode ser reaberto se \
necessário."

command -v gh >/dev/null 2>&1 || { echo "ERRO: gh CLI não encontrado. Instale em https://cli.github.com/ e rode 'gh auth login'."; exit 1; }

echo "Repositório: $REPO"
echo "Coletando PRs a fechar (seus rascunhos + Dependabot)..."

# (1) Your own DRAFT PRs.
mapfile -t DRAFTS < <(gh pr list --repo "$REPO" --state open --author "$OWNER" --draft \
  --limit 1000 --json number --jq '.[].number')
# (2) Dependabot PRs.
mapfile -t DEPS < <(gh pr list --repo "$REPO" --state open --author "app/dependabot" \
  --limit 1000 --json number --jq '.[].number')

# Merge + dedup.
PRS=$(printf '%s\n' "${DRAFTS[@]}" "${DEPS[@]}" | grep -E '^[0-9]+$' | sort -un)
count=$(printf '%s\n' "$PRS" | grep -c . || true)
echo "Encontrados: ${#DRAFTS[@]} rascunho(s) seu(s) + ${#DEPS[@]} do Dependabot = $count PR(s) (após dedup)."

if [[ "$count" -eq 0 ]]; then echo "Nada a fazer."; exit 0; fi

if [[ "$APPLY" != "1" ]]; then
  echo
  echo "--- DRY RUN (nada será fechado). Fecharia os PRs: ---"
  printf '%s\n' "$PRS" | sed 's/^/  #/'
  echo
  echo "Para fechar de verdade (mantendo as branches):  APPLY=1 ./scripts/close_stale_prs.sh"
  exit 0
fi

DEL_FLAG=""
[[ "$DELETE_BRANCHES" == "1" ]] && DEL_FLAG="--delete-branch"

n=0
for num in $PRS; do
  n=$((n+1))
  echo "[$n/$count] Fechando PR #$num ..."
  gh pr close "$num" --repo "$REPO" --comment "$COMMENT" $DEL_FLAG || \
    echo "  (aviso: não foi possível fechar #$num; continuando)"
done

echo "Concluído: $count PR(s) processado(s). Branches mantidas: $([[ -z "$DEL_FLAG" ]] && echo sim || echo NÃO)."
