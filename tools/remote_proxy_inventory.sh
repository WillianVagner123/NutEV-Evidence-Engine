#!/usr/bin/env bash
# Read-only host/proxy inventory. Never stops, reloads or removes services.
set -euo pipefail
PUBLIC_URL="${PUBLIC_URL:-https://nutev.mindsperformance.com.br}"

has_listener() {
  local port="$1"
  ss -H -ltn "sport = :$port" 2>/dev/null | grep -q .
}

PORT80=no
PORT443=no
if has_listener 80; then PORT80=yes; fi
if has_listener 443; then PORT443=yes; fi

MODE=managed
if [[ "$PORT80" = yes || "$PORT443" = yes ]]; then MODE=external; fi

printf 'NUTEV_PROXY_MODE=%s\n' "$MODE"
printf 'PORT80_LISTENER=%s\n' "$PORT80"
printf 'PORT443_LISTENER=%s\n' "$PORT443"
printf 'HOSTNAME=%s\n' "$(hostname)"
printf 'KERNEL=%s\n' "$(uname -sr)"
printf 'UPTIME_SECONDS=%s\n' "$(cut -d. -f1 /proc/uptime)"
printf 'ROOT_FREE_KB=%s\n' "$(df -Pk / | awk 'NR==2 {print $4}')"
printf 'MEM_AVAILABLE_KB=%s\n' "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"

printf '%s\n' '--- PORT OWNERS (sanitized process identity only) ---'
ss -H -ltnp '( sport = :80 or sport = :443 )' 2>/dev/null || true
printf '%s\n' '--- DOCKER PUBLISHED 80/443 ---'
docker ps --format '{{.Names}}|{{.Image}}|{{.Label "com.docker.compose.project"}}|{{.Label "com.docker.compose.service"}}|{{.Ports}}' \
  | grep -E '(^|[, ])([^ ]*:)?(80|443)->|:(80|443)->|0\.0\.0\.0:(80|443)|\[::\]:(80|443)' || true
printf '%s\n' '--- SYSTEM SERVICES ---'
for service in caddy nginx apache2 traefik; do
  state=$(systemctl is-active "$service" 2>/dev/null || true)
  printf '%s=%s\n' "$(printf '%s' "$service" | tr '[:lower:]' '[:upper:]')" "${state:-not-found}"
done

status_code() {
  curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "$1" 2>/dev/null || printf '000'
}
printf 'PUBLIC_HEALTH_STATUS=%s\n' "$(status_code "$PUBLIC_URL/api/health")"
printf 'PUBLIC_VERSION_STATUS=%s\n' "$(status_code "$PUBLIC_URL/api/version")"
printf 'PUBLIC_ROOT_STATUS=%s\n' "$(status_code "$PUBLIC_URL/")"
