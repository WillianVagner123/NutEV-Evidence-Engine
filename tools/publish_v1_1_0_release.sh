#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"
: "${TARGET_SHA:?TARGET_SHA required}"
: "${TAG:?TAG required}"
: "${DEPLOY_RUN_ID:?DEPLOY_RUN_ID required}"
: "${DIST_ARTIFACT_ID:?DIST_ARTIFACT_ID required}"
: "${DIST_ARTIFACT_DIGEST:?DIST_ARTIFACT_DIGEST required}"
: "${CONTAINER_ARTIFACT_ID:?CONTAINER_ARTIFACT_ID required}"
: "${CONTAINER_ARTIFACT_DIGEST:?CONTAINER_ARTIFACT_DIGEST required}"
: "${PREREQ_ARTIFACT_ID:?PREREQ_ARTIFACT_ID required}"
: "${PREREQ_ARTIFACT_DIGEST:?PREREQ_ARTIFACT_DIGEST required}"

WORK="release-work"
ASSETS="release-assets"
rm -rf "$WORK" "$ASSETS"
mkdir -p "$WORK" "$ASSETS"

api_json() {
  local endpoint="$1"
  local output="$2"
  gh api "$endpoint" > "$output"
}

main_sha() {
  gh api "repos/$GITHUB_REPOSITORY/branches/main" --jq '.commit.sha'
}

verify_main() {
  local current
  current="$(main_sha)"
  if [[ "$current" != "$TARGET_SHA" ]]; then
    echo "FAIL: main moved: $current != $TARGET_SHA" >&2
    exit 1
  fi
  echo "main exact SHA: PASS ($TARGET_SHA)"
}

verify_run() {
  local run_id="$1"
  local file="$WORK/run-$run_id.json"
  api_json "repos/$GITHUB_REPOSITORY/actions/runs/$run_id" "$file"
  python - "$file" "$TARGET_SHA" "$run_id" <<'PY'
import json, sys
path, target, run_id = sys.argv[1:4]
data = json.load(open(path, encoding='utf-8'))
assert data['head_sha'] == target, (run_id, data['head_sha'], target)
assert data['status'] == 'completed', (run_id, data['status'])
assert data['conclusion'] == 'success', (run_id, data['conclusion'])
print(f"gate {run_id}: PASS ({data['name']})")
PY
}

verify_main

REQUIRED_RUNS=(
  34698980767
  34698980724
  34698980774
  34698980757
  34698980799
  34698980697
  34698980712
)
for run_id in "${REQUIRED_RUNS[@]}"; do
  verify_run "$run_id"
done

DEPLOY_JSON="$WORK/deploy.json"
deploy_done=false
for _ in $(seq 1 120); do
  api_json "repos/$GITHUB_REPOSITORY/actions/runs/$DEPLOY_RUN_ID" "$DEPLOY_JSON"
  status="$(python - "$DEPLOY_JSON" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['status'])
PY
)"
  if [[ "$status" == "completed" ]]; then
    deploy_done=true
    break
  fi
  sleep 10
done
if [[ "$deploy_done" != "true" ]]; then
  echo "FAIL: deploy did not complete inside release gate" >&2
  exit 1
fi

DEPLOY_UPDATED_AT="$(python - "$DEPLOY_JSON" "$TARGET_SHA" <<'PY'
import json, sys
path, target = sys.argv[1:3]
data=json.load(open(path, encoding='utf-8'))
assert data['head_sha'] == target, (data['head_sha'], target)
assert data['conclusion'] == 'success', data['conclusion']
print(data['updated_at'])
PY
)"
echo "deploy run $DEPLOY_RUN_ID: PASS"

AUDIT_RUN_ID=""
RUNS_JSON="$WORK/workflow-runs.json"
for _ in $(seq 1 90); do
  api_json "repos/$GITHUB_REPOSITORY/actions/runs?head_sha=$TARGET_SHA&event=workflow_run&per_page=100" "$RUNS_JSON"
  AUDIT_RUN_ID="$(python - "$RUNS_JSON" "$DEPLOY_UPDATED_AT" <<'PY'
