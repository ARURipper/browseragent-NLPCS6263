#!/usr/bin/env bash
# scripts/demo.sh
# Exercises every user story end-to-end against a running app.
# Usage: bash scripts/demo.sh [HOST]
# Default host: http://localhost:5000

set -euo pipefail
HOST="${1:-http://localhost:5000}"
PASS=0; FAIL=0

ok()   { echo "✅ $1"; PASS=$((PASS+1)); }
fail() { echo "❌ $1"; FAIL=$((FAIL+1)); }

echo "=== BrowserAgent Demo ==="
echo "Host: $HOST"
echo

# ── US-04: Health check ───────────────────────────────────────────────────────
echo "[US-04] Health check…"
STATUS=$(curl -o /dev/null -s -w "%{http_code}" "$HOST/health")
if [ "$STATUS" = "200" ]; then ok "GET /health → 200"; else fail "GET /health → $STATUS (expected 200)"; fi

# ── US-01 / US-03: API question ───────────────────────────────────────────────
echo "[US-03] POST /api/ask — valid question…"
RESPONSE=$(curl -s -X POST "$HOST/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?", "max_steps": 4}')
if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'answer' in d and 'request_id' in d"; then
  ok "POST /api/ask returned answer + request_id"
else
  fail "POST /api/ask missing fields: $RESPONSE"
fi

# ── US-05: Empty question → UI redirect ──────────────────────────────────────
echo "[US-05] POST /ask — empty question…"
STATUS=$(curl -o /dev/null -s -w "%{http_code}" -X POST "$HOST/ask" -d "question=")
if [ "$STATUS" = "302" ] || [ "$STATUS" = "200" ]; then
  ok "POST /ask empty → $STATUS (no crash)"
else
  fail "POST /ask empty → $STATUS (expected 302 or 200)"
fi

# ── US-06: API missing question → 400 ────────────────────────────────────────
echo "[US-06] POST /api/ask — missing question…"
STATUS=$(curl -o /dev/null -s -w "%{http_code}" -X POST "$HOST/api/ask" \
  -H "Content-Type: application/json" -d '{}')
if [ "$STATUS" = "400" ]; then ok "POST /api/ask {} → 400"; else fail "POST /api/ask {} → $STATUS (expected 400)"; fi

# ── US-01: Landing page ───────────────────────────────────────────────────────
echo "[US-01] GET / — landing page…"
STATUS=$(curl -o /dev/null -s -w "%{http_code}" "$HOST/")
if [ "$STATUS" = "200" ]; then ok "GET / → 200"; else fail "GET / → $STATUS"; fi

echo
echo "Demo results — PASSED: $PASS   FAILED: $FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "🎉 All demo checks passed!"
  exit 0
else
  exit 1
fi
