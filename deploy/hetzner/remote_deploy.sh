#!/usr/bin/env bash
# Remote half of the Hetzner production deploy, executed on the host.
#
# This used to be a heredoc streamed into `bash -s` over the SSH channel. That made a
# partially delivered script indistinguishable from a successful deploy: when the channel
# was disturbed around the container restart, bash reached EOF mid-script and exited 0,
# so the post-promotion runtime contract, the build-identity assertion, the public edge
# smoke and the rollback safety net could all be skipped while the job reported success.
#
# The workflow now copies this file to the host, verifies its SHA-256 and executes it from
# disk, so delivery is checked before anything runs. The script also prints an explicit
# completion sentinel as its final act; the workflow fails the deploy when that sentinel
# is absent, so partial execution can never read as success again.
#
# Inputs arrive as environment variables: APP_DIR, TARGET_SHA, PUBLIC_URL, PROXY_MODE and
# EVIDENCE_DIR. It changes no scientific state and approves nothing.

set -euo pipefail
[[ "$PROXY_MODE" = managed || "$PROXY_MODE" = external ]]
cd "$APP_DIR"
test -d .git
test -f deploy/hetzner/.env

# Runtime owner pins live outside the Git checkout so a deployment cannot
# silently lose the reviewed Article 1 ownership binding. Only these two
# opaque IDs may be merged, and malformed/incomplete files fail closed.
ARTICLE1_OWNER_ENV=/etc/nutev/article1-owner.env
if [[ -f "$ARTICLE1_OWNER_ENV" ]]; then
  test "$(stat -c '%u' "$ARTICLE1_OWNER_ENV")" = "0"
  test "$(stat -c '%a' "$ARTICLE1_OWNER_ENV")" = "600"
  python3 - "$ARTICLE1_OWNER_ENV" deploy/hetzner/.env <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import re
import sys
import tempfile

source = Path(sys.argv[1])
target = Path(sys.argv[2])
allowed = {"NUTEV_A1_WORKSPACE_ID", "NUTEV_A1_PROJECT_ID"}
values: dict[str, str] = {}

for raw in source.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    if "=" not in line:
        raise SystemExit("invalid Article 1 owner env line")
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if key not in allowed:
        raise SystemExit("unexpected key in Article 1 owner env")
    if key in values:
        raise SystemExit("duplicate key in Article 1 owner env")
    values[key] = value

if set(values) != allowed:
    raise SystemExit("Article 1 owner env must contain exactly both owner pins")
if not re.fullmatch(r"wsp_[0-9a-f]{32}", values["NUTEV_A1_WORKSPACE_ID"]):
    raise SystemExit("invalid Article 1 workspace pin")
if not re.fullmatch(r"prj_[0-9a-f]{32}", values["NUTEV_A1_PROJECT_ID"]):
    raise SystemExit("invalid Article 1 project pin")

text = target.read_text(encoding="utf-8")
for key, value in values.items():
    pattern = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    replacement = f"{key}={value}"
    text = pattern.sub(replacement, text) if pattern.search(text) else text.rstrip() + "\n" + replacement + "\n"

fd, temp_name = tempfile.mkstemp(prefix=".env.article1.", dir=str(target.parent))
try:
    os.write(fd, text.encode("utf-8"))
    os.close(fd)
    os.chmod(temp_name, 0o600)
    os.replace(temp_name, target)
except Exception:
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.unlink(temp_name)
    except OSError:
        pass
    raise
PY
  echo "Article 1 owner pins synchronized from protected runtime configuration."
fi

# Evidence lands in a run-scoped directory on the host so it survives the restart that
# used to swallow it from the streamed log. The workflow fetches this directory after the
# deploy step and uploads it, making every promotion carry its own proof.
EVIDENCE_DIR="${EVIDENCE_DIR:-/tmp/nutev-deploy-evidence}"
rm -rf "$EVIDENCE_DIR"
mkdir -p "$EVIDENCE_DIR"
keep_evidence() {
  # $1 = source file, $2 = name under the evidence directory.
  [[ -f "$1" ]] && cp "$1" "$EVIDENCE_DIR/$2" || true
}

public_status() {
  curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || printf '000'
}
acceptable_edge_status() {
  [[ "$1" = "200" || "$1" = "401" ]]
}

# If something already owns 80/443, preserve it. Only continue when it
# already routes the NutEV hostname to a reachable endpoint.
if [[ "$PROXY_MODE" = external ]]; then
  echo "Existing listener detected; NutEV will not stop or replace it."
  BEFORE_HEALTH=$(public_status "$PUBLIC_URL/api/health")
  BEFORE_ROOT=$(public_status "$PUBLIC_URL/")
  if ! acceptable_edge_status "$BEFORE_HEALTH" && ! acceptable_edge_status "$BEFORE_ROOT"; then
    echo "::error::External proxy owns 80/443 but the current NutEV public route is not reachable; configure that proxy explicitly before promotion." >&2
    exit 1
  fi