import json, sys
path, cutoff = sys.argv[1:3]
runs=json.load(open(path, encoding='utf-8')).get('workflow_runs', [])
ok=[r for r in runs if r.get('name') == 'production-doctorate-audit'
    and r.get('status') == 'completed'
    and r.get('conclusion') == 'success'
    and r.get('created_at','') >= cutoff]
ok.sort(key=lambda r:r.get('created_at',''))
print(ok[-1]['id'] if ok else '')
PY
)"
  [[ -n "$AUDIT_RUN_ID" ]] && break
  sleep 10
done
if [[ -z "$AUDIT_RUN_ID" ]]; then
  echo "FAIL: no successful post-deploy doctorate audit found after deploy" >&2
  exit 1
fi
echo "post-deploy audit run: $AUDIT_RUN_ID"

AUDIT_ARTIFACTS="$WORK/audit-artifacts.json"
api_json "repos/$GITHUB_REPOSITORY/actions/runs/$AUDIT_RUN_ID/artifacts" "$AUDIT_ARTIFACTS"
AUDIT_ARTIFACT_ID="$(python - "$AUDIT_ARTIFACTS" <<'PY'
import json, sys
arts=json.load(open(sys.argv[1], encoding='utf-8')).get('artifacts',[])
vals=[a for a in arts if a.get('name','').startswith('doctorate-runtime-') and not a.get('expired')]
assert vals, 'doctorate runtime artifact missing'
print(vals[0]['id'])
PY
)"
mkdir -p "$WORK/doctorate"
gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$AUDIT_ARTIFACT_ID/zip" > "$WORK/doctorate.zip"
unzip -q "$WORK/doctorate.zip" -d "$WORK/doctorate"
AUDIT_JSON="$(find "$WORK/doctorate" -type f -name 'doctorate-runtime.json' -print -quit)"
[[ -n "$AUDIT_JSON" ]]
python - "$AUDIT_JSON" <<'PY'
import json, sys
from pathlib import Path
data=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert data.get('record_type') == 'NUTEV_WILLIAN_DOCTORATE_RUNTIME_AUDIT'
assert data.get('status') == 'PASS'
assert data.get('read_only') is True
assert data.get('scientific_state_modified') is False
assert data.get('legacy_binding_performed') is False
assert data.get('search_executed') is False
assert data['article1']['application_count'] == 0
assert data['article2']['application_count'] == 0
print('post-deploy doctorate audit: PASS, 0 A1 / 0 A2, read-only')
PY

check_artifact() {
  local id="$1"
  local expected="$2"
  local file="$WORK/artifact-$id.json"
  api_json "repos/$GITHUB_REPOSITORY/actions/artifacts/$id" "$file"
  python - "$file" "$TARGET_SHA" "$expected" <<'PY'
import json, sys
path, target, expected = sys.argv[1:4]
data=json.load(open(path, encoding='utf-8'))
assert data.get('digest') == expected, (data.get('digest'), expected)
assert data.get('expired') is False
a=data.get('workflow_run') or {}
assert a.get('head_sha') == target, (a.get('head_sha'), target)
print(f"artifact {data['id']} metadata: PASS")
PY
}

check_artifact "$DIST_ARTIFACT_ID" "$DIST_ARTIFACT_DIGEST"
check_artifact "$CONTAINER_ARTIFACT_ID" "$CONTAINER_ARTIFACT_DIGEST"
check_artifact "$PREREQ_ARTIFACT_ID" "$PREREQ_ARTIFACT_DIGEST"

mkdir -p "$WORK/dist" "$WORK/container" "$WORK/prereq"
gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$DIST_ARTIFACT_ID/zip" > "$WORK/distributions.zip"
gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$CONTAINER_ARTIFACT_ID/zip" > "$WORK/container-audit.zip"
gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$PREREQ_ARTIFACT_ID/zip" > "$WORK/release-prerequisites.zip"
unzip -q "$WORK/distributions.zip" -d "$WORK/dist"
unzip -q "$WORK/container-audit.zip" -d "$WORK/container"
unzip -q "$WORK/release-prerequisites.zip" -d "$WORK/prereq"

