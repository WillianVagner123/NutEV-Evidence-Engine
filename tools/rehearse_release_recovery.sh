#!/usr/bin/env bash
# Invoke only from the disposable container gate. No SSH or production inputs.
set -euo pipefail
IMAGE="${1:?candidate image required}"
OUT="${2:?evidence directory required}"
[[ "$IMAGE" =~ ^nutev-audit-[A-Za-z0-9-]+-app$ ]]
ID="${IMAGE%-app}-recovery"
TEMP=$(mktemp -d)
mkdir -p "$OUT"
COMPOSE_PROJECT="$ID"
cleanup() {
  docker compose --project-name "$COMPOSE_PROJECT" --env-file "$TEMP/.env" -f "$TEMP/compose.yaml" down -v >/dev/null 2>&1 || true
  docker image rm "$ID-broken" nutev:rollback >/dev/null 2>&1 || true
  rm -rf "$TEMP"
}
trap cleanup EXIT
printf 'NUTEV_IMAGE=%s\n' "$IMAGE" > "$TEMP/.env"
cat > "$TEMP/compose.yaml" <<'YAML'
services:
  nutev:
    image: ${NUTEV_IMAGE}
    ports:
      - "127.0.0.1:8765:8765"
    environment:
      NUTEV_AUTH_MODE: pilot
      NUTEV_ENVIRONMENT: test
      NUTEV_DISABLE_NETWORK: "1"
    volumes:
      - fixture:/app/project_output_reference
  caddy:
    image: ${NUTEV_IMAGE}
    entrypoint: ["python", "-c", "import time; time.sleep(600)"]
    network_mode: none
volumes:
  fixture:
YAML
# The sidecar is synthetic: this proves workflow recovery wiring, not real TLS.
COMPOSE=(docker compose --project-name "$COMPOSE_PROJECT" --env-file "$TEMP/.env" -f "$TEMP/compose.yaml")
"${COMPOSE[@]}" up -d --no-build
for _ in $(seq 1 45); do
  if curl -fsS --max-time 2 http://127.0.0.1:8765/api/health >/dev/null; then break; fi
  sleep 1
done
curl -fsS --max-time 2 http://127.0.0.1:8765/api/health >/dev/null
OLD_CONTAINER=$("${COMPOSE[@]}" ps -q nutev)
OLD_IMAGE_ID=$(docker inspect -f '{{.Image}}' "$OLD_CONTAINER")
OLD_COMMIT=$(curl -fsS http://127.0.0.1:8765/api/version | python3 -c 'import sys,json;print(json.load(sys.stdin)["commit"])')
[[ "$OLD_COMMIT" =~ ^[0-9a-f]{40}$ ]]
docker exec "$OLD_CONTAINER" python -c 'from pathlib import Path; Path("/app/project_output_reference/recovery-synthetic.txt").write_text("preserve-this-synthetic-decision")'
RECOVERY_DIR="$TEMP/saved"
mkdir -p "$RECOVERY_DIR/config"
cp "$TEMP/.env" "$TEMP/compose.yaml" "$RECOVERY_DIR/config/"
# Extract the actual workflow functions instead of testing a reimplementation.
python3 - "$TEMP/functions.sh" <<'PY'
from pathlib import Path
import sys,textwrap
text=Path('.github/workflows/deploy-hetzner.yml').read_text()
start=text.index('          rollback() {\n')
end=text.index('          set -E\n',start)
code=textwrap.dedent(text[start:end])
assert 'recover_on_error()' in code and '"$RESTORED_COMMIT" = "$OLD_COMMIT"' in code
Path(sys.argv[1]).write_text(code)
PY
bash -n "$TEMP/functions.sh"
# Before promotion, the real error trap must restart the original stopped app.
docker stop "$OLD_CONTAINER" >/dev/null
export OLD_CONTAINER OLD_IMAGE_ID OLD_COMMIT COMPOSE_PROJECT RECOVERY_DIR
set +e
bash -euc 'source "$1"; OLD_STOPPED=1; PROMOTED=0; ROLLBACK_DONE=0; recover_on_error' _ "$TEMP/functions.sh" > "$OUT/prepromotion-recovery.log" 2>&1
STATUS=$?
set -e
test "$STATUS" = 1
test "$(docker inspect -f '{{.State.Running}}' "$OLD_CONTAINER")" = true
# Simulate an image that fails on startup. It must never obtain a release PASS.
printf 'FROM %s\nCMD ["python", "-c", "raise SystemExit(23)"]\n' "$IMAGE" | docker build --network none -q -t "$ID-broken" -
NUTEV_IMAGE="$ID-broken" "${COMPOSE[@]}" up -d --no-build nutev
for _ in $(seq 1 20); do
  if ! curl -fsS --max-time 1 http://127.0.0.1:8765/api/health >/dev/null 2>&1; then break; fi
  sleep 1
done
if curl -fsS --max-time 1 http://127.0.0.1:8765/api/health >/dev/null 2>&1; then
  echo 'Injected failed image unexpectedly healthy' >&2; exit 1
fi
# Exact old image, saved config, same volume, health and old SHA must recover.
bash -euc 'source "$1"; ROLLBACK_DONE=0; rollback; rollback' _ "$TEMP/functions.sh" > "$OUT/rollback-recovery.log" 2>&1
CURRENT=$("${COMPOSE[@]}" ps -q nutev)
test "$(docker inspect -f '{{.Image}}' "$CURRENT")" = "$OLD_IMAGE_ID"
docker exec "$CURRENT" python -c 'from pathlib import Path; assert Path("/app/project_output_reference/recovery-synthetic.txt").read_text()=="preserve-this-synthetic-decision"'
python3 - "$OUT/workflow-recovery.json" "$OLD_COMMIT" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({
 'status':'PASS','workflow_functions_executed':True,
 'prepromotion_restart':True,'injected_failed_image_recovered':True,
 'previous_image_sha_verified':True,'previous_commit':sys.argv[2],
 'saved_configuration_used':True,'synthetic_data_preserved':True,
 'production_touched':False,'real_caddy_tls_tested':False,
 'scope':'disposable recovery mechanics; not production schema compatibility'
},indent=2)+'\n')
PY