else
  echo "No listener on 80/443; NutEV will manage its own Caddy."
fi

test -z "$(git status --porcelain --untracked-files=no)"
git fetch --prune origin main
test "$(git rev-parse origin/main)" = "$TARGET_SHA"
umask 077
RECOVERY_BASE=/var/lib/nutev-release-recovery
mkdir -p "$RECOVERY_BASE"
RECOVERY_DIR=$(mktemp -d "$RECOVERY_BASE/${TARGET_SHA}.XXXXXX")
cp -a deploy/hetzner "$RECOVERY_DIR/config"
git checkout -f main
git reset --hard "$TARGET_SHA"

IMAGE="nutev:${TARGET_SHA}"
BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
BUILD_BRANCH="main"
VERSION="$(python3 -c 'ns={};exec(open("src/nutev/__version__.py", encoding="utf-8").read(), ns);print(ns["__version__"])')"
COMPOSE=(docker compose --env-file deploy/hetzner/.env -f deploy/hetzner/compose.yaml)
DEPLOY_SERVICES=(nutev)
if [[ "$PROXY_MODE" = managed ]]; then DEPLOY_SERVICES+=(caddy); fi

OLD_CONTAINER="$("${COMPOSE[@]}" ps -q nutev 2>/dev/null)"
test -n "$OLD_CONTAINER"
OLD_IMAGE_ID="$(docker inspect -f '{{.Image}}' "$OLD_CONTAINER")"
docker tag "$OLD_IMAGE_ID" nutev:rollback
OLD_COMMIT="$(curl -fsS http://127.0.0.1:8765/api/version | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit", ""))')"
[[ "$OLD_COMMIT" =~ ^[0-9a-f]{40}$ ]]
COMPOSE_PROJECT="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$OLD_CONTAINER")"
test -n "$COMPOSE_PROJECT"
OUTPUT_VOLUME="$(docker inspect -f '{{range .Mounts}}{{if and (eq .Destination "/app/project_output_reference") (eq .Type "volume")}}{{.Name}}{{end}}{{end}}' "$OLD_CONTAINER")"
test -n "$OUTPUT_VOLUME"
printf '%s\n' "$OLD_COMMIT" > "$RECOVERY_DIR/previous-sha.txt"
printf '%s\n' "$OLD_IMAGE_ID" > "$RECOVERY_DIR/previous-image.txt"
printf '%s\n' "$PROXY_MODE" > "$RECOVERY_DIR/proxy-mode.txt"
OLD_STOPPED=0
PROMOTED=0
ROLLBACK_DONE=0

rollback() {
  if [[ "$ROLLBACK_DONE" = "1" ]]; then return; fi
  ROLLBACK_DONE=1
  echo "Deployment failed; restoring the previous image and configuration, not overwriting scientific data."
  docker tag "$OLD_IMAGE_ID" nutev:rollback
  RESTORE_SERVICES=(nutev)
  if [[ "$PROXY_MODE" = managed ]]; then RESTORE_SERVICES+=(caddy); fi
  NUTEV_IMAGE=nutev:rollback docker compose \
    --project-name "$COMPOSE_PROJECT" \
    --env-file "$RECOVERY_DIR/config/.env" \
    -f "$RECOVERY_DIR/config/compose.yaml" up -d --no-build "${RESTORE_SERVICES[@]}"
  for _ in $(seq 1 30); do
    RESTORED_COMMIT=$(curl -fsS --max-time 3 http://127.0.0.1:8765/api/version | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit", ""))') || RESTORED_COMMIT=''
    if [[ "$RESTORED_COMMIT" = "$OLD_COMMIT" ]] && curl -fsS --max-time 3 http://127.0.0.1:8765/api/health >/dev/null; then
      echo "Previous runtime identity restored; release remains FAILED."
      return 0
    fi
    sleep 2
  done
  echo "::error::Rollback verification failed; manual recovery required. Protected snapshot preserved." >&2
  return 1
}
recover_on_error() {
  trap - ERR
  if [[ "$PROMOTED" = "1" ]]; then rollback;
  elif [[ "$OLD_STOPPED" = "1" ]]; then docker start "$OLD_CONTAINER" >/dev/null; fi
  exit 1
}
set -E
trap recover_on_error ERR

docker build \
  --build-arg NUTEV_BUILD_COMMIT="$TARGET_SHA" \
  --build-arg NUTEV_BUILD_BRANCH="$BUILD_BRANCH" \
  --build-arg NUTEV_BUILD_TIME="$BUILD_TIME" \
  --build-arg NUTEV_VERSION="$VERSION" \
  -f deploy/hetzner/Dockerfile -t "$IMAGE" .

docker rm -f nutev-preflight >/dev/null 2>&1 || true
docker run -d --name nutev-preflight --env-file deploy/hetzner/.env \
  -p 127.0.0.1:18765:8765 "$IMAGE" >/dev/null
cleanup_preflight() { docker rm -f nutev-preflight >/dev/null 2>&1 || true; }
trap cleanup_preflight EXIT
preflight_ok=0
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18765/api/health >/dev/null; then preflight_ok=1; break; fi
  sleep 2
done
if [[ "$preflight_ok" != "1" ]]; then docker logs nutev-preflight || true; exit 1; fi
docker exec nutev-preflight python tools/check_predeploy_runtime_contract.py --json > /tmp/nutev-runtime-preflight.json
keep_evidence /tmp/nutev-runtime-preflight.json runtime-preflight.json
cat /tmp/nutev-runtime-preflight.json
if ! docker exec nutev-preflight python tools/check_runtime_http_surface.py \
  --base-url http://127.0.0.1:8765 --expected-commit "$TARGET_SHA" --json > /tmp/nutev-http-preflight.json; then
  cat /tmp/nutev-http-preflight.json || true; exit 1
fi
keep_evidence /tmp/nutev-http-preflight.json http-preflight.json
cat /tmp/nutev-http-preflight.json
PREFLIGHT_COMMIT="$(curl -fsS http://127.0.0.1:18765/api/version | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit", ""))')"
test "$PREFLIGHT_COMMIT" = "$TARGET_SHA"
cleanup_preflight
trap - EXIT

