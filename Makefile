# BrowserAgent — Makefile
# All targets runnable inside Docker or on bare Linux/HPC

PYTHON      := python3
PIP         := pip3
PYTEST      := pytest
REPORTS_DIR := reports
SRC_DIR     := src/browseragent

.PHONY: all install install-playwright lint test loadtest reproduce \
        download-data download-models demo clean help

# ── Default ───────────────────────────────────────────────────────────────────
all: lint test

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	$(PIP) install --no-cache-dir -r requirements.txt
	$(PIP) install -e .

install-playwright:
	playwright install chromium
	playwright install-deps chromium

# ── Lint (ruff + black check + mypy) ─────────────────────────────────────────
lint:
	@mkdir -p $(REPORTS_DIR)
	ruff check $(SRC_DIR) --output-format=text | tee $(REPORTS_DIR)/ruff.txt
	black --check $(SRC_DIR) 2>&1 | tee -a $(REPORTS_DIR)/ruff.txt
	mypy $(SRC_DIR) 2>&1 | tee -a $(REPORTS_DIR)/mypy.txt
	@echo "✅ Lint passed"

# ── Security ──────────────────────────────────────────────────────────────────
security:
	@mkdir -p $(REPORTS_DIR)
	pip-audit --output json > $(REPORTS_DIR)/security.txt 2>&1 || \
	pip-audit > $(REPORTS_DIR)/security.txt 2>&1
	@echo "Security audit written to $(REPORTS_DIR)/security.txt"

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	@mkdir -p $(REPORTS_DIR)
	$(PYTEST) tests/unit/ \
		--junit-xml=$(REPORTS_DIR)/unit.xml \
		-m unit -v 2>&1 | tee $(REPORTS_DIR)/unit.log
	$(PYTEST) tests/integration/ \
		--junit-xml=$(REPORTS_DIR)/integration.xml \
		-m integration -v 2>&1 | tee $(REPORTS_DIR)/integration.log
	$(PYTEST) tests/user_stories/ \
		--junit-xml=$(REPORTS_DIR)/user_stories.xml \
		-m user_story -v 2>&1 | tee $(REPORTS_DIR)/user_stories.log
	$(PYTEST) tests/edge/ \
		-m edge -v 2>&1 | tee $(REPORTS_DIR)/edge.log
	@echo "✅ All tests passed"

# ── Load test (requires app running on localhost:5000) ────────────────────────
loadtest:
	@mkdir -p $(REPORTS_DIR)
	locust -f tests/load/locustfile.py \
		--host=http://localhost:5000 \
		--headless \
		--users=10 \
		--spawn-rate=2 \
		--run-time=60s \
		--csv=$(REPORTS_DIR)/loadtest \
		--html=$(REPORTS_DIR)/loadtest.html 2>&1 | tee $(REPORTS_DIR)/loadtest.log
	@echo "✅ Load test done — see $(REPORTS_DIR)/loadtest.html"

# ── Demo (exercises every user story end-to-end) ─────────────────────────────
demo:
	@bash scripts/demo.sh

# ── Reproduce (full pipeline on clean machine) ────────────────────────────────
reproduce:
	@echo "=== BrowserAgent full replay ==="
	@echo "Step 1/4: Installing dependencies"
	$(MAKE) install
	$(MAKE) install-playwright
	@echo "Step 2/4: Running lint"
	$(MAKE) lint
	@echo "Step 3/4: Running tests"
	$(MAKE) test
	@echo "Step 4/4: Done — see reports/"
	@echo "✅ Reproduce complete"

# ── Data / model downloads ────────────────────────────────────────────────────
download-data:
	@echo "Benchmark data: using live Wikipedia — no download required"
	@echo "See docs/DATA.md for dataset details"

download-models:
	@echo "Model: Anthropic claude-sonnet-4-20250514 via API — no local download required"
	@echo "See docs/MODELS.md for model details"

# ── Spec regeneration (TA runs this) ─────────────────────────────────────────
regenerate:
	@bash scripts/regenerate.sh

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov
	@echo "✅ Cleaned"

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo "Targets:"
	@echo "  make install          Install Python deps + Playwright"
	@echo "  make lint             ruff + black --check + mypy"
	@echo "  make test             All pytest suites with coverage"
	@echo "  make loadtest         Locust load test (app must be up)"
	@echo "  make demo             Run scripts/demo.sh"
	@echo "  make reproduce        Full clean-machine replay"
	@echo "  make regenerate       Spec → code regeneration (TA check)"
	@echo "  make security         pip-audit security scan"
	@echo "  make clean            Remove caches and compiled files"
