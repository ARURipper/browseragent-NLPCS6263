#!/usr/bin/env bash
# scripts/regenerate.sh
# TA runs this to test spec-driven regeneration (25-point category).
# Feeds docs/SPEC.md to claude-opus-4-5-20251101 and runs user story tests.
#
# Usage: bash scripts/regenerate.sh
# Requires: ANTHROPIC_API_KEY set in environment

set -euo pipefail

SPEC_FILE="docs/SPEC.md"
PROMPT_FILE="scripts/regenerate_prompt.md"
GEN_DIR="reports/regenerated"
GEN_SRC="$GEN_DIR/src/browseragent"

mkdir -p "$GEN_DIR/src/browseragent"
mkdir -p reports

echo "=== BrowserAgent Spec Regeneration ==="
echo "Spec:   $SPEC_FILE"
echo "Model:  claude-opus-4-5-20251101"
echo "Output: $GEN_DIR"
echo

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set."
  exit 1
fi

SPEC_CONTENT=$(cat "$SPEC_FILE")
PROMPT_TEMPLATE=$(cat "$PROMPT_FILE")

# Build the prompt
FULL_PROMPT="${PROMPT_TEMPLATE}

---

## SPEC

${SPEC_CONTENT}"

echo "[1/4] Calling Anthropic API to regenerate code from spec..."

python3 - <<'PYEOF'
import os, json, sys
import anthropic

spec = open("docs/SPEC.md").read()
prompt_template = open("scripts/regenerate_prompt.md").read()

full_prompt = f"{prompt_template}\n\n---\n\n## SPEC\n\n{spec}"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
response = client.messages.create(
    model="claude-opus-4-5-20251101",
    max_tokens=8192,
    temperature=0,
    messages=[{"role": "user", "content": full_prompt}],
)

raw = response.content[0].text

# Extract Python code blocks and write them
import re, os
blocks = re.findall(r'```python\n# FILE: (.+?)\n(.*?)```', raw, re.DOTALL)
if not blocks:
    # Fallback: write entire output as app.py
    os.makedirs("reports/regenerated/src/browseragent", exist_ok=True)
    with open("reports/regenerated/src/browseragent/app.py", "w") as f:
        f.write(raw)
    print("WARNING: No file markers found; wrote raw output to reports/regenerated/src/browseragent/app.py")
else:
    for filename, code in blocks:
        path = os.path.join("reports/regenerated", filename.strip())
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(code)
        print(f"  Wrote: {path}")

print("Done writing regenerated files.")
PYEOF

echo "[2/4] Running user story tests against regenerated code..."
PYTHONPATH="$GEN_DIR/src:src" \
  python3 -m pytest tests/user_stories/ \
    --junit-xml=reports/regenerate_results.xml \
    -m user_story -v 2>&1 | tee reports/regenerate.log || true

echo "[3/4] Scoring..."
python3 - <<'PYEOF'
import xml.etree.ElementTree as ET
try:
    tree = ET.parse("reports/regenerate_results.xml")
    root = tree.getroot()
    # Handle both <testsuite> and <testsuites> wrapping
    suites = root.findall("testsuite") or [root]
    total = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
    passed = total - failures
    pct = (passed / total * 100) if total > 0 else 0
    print(f"  Passed: {passed}/{total}  ({pct:.1f}%)")
    if pct >= 90:
        print("  ✅ FULL CREDIT (≥90%)")
    elif pct >= 50:
        print(f"  ⚠️  PARTIAL CREDIT ({pct:.1f}%)")
    else:
        print("  ❌ ZERO (<50%)")
except Exception as e:
    print(f"  Could not parse results: {e}")
PYEOF

echo "[4/4] Done. See reports/regenerate.log and reports/regenerate_results.xml"
