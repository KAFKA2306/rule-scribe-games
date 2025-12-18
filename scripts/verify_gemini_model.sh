#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="models/gemini-3-flash-preview"
API_BASE="https://generativelanguage.googleapis.com/v1beta"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

test -n "${GEMINI_API_KEY:-}" || (echo "GEMINI_API_KEY is not set" >&2; exit 1)

echo "RUN_AT=$(date -Is)"
echo "MODEL=${MODEL_ID}"
echo

echo "== (2.1) Verify model exists in list =="
curl -sS \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  "${API_BASE}/models" \
  | grep -nF "${MODEL_ID}"
echo

echo "== (2.2) Verify supportedGenerationMethods includes generateContent =="
curl -sS \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  "${API_BASE}/${MODEL_ID}" \
  | grep -nF "supportedGenerationMethods"
curl -sS \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  "${API_BASE}/${MODEL_ID}" \
  | grep -nF "generateContent"
echo

echo "== (4.1) Smoke generateContent =="
resp_file="/tmp/gemini_generateContent.json"
http_status="$(
  curl -sS \
    -H "x-goog-api-key: ${GEMINI_API_KEY}" \
    -H "Content-Type: application/json" \
    -o "${resp_file}" \
    -w "%{http_code}" \
    "${API_BASE}/${MODEL_ID}:generateContent" \
    -d '{"contents":[{"parts":[{"text":"hello"}]}]}'
)"
echo "HTTP_STATUS=${http_status}"

python - <<'PY'
import json

with open("/tmp/gemini_generateContent.json", "r", encoding="utf-8") as f:
    data = json.load(f)

cand = (data.get("candidates") or [{}])[0]
parts = ((cand.get("content") or {}).get("parts") or [{}])
text = (parts[0] or {}).get("text", "") if parts else ""

print("finishReason:", cand.get("finishReason"))
print("text:", text.strip().replace("\n", " ")[:200])
PY