docker stop "$OLD_CONTAINER" >/dev/null
OLD_STOPPED=1
test "$(docker inspect -f '{{.State.Running}}' "$OLD_CONTAINER")" = "false"
test -z "$(docker ps -q --filter volume="$OUTPUT_VOLUME")"
docker run --rm --user 0 --entrypoint python \
  -v "$OUTPUT_VOLUME:/snapshot-source:ro" -v "$RECOVERY_DIR:/snapshot-backups" \
  "$IMAGE" tools/recovery_snapshot.py --source /snapshot-source --backup /snapshot-backups/volume --quiesced
test -s "$RECOVERY_DIR/volume/restore-proof.json"
PROMOTED=1
NUTEV_IMAGE="$IMAGE" "${COMPOSE[@]}" up -d --no-build "${DEPLOY_SERVICES[@]}"

production_ok=0
for _ in $(seq 1 45); do
  if curl -fsS http://127.0.0.1:8765/api/health >/dev/null; then production_ok=1; break; fi
  sleep 2
done
if [[ "$production_ok" != "1" ]]; then "${COMPOSE[@]}" logs --tail=200 nutev || true; rollback; exit 1; fi

if ! "${COMPOSE[@]}" exec -T nutev python tools/check_predeploy_runtime_contract.py \
  --output-root /app/project_output_reference --write-probe --json > /tmp/nutev-runtime-production.json; then
  keep_evidence /tmp/nutev-runtime-production.json runtime-production.json; cat /tmp/nutev-runtime-production.json || true; rollback; exit 1
fi
keep_evidence /tmp/nutev-runtime-production.json runtime-production.json
cat /tmp/nutev-runtime-production.json
if ! "${COMPOSE[@]}" exec -T nutev python tools/check_runtime_http_surface.py \
  --base-url http://127.0.0.1:8765 --expected-commit "$TARGET_SHA" --json > /tmp/nutev-http-production.json; then
  keep_evidence /tmp/nutev-http-production.json http-production.json; cat /tmp/nutev-http-production.json || true; rollback; exit 1
fi
keep_evidence /tmp/nutev-http-production.json http-production.json
cat /tmp/nutev-http-production.json
DEPLOYED_COMMIT="$(curl -fsS http://127.0.0.1:8765/api/version | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit", ""))')"
if [[ "$DEPLOYED_COMMIT" != "$TARGET_SHA" ]]; then echo "Build identity mismatch" >&2; rollback; exit 1; fi

if ! "${COMPOSE[@]}" exec -T nutev sh -lc 'test -f /app/apps/nutev-web/access-admin.html && test -f /app/apps/nutev-web/access-admin.js && test -f /app/apps/nutev-web/access-flow.css && test -f /app/apps/nutev-web/access-i18n.js && test -f /app/apps/nutev-web/forgot-password.html && test -f /app/apps/nutev-web/forgot-password.js'; then
  echo "::error::Auth/access static assets are missing from the production container." >&2
  rollback
  exit 1
fi

AUTH_EMAIL_RUNTIME="$("${COMPOSE[@]}" exec -T nutev python - <<'PY'
import sys

