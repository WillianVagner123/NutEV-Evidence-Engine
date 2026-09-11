#!/usr/bin/env bash
# Only disposable local Docker resources. Never takes a server/SSH/volume argument.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/package_audit"
mkdir -p "$OUT"
TEMP=$(mktemp -d)
ID="nutev-audit-${GITHUB_RUN_ID:-local}-${RANDOM}"
APP_ID=''
CONTEXT_ID=''
cleanup() {
  if [[ -n "$APP_ID" ]]; then docker rm -fv "$APP_ID" >/dev/null 2>&1 || true; fi
  if [[ -n "$CONTEXT_ID" ]]; then docker rm -fv "$CONTEXT_ID" >/dev/null 2>&1 || true; fi
  docker image rm "$ID-app" "$ID-context" >/dev/null 2>&1 || true
  rm -rf "$TEMP"
}
trap cleanup EXIT
cd "$ROOT"
SHA=$(git rev-parse HEAD)
git archive "$SHA" | tar -x -C "$TEMP"
# Synthetic forbidden files deliberately inserted after checkout.
CANARY="NUTEV_PACKAGE_PRIVATE_$(python3 -c 'import uuid; print(uuid.uuid4().hex)')"
mkdir -p "$TEMP/project_output_private" "$TEMP/deploy/hetzner/backups" "$TEMP/apps/nutev-web/project_output_other"
printf '%s' "$CANARY" > "$TEMP/project_output_private/records.json"
printf '%s' "$CANARY" > "$TEMP/deploy/hetzner/.env"
printf '%s' "$CANARY" > "$TEMP/deploy/hetzner/backups/records.sqlite"
printf '%s' "$CANARY" > "$TEMP/apps/nutev-web/project_output_other/records.json"
printf '%s' "$CANARY" > "$TEMP/apps/nutev-web/credentials.key"
printf 'FROM scratch\nCOPY . /payload\n' | docker build -q -f - -t "$ID-context" "$TEMP"
CONTEXT_ID=$(docker create "$ID-context" /noop)
docker export "$CONTEXT_ID" -o "$TEMP/context.tar"
python3 - "$TEMP/context.tar" "$OUT/context-boundary.json" "$CANARY" <<'PY'
import json,sys,tarfile
from pathlib import Path
with tarfile.open(sys.argv[1]) as archive:
    names = archive.getnames()
    assert 'payload/src/nutev/__init__.py' in names
    for item in archive:
        if item.isfile():
            stream = archive.extractfile(item)
            assert stream is not None
            assert sys.argv[3].encode() not in stream.read(), item.name
Path(sys.argv[2]).write_text(json.dumps({'status':'PASS','synthetic_canaries_excluded':5,'production_touched':False})+'\n')
PY
VERSION=$(python3 -c 'ns={};exec(open("src/nutev/__version__.py").read(),ns);print(ns["__version__"])')
docker build --build-arg "NUTEV_BUILD_COMMIT=$SHA" --build-arg "NUTEV_VERSION=$VERSION" \
  --build-arg NUTEV_BUILD_BRANCH=release-audit -f deploy/hetzner/Dockerfile -t "$ID-app" .
APP_ID=$(docker run -d --network bridge -p 127.0.0.1::8765 \
  -e NUTEV_AUTH_MODE=pilot -e NUTEV_ENVIRONMENT=test -e NUTEV_DISABLE_NETWORK=1 "$ID-app")
PORT=$(docker port "$APP_ID" 8765/tcp | awk -F: '{print $NF}')
READY=0
for _ in $(seq 1 45); do
  if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/api/health" >/dev/null; then READY=1; break; fi
  sleep 1
done
test "$READY" = 1
docker exec "$APP_ID" python tools/check_runtime_http_surface.py \
  --base-url http://127.0.0.1:8765 --expected-commit "$SHA" --json > "$OUT/container-runtime.json"
docker exec "$APP_ID" python tools/check_predeploy_runtime_contract.py --json > "$OUT/container-contract.json"
docker run --rm --network none --user 0 --entrypoint python \
  -e PYTHONPATH=/app/src:/app "$ID-app" tools/container_recovery_fixture.py > "$OUT/container-recovery.json"
# Exercise the actual workflow's pre-promotion restart and post-failure rollback.
bash tools/rehearse_release_recovery.sh "$ID-app" "$OUT"