WHEEL="$(find "$WORK/dist" -type f -name 'nutev_nutmev-1.1.0-*.whl' -print -quit)"
SDIST="$(find "$WORK/dist" -type f -name 'nutev_nutmev-1.1.0.tar.gz' -print -quit)"
DIST_AUDIT="$(find "$WORK/dist" -type f -path '*/package_audit/distributions.json' -print -quit)"
[[ -n "$WHEEL" && -n "$SDIST" && -n "$DIST_AUDIT" ]]
[[ "$(find "$WORK/dist" -type f -name 'nutev_nutmev-1.1.0-*.whl' | wc -l)" -eq 1 ]]
[[ "$(find "$WORK/dist" -type f -name 'nutev_nutmev-1.1.0.tar.gz' | wc -l)" -eq 1 ]]
cp "$WHEEL" "$ASSETS/"
cp "$SDIST" "$ASSETS/"
cp "$DIST_AUDIT" "$ASSETS/distributions.json"
cp "$WORK/container-audit.zip" "$ASSETS/container-audit.zip"
cp "$WORK/release-prerequisites.zip" "$ASSETS/release-prerequisites.zip"

export AUDIT_RUN_ID AUDIT_ARTIFACT_ID
python - "$AUDIT_JSON" "$ASSETS/release-evidence.json" <<'PY'
import json, os, sys
from pathlib import Path
audit=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
evidence={
  'record_type':'NUTEV_1_1_0_PUBLIC_RELEASE_EVIDENCE',
  'schema_version':1,
  'version':'1.1.0',
  'tag':os.environ['TAG'],
  'target_sha':os.environ['TARGET_SHA'],
  'required_gate_run_ids':[34698980767,34698980724,34698980774,34698980757,34698980799,34698980697,34698980712],
  'required_gates':'7/7 PASS on exact SHA',
  'deploy_run_id':int(os.environ['DEPLOY_RUN_ID']),
  'deploy_status':'PASS',
  'post_deploy_audit_run_id':int(os.environ['AUDIT_RUN_ID']),
  'post_deploy_audit_status':'PASS',
  'scientific_boundary':{
    'read_only':audit['read_only'],
    'scientific_state_modified':audit['scientific_state_modified'],
    'legacy_binding_performed':audit['legacy_binding_performed'],
    'search_executed':audit['search_executed'],
    'article1_application_count':audit['article1']['application_count'],
    'article2_application_count':audit['article2']['application_count'],
  },
  'artifacts':{
    'audited_distributions':{'id':int(os.environ['DIST_ARTIFACT_ID']),'digest':os.environ['DIST_ARTIFACT_DIGEST']},
    'container_audit':{'id':int(os.environ['CONTAINER_ARTIFACT_ID']),'digest':os.environ['CONTAINER_ARTIFACT_DIGEST']},
    'release_prerequisites':{'id':int(os.environ['PREREQ_ARTIFACT_ID']),'digest':os.environ['PREREQ_ARTIFACT_DIGEST']},
    'post_deploy_doctorate_audit':{'id':int(os.environ['AUDIT_ARTIFACT_ID'])},
  },
  'scientific_validation_status':'B — DEMOTE',
  'archive_doi':None,
  'archive_note':'No DOI is claimed for v1.1.0 until a real archive service issues and verifies one.',
}
Path(sys.argv[2]).write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
PY

python - "docs/RELEASE_NOTES_1_1_0.md" "$ASSETS/published-release-notes.md" <<'PY'
import os, sys
from pathlib import Path
src=Path(sys.argv[1]).read_text(encoding='utf-8')
src=src.replace('Status: **production accepted / publication pending**.', 'Status: **public GitHub release published / archive DOI pending**.', 1)
src=src.split('## Publication still pending',1)[0].rstrip()
append=f'''\n\n## Verified public release identity\n\nThis GitHub Release is bound to the final publication commit:\n\n`{os.environ['TARGET_SHA']}`\n\nVerified publication evidence:\n\n- tag: `{os.environ['TAG']}`;\n- seven required workflows: **7/7 PASS on the exact SHA**;\n- production deploy run: **#{os.environ['DEPLOY_RUN_ID']} — PASS**;\n- post-deploy doctorate audit run: **#{os.environ['AUDIT_RUN_ID']} — PASS**;\n- post-deploy scientific boundary: **read-only, 0 A1 and 0 A2 applications, no scientific mutation, no Legacy Binding, no search execution**;\n- wheel/sdist and audit evidence hashes: attached in `SHA256SUMS.txt` and `release-evidence.json`.\n\nThe software release does not promote scientific validation. The Reference Engine remains **B — DEMOTE**, and A1/A2 keep their independent academic/provenance gates.\n\nNo DOI is claimed here for v1.1.0. The historical v1.0.0 DOI must not be reused; a version-specific DOI may only be recorded after a real archive record is issued and verified.\n'''
Path(sys.argv[2]).write_text(src+append,encoding='utf-8')
PY

