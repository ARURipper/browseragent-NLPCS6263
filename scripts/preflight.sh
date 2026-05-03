#!/usr/bin/env bash
# scripts/preflight.sh
# Run this before pushing — if it passes locally, your automated grade passes.
# Usage: bash scripts/preflight.sh

set -euo pipefail

PASS=0
FAIL=0

ok()   { echo "✅ $1"; PASS=$((PASS+1)); }
fail() { echo "❌ $1"; FAIL=$((FAIL+1)); }
sep()  { echo "────────────────────────────────────────"; }

echo "════════════════════════════════════════"
echo "  BrowserAgent Preflight Check"
echo "════════════════════════════════════════"

# ── 1. Required files ─────────────────────────────────────────────────────────
sep
echo "Checking required files…"
required_files=(
  "docs/SPEC.md"
  "docs/STORIES.md"
  "docs/DATA.md"
  "docs/MODELS.md"
  "docs/REPRODUCE.md"
  "docs/MODEL_CARD.md"
  "docs/LOGGING.md"
  "docs/benchmarks.md"
  "grading/manifest.yaml"
  "grading/traceability.yaml"
  "Dockerfile"
  "docker-compose.yml"
  ".env.example"
  "Makefile"
  "pyproject.toml"
  "requirements.txt"
  "CONTRIBUTIONS.md"
  "README.md"
  "scripts/regenerate.sh"
  "scripts/regenerate_prompt.md"
  "scripts/demo.sh"
  "tests/unit/test_evaluator.py"
  "tests/unit/test_agent.py"
  "tests/unit/test_app.py"
  "tests/integration/test_pipeline.py"
  "tests/user_stories/test_stories.py"
  "tests/load/locustfile.py"
  "tests/edge/test_edge.py"
  "reports/benchmarks.json"
)

for f in "${required_files[@]}"; do
  if [ -f "$f" ]; then ok "$f"; else fail "MISSING: $f"; fi
done

# ── 2. User story screenshots ─────────────────────────────────────────────────
sep
echo "Checking story screenshots…"
for i in 01 02 03 04 05 06 07; do
  f="docs/assets/stories/us_${i}_expected.png"
  if [ -f "$f" ]; then ok "$f"; else fail "MISSING: $f"; fi
done

# ── 3. Lint ───────────────────────────────────────────────────────────────────
sep
echo "Running lint…"
if make lint > /dev/null 2>&1; then ok "make lint"; else fail "make lint FAILED"; fi

# ── 4. Tests ──────────────────────────────────────────────────────────────────
sep
echo "Running tests…"
if python3 -m pytest tests/unit tests/integration tests/user_stories tests/edge \
    --tb=no -q > /dev/null 2>&1; then
  ok "make test (unit + integration + user_stories + edge)"
else
  fail "make test FAILED — run 'make test' for details"
fi

# ── 5. Security ───────────────────────────────────────────────────────────────
sep
echo "Running security audit…"
if pip-audit --desc 2>/dev/null | grep -q "No known vulnerabilities"; then
  ok "pip-audit clean"
else
  echo "⚠️  pip-audit found issues — check reports/security.txt"
fi

# ── 6. Env template ───────────────────────────────────────────────────────────
sep
echo "Checking .env setup…"
if grep -q "ANTHROPIC_API_KEY" .env.example; then ok ".env.example has ANTHROPIC_API_KEY"; else fail ".env.example missing ANTHROPIC_API_KEY"; fi
if grep -q "\.env" .gitignore 2>/dev/null; then ok ".env in .gitignore"; else fail ".env NOT in .gitignore"; fi

# ── 7. manifest.yaml commit_sha ───────────────────────────────────────────────
sep
echo "Checking manifest…"
if grep -q "FILL_IN" grading/manifest.yaml; then
  fail "grading/manifest.yaml: commit_sha is still placeholder — run: git rev-parse HEAD"
else
  ok "grading/manifest.yaml commit_sha set"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
sep
echo "PASSED: $PASS   FAILED: $FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "🎉 All preflight checks passed!"
  exit 0
else
  echo "Fix the ❌ items above before pushing."
  exit 1
fi
