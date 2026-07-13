#!/usr/bin/env bash
# Build a sanitized CI artifact from a NutEV project_output directory.
#
# Usage: build-safe-artifact.sh <src_project_output> <dest_safe_dir>
#
# Policy (docs/DATA_GOVERNANCE.md, docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md):
#   - Upload only metadata, sanitized logs, derived tables and permitted reports.
#   - NEVER upload raw captures, full PDFs/HTML, or unsanitized webhook payloads.
#   - Emit a MANIFEST of everything included.
#   - FAIL if secrets, signed URLs, cookies, or forbidden file types are detected.
set -euo pipefail

SRC="${1:-project_output}"
SAFE="${2:-artifact_safe}"

rm -rf "$SAFE"
mkdir -p "$SAFE"

if [ ! -d "$SRC" ]; then
  echo "::warning::Source '$SRC' not found; producing empty safe artifact."
  echo "no source directory ($SRC)" > "$SAFE/MANIFEST.txt"
  exit 0
fi

# Permitted, derived output directories only. Raw corpus (03_corpus) and the
# Global Watch runs dir (09_global_watch, which holds webhook payloads/captures)
# are intentionally NOT included; the digest report lives in 08_docs.
INCLUDE_DIRS=(02_metadata 06_tables 07_logs 08_docs)

# Forbidden file types (never copied even from included dirs). tar is used
# instead of rsync for portability across runners.
EXCLUDES=(
  --exclude='*.pdf' --exclude='*.PDF'
  --exclude='*.html' --exclude='*.htm'
  --exclude='*.env' --exclude='.env*'
  --exclude='webhook_payload*.json'
  --exclude='*.db' --exclude='*.sqlite' --exclude='*.sqlite3'
  --exclude='*.pem' --exclude='*.key'
  --exclude='cookies*' --exclude='*cookies.json'
)

for d in "${INCLUDE_DIRS[@]}"; do
  if [ -d "$SRC/$d" ]; then
    mkdir -p "$SAFE/$d"
    tar -C "$SRC/$d" "${EXCLUDES[@]}" -cf - . | tar -C "$SAFE/$d" -xf -
  fi
done

# Manifest of everything included.
( cd "$SAFE" && find . -type f | sort ) > "$SAFE/MANIFEST.txt"
echo "===== ARTIFACT MANIFEST ====="
cat "$SAFE/MANIFEST.txt"

# --- Guard 1: forbidden file types must not have slipped in ---
if find "$SAFE" -type f \( \
      -iname '*.pdf' -o -iname '*.html' -o -iname '*.htm' \
      -o -iname '*.env' -o -iname 'webhook_payload*.json' \
      -o -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3' \
      -o -iname '*.pem' -o -iname '*.key' \) | grep -q . ; then
  echo "::error::Forbidden file type present in sanitized artifact."
  find "$SAFE" -type f \( -iname '*.pdf' -o -iname '*.html' -o -iname '*.env' \
      -o -iname 'webhook_payload*.json' -o -iname '*.db' \) || true
  exit 1
fi

# --- Guard 2: secrets / signed URLs / cookies -> FAIL ---
if grep -RInaE \
    -e '(AKIA|ASIA)[0-9A-Z]{16}' \
    -e '(secret|token|password|passwd|api[_-]?key|private[_-]?key)[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/_+.\-]{16,}' \
    -e '(X-Amz-Signature|X-Goog-Signature|Signature|sig|access_token)=[A-Za-z0-9%/_+.\-]{8,}' \
    -e 'Set-Cookie:' -e 'Authorization:[[:space:]]*Bearer' \
    -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
    "$SAFE" ; then
  echo "::error::Secret / signed URL / cookie pattern detected in sanitized artifact."
  exit 1
fi

# --- Guard 3: emails -> WARN (public metadata may legitimately contain emails) ---
if grep -RInaoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$SAFE" | grep -q . ; then
  echo "::warning::Email address(es) present in artifact — verify none are private before sharing."
fi

echo "Sanitized artifact ready at: $SAFE"