sys.path.insert(0, "/app/apps/nutev-web")
from transactional_email import email_configured, public_origin

origin = public_origin()
configured = email_configured()
print(f"PUBLIC_ORIGIN_CONFIGURED={'true' if bool(origin) else 'false'}")
print(f"PUBLIC_ORIGIN_EFFECTIVE={origin or 'UNCONFIGURED'}")
print("EMAIL_DELIVERY_CONFIGURED" if configured else "EMAIL_DELIVERY_NOT_CONFIGURED")
print(
    "PASSWORD_RESET_DELIVERY_READY="
    + ("true" if configured and bool(origin) else "false")
)
PY
)"
printf '%s\n' "$AUTH_EMAIL_RUNTIME" | tee "$EVIDENCE_DIR/auth-email-runtime.txt"

public_ok=0
for _ in $(seq 1 30); do
  HEALTH_CODE="$(public_status "$PUBLIC_URL/api/health")"
  VERSION_CODE="$(public_status "$PUBLIC_URL/api/version")"
  SEARCH_CODE="$(public_status "$PUBLIC_URL/search.html")"
  ARTICLES_CODE="$(public_status "$PUBLIC_URL/articles.html")"
  FORGOT_PASSWORD_CODE="$(public_status "$PUBLIC_URL/forgot-password.html")"
  ACCESS_ADMIN_CODE="$(public_status "$PUBLIC_URL/access-admin.html")"
  if acceptable_edge_status "$HEALTH_CODE" && acceptable_edge_status "$VERSION_CODE" \
    && acceptable_edge_status "$SEARCH_CODE" && acceptable_edge_status "$ARTICLES_CODE" \
    && [[ "$FORGOT_PASSWORD_CODE" = "200" ]] && [[ "$ACCESS_ADMIN_CODE" = "200" ]]; then
    if [[ "$VERSION_CODE" = "200" ]]; then
      PUBLIC_COMMIT="$(curl -fsS --max-time 10 "$PUBLIC_URL/api/version" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit", ""))')"
      [[ "$PUBLIC_COMMIT" = "$TARGET_SHA" ]] || { sleep 2; continue; }
    fi
    public_ok=1; break
  fi
  sleep 2
done
if [[ "$public_ok" != "1" ]]; then
  echo "Public HTTPS edge smoke failed for $PUBLIC_URL (expected 200 or Basic-Auth 401 on protected surfaces; auth recovery static pages require HTTP 200)." >&2
  rollback
  exit 1
fi

RESET_REQUEST_CODE="$(curl -sS -o /tmp/nutev-password-reset-smoke.json -w '%{http_code}' --max-time 10 \
  -X POST -H 'Content-Type: application/json' -H "Origin: $PUBLIC_URL" \
  --data '{"email":"release-smoke@example.invalid"}' \
  "$PUBLIC_URL/api/auth/password-reset/request" 2>/dev/null || printf '000')"
if [[ "$RESET_REQUEST_CODE" != "202" ]]; then
  echo "::error::Public password-reset request smoke returned HTTP $RESET_REQUEST_CODE instead of 202." >&2
  rollback
  exit 1
fi

AUTH_STATUS_JSON="$(curl -fsS --max-time 10 "$PUBLIC_URL/api/auth/status")"
AUTH_MODE="$(printf '%s' "$AUTH_STATUS_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("mode", ""))')"
if [[ "$AUTH_MODE" != "pilot" ]]; then
  echo "::error::Public auth status is not pilot mode." >&2
  rollback
  exit 1
fi

ADMIN_ANON_CODE="$(curl -sS -o /tmp/nutev-admin-anonymous-smoke.json -w '%{http_code}' --max-time 10   "$PUBLIC_URL/api/admin/access-requests?status=pending" 2>/dev/null || printf '000')"
if [[ "$ADMIN_ANON_CODE" != "401" ]]; then
  echo "::error::Anonymous admin API smoke returned HTTP $ADMIN_ANON_CODE instead of 401." >&2
  rollback
  exit 1
fi

echo "NutEV deployed successfully at commit $TARGET_SHA using proxy mode $PROXY_MODE"
curl -fsS http://127.0.0.1:8765/api/version | tee "$EVIDENCE_DIR/deployed-version.json"
docker image prune -f --filter "until=168h" >/dev/null 2>&1 || true

# Completion sentinel. Every exit path above either rolls back and exits non-zero or
# reaches this line, so its absence means the script did not run to completion however
# cleanly ssh returned. The workflow treats a missing sentinel as a failed deploy.
printf 'NUTEV_REMOTE_DEPLOY_COMPLETE %s\n' "$TARGET_SHA" | tee "$EVIDENCE_DIR/completion.txt"