(
  cd "$ASSETS"
  sha256sum nutev_nutmev-1.1.0-* distributions.json container-audit.zip release-prerequisites.zip release-evidence.json > SHA256SUMS.txt
)

verify_main

if gh api "repos/$GITHUB_REPOSITORY/git/ref/tags/$TAG" > "$WORK/tag-ref.json" 2>/dev/null; then
  tag_type="$(python - "$WORK/tag-ref.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['object']['type'])
PY
)"
  tag_sha="$(python - "$WORK/tag-ref.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['object']['sha'])
PY
)"
  if [[ "$tag_type" == "tag" ]]; then
    tag_sha="$(gh api "repos/$GITHUB_REPOSITORY/git/tags/$tag_sha" --jq '.object.sha')"
  fi
  [[ "$tag_sha" == "$TARGET_SHA" ]]
  echo "$TAG already exists on correct target"
else
  gh api -X POST "repos/$GITHUB_REPOSITORY/git/refs" -f ref="refs/tags/$TAG" -f sha="$TARGET_SHA" >/dev/null
  echo "$TAG created on $TARGET_SHA"
fi

if gh api "repos/$GITHUB_REPOSITORY/releases/tags/$TAG" > "$WORK/release.json" 2>/dev/null; then
  python - "$WORK/release.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1], encoding='utf-8'))
assert data['draft'] is False
assert data['prerelease'] is False
PY
  gh release edit "$TAG" --repo "$GITHUB_REPOSITORY" --title "NutEV Reference Engine v1.1.0" --notes-file "$ASSETS/published-release-notes.md"
else
  gh release create "$TAG" --repo "$GITHUB_REPOSITORY" --verify-tag --title "NutEV Reference Engine v1.1.0" --notes-file "$ASSETS/published-release-notes.md"
fi

gh release upload "$TAG" --repo "$GITHUB_REPOSITORY" --clobber \
  "$ASSETS"/nutev_nutmev-1.1.0-*.whl \
  "$ASSETS"/nutev_nutmev-1.1.0.tar.gz \
  "$ASSETS"/distributions.json \
  "$ASSETS"/SHA256SUMS.txt \
  "$ASSETS"/release-evidence.json \
  "$ASSETS"/container-audit.zip \
  "$ASSETS"/release-prerequisites.zip

verify_main
api_json "repos/$GITHUB_REPOSITORY/git/ref/tags/$TAG" "$WORK/final-tag.json"
python - "$WORK/final-tag.json" "$TARGET_SHA" <<'PY'
import json, subprocess, sys
path, target=sys.argv[1:3]
data=json.load(open(path, encoding='utf-8'))
obj=data['object']
sha=obj['sha']
if obj['type']=='tag':
    raw=subprocess.check_output(['gh','api',f"repos/{__import__('os').environ['GITHUB_REPOSITORY']}/git/tags/{sha}"])
    sha=json.loads(raw)['object']['sha']
assert sha==target,(sha,target)
PY
api_json "repos/$GITHUB_REPOSITORY/releases/tags/$TAG" "$WORK/final-release.json"
python - "$WORK/final-release.json" <<'PY'
import json, sys
data=json.load(open(sys.argv[1], encoding='utf-8'))
assert data['draft'] is False
assert data['prerelease'] is False
assert data['tag_name']=='v1.1.0'
names={a['name'] for a in data.get('assets',[])}
required={'distributions.json','SHA256SUMS.txt','release-evidence.json','container-audit.zip','release-prerequisites.zip','nutev_nutmev-1.1.0.tar.gz'}
assert required <= names, required-names
assert any(n.startswith('nutev_nutmev-1.1.0-') and n.endswith('.whl') for n in names)
print('GitHub Release v1.1.0: PASS')
print(data['html_url'])
PY
