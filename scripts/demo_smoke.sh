#!/usr/bin/env bash
# =============================================================================
# BioMed Knowledge API — Demo Smoke Script
#
# One-click curl-based walkthrough of all core endpoints.
# Designed for screencast, technical walkthroughs, and post-deployment sanity checks.
#
# Usage:
#   chmod +x scripts/demo_smoke.sh
#   ./scripts/demo_smoke.sh              # uses localhost:8000
#   BASE_URL=http://my-host:8000 ./scripts/demo_smoke.sh
#
# Exit code: 0 if all steps pass, 1 otherwise.
# =============================================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $*"; }

check_status() {
  local label="$1" status="$2" expected="$3"
  if [ "$status" = "$expected" ]; then
    pass
  else
    fail "$label — expected status $expected, got $status"
  fi
}

check_json() {
  local label="$1" json="$2" key="$3" expected="$4"
  local actual
  actual=$(echo "$json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('$key',''))" 2>/dev/null || echo "")
  if [ "$actual" = "$expected" ]; then
    pass
  else
    fail "$label — expected $key='$expected', got '$actual'"
  fi
}

echo "=================================================="
echo " BioMed Knowledge API — Smoke Test"
echo " Target: $BASE_URL"
echo "=================================================="

# ---------------------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------------------
echo ""
echo "[1/7] Health check"
HEALTH=$(curl -sf "$BASE_URL/health" 2>/dev/null || echo '{"status":"error"}')
check_json "health" "$HEALTH" "status" "ok"

# ---------------------------------------------------------------------------
# 2. Async Ingest — Create Job
# ---------------------------------------------------------------------------
echo ""
echo "[2/7] Async ingest — create job"
JOB_RESP=$(curl -sf -X POST "$BASE_URL/documents/ingest-jobs" \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}' 2>/dev/null || echo '{"status":"error"}')
check_json "create job" "$JOB_RESP" "status" "pending"
echo "  job created: $(echo "$JOB_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))")"

# ---------------------------------------------------------------------------
# 3. Async Ingest — Poll Job
# ---------------------------------------------------------------------------
echo ""
echo "[3/7] Async ingest — poll until completion"
JOB_ID=$(echo "$JOB_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null || echo "")
if [ -n "$JOB_ID" ] && [ "$JOB_ID" != "None" ]; then
  FINAL_STATUS="pending"
  for i in $(seq 1 20); do
    POLL_RESP=$(curl -sf "$BASE_URL/documents/ingest-jobs/$JOB_ID" 2>/dev/null || echo '{}')
    FINAL_STATUS=$(echo "$POLL_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
    echo "  attempt $i: status=$FINAL_STATUS"
    if [ "$FINAL_STATUS" = "succeeded" ] || [ "$FINAL_STATUS" = "failed" ]; then
      break
    fi
    sleep 0.3
  done
  check_status "poll job" "$FINAL_STATUS" "succeeded"

  DOC_COUNT=$(echo "$POLL_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('document_count',0))" 2>/dev/null || echo "0")
  CHUNK_COUNT=$(echo "$POLL_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('chunk_count',0))" 2>/dev/null || echo "0")
  echo "  documents: $DOC_COUNT, chunks: $CHUNK_COUNT"
else
  fail "extract job_id"
fi

# ---------------------------------------------------------------------------
# 4. Query with Citations
# ---------------------------------------------------------------------------
echo ""
echo "[4/7] RAG query with citations"
QUERY_RESP=$(curl -sf -X POST "$BASE_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the primary endpoint of the ADC trial?","top_k":3}' 2>/dev/null || echo '{}')
HAS_SOURCES=$(echo "$QUERY_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
sources = d.get('sources', [])
print('yes' if len(sources) > 0 else 'no')
" 2>/dev/null || echo "no")
if [ "$HAS_SOURCES" = "yes" ]; then
  pass
  echo "  sources returned: $(echo "$QUERY_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
docs = set(s.get('source','') for s in d.get('sources',[]))
print(', '.join(docs))
" 2>/dev/null || echo "")"
  FIRST_CITE=$(echo "$QUERY_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d.get('sources', [])
print(s[0].get('citation_id','') if s else 'none')
" 2>/dev/null || echo "none")
  echo "  first citation_id: $FIRST_CITE"
else
  fail "query returned sources"
fi

# ---------------------------------------------------------------------------
# 5. Structured Trial Extraction
# ---------------------------------------------------------------------------
echo ""
echo "[5/7] Structured trial extraction"
EXTRACT_RESP=$(curl -sf -X POST "$BASE_URL/extract/trial" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"trial_adc_001"}' 2>/dev/null || echo '{}')
check_json "extract trial" "$EXTRACT_RESP" "validation_status" "valid"
PHASE=$(echo "$EXTRACT_RESP" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('result',{}).get('phase',''))
" 2>/dev/null || echo "")
echo "  extracted phase: $PHASE"

# Also test raw-text extraction
EXTRACT_RAW=$(curl -sf -X POST "$BASE_URL/extract/trial" \
  -H "Content-Type: application/json" \
  -d '{"text":"A Phase I trial of Drug-X in glioma with primary endpoint safety."}' 2>/dev/null || echo '{}')
check_json "extract raw text" "$EXTRACT_RAW" "validation_status" "valid"

# ---------------------------------------------------------------------------
# 6. Agent Report
# ---------------------------------------------------------------------------
echo ""
echo "[6/7] Agent report workflow"
REPORT_RESP=$(curl -sf -X POST "$BASE_URL/agent/report" \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}' 2>/dev/null || echo '{}')
HAS_STEPS=$(echo "$REPORT_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
steps = d.get('steps', [])
print('yes' if len(steps) > 0 else 'no')
" 2>/dev/null || echo "no")
if [ "$HAS_STEPS" = "yes" ]; then
  pass
  STEP_COUNT=$(echo "$REPORT_RESP" | python3 -c "
import sys, json
print(len(json.load(sys.stdin).get('steps',[])))
" 2>/dev/null || echo "0")
  echo "  steps returned: $STEP_COUNT"
  echo "  report length: $(echo "$REPORT_RESP" | python3 -c "
import sys, json
print(len(json.load(sys.stdin).get('report','')))
" 2>/dev/null || echo "0") chars"
else
  fail "report returned steps"
fi

# ---------------------------------------------------------------------------
# 7. 404 / Error Handling
# ---------------------------------------------------------------------------
echo ""
echo "[7/7] Error handling — missing document"
ERR_RESP=$(curl -s -X POST "$BASE_URL/extract/trial" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"nonexistent_doc"}' 2>/dev/null || echo '{}')
check_json "404 error" "$ERR_RESP" "error" "not_found"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=================================================="
echo " Results: $PASS passed, $FAIL failed"
echo "=================================================="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
