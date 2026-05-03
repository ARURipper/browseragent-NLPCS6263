# BrowserAgent

> **CS 6263 NLP & Agentic AI | UTSA | Dr. Peyman Najafirad**  
> Based on: *Yu et al. (TIGER AI Lab), TMLR 2025*  
> Paper: https://arxiv.org/abs/2510.10666

A web agent that answers complex multi-hop questions by browsing live Wikipedia pages
through human-inspired browser actions: search, goto, scroll, stop. Unlike pipelines that
scrape pages into static text, this agent reasons directly over raw page state at each step,
maintaining an explicit memory of key conclusions from earlier pages.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent | Python 3.10 + Anthropic Claude API |
| Browser | Playwright (headless Chromium) |
| Web UI | Flask + SSE streaming |
| Tests | pytest + locust |
| Linting | ruff + black + mypy |
| Container | Docker + docker compose |

---

## Results

| Metric | Value | Tolerance |
|--------|-------|-----------|
| Token F1 (50-sample NQ) | **0.52** | ± 0.05 |
| Exact Match | **0.28** | ± 0.05 |
| Accuracy @ F1 ≥ 0.5 | **0.50** | ± 0.05 |
| HTTP RPS (health endpoint) | **48** | — |
| HTTP Error Rate | **0.0%** | < 5% |

See `docs/benchmarks.md` and `reports/benchmarks.json` for full details.

---

## Source Layout

```
src/browseragent/
  __init__.py          Package init
  agent.py             Agentic browsing loop (LLM + action dispatch + memory)
  browser.py           Playwright browser session wrapper
  evaluator.py         Token-F1 and exact-match scoring
  app.py               Flask web application (UI + REST API)
  logging_config.py    Structured JSON logging with request_id propagation

tests/
  unit/                Fast unit tests (no network)
  integration/         Integration tests (mocked LLM + browser)
  user_stories/        Story acceptance tests
  edge/                Edge case tests
  load/                Locust load test

docs/
  SPEC.md              System specification (feeds spec-regeneration test)
  STORIES.md           User stories with manual walkthrough steps
  usage.md             One usage section per story
  MODEL_CARD.md        Intended use, limitations, risks, out of scope
  LOGGING.md           Structured logging guide with worked example
  DATA.md              Dataset documentation
  MODELS.md            Model documentation
  REPRODUCE.md         Hardware profile + one-command replay
  benchmarks.md        Performance benchmarks

grading/
  manifest.yaml        Pinned versions, seed, commit SHA, metric targets
  traceability.yaml    Story → spec → code → test mapping

scripts/
  preflight.sh         Run before pushing (replicates TA's automated checks)
  regenerate.sh        Spec → code regeneration (25-point TA check)
  demo.sh              End-to-end demo of all user stories
```

---

## Quick Start (Docker — Recommended)

```bash
# 1. Clone
git clone <your-repo-url> browseragent && cd browseragent

# 2. Configure
cp .env.example .env
nano .env          # Set ANTHROPIC_API_KEY=sk-ant-...

# 3. Build and launch
docker compose up --build

# 4. Open the app
open http://localhost:5000
```

> **Time to healthy:** < 10 minutes on first build.  
> All-in-one health check: `curl http://localhost:5000/health`

---

## Quick Start (Linux / HPC — No Docker)

```bash
# 1. Clone
git clone <your-repo-url> browseragent && cd browseragent

# 2. Python environment
conda create -n browseragent python=3.10.12 -y
conda activate browseragent
pip install -r requirements.txt

# 3. Playwright browsers
playwright install chromium
playwright install-deps chromium      # may need sudo on bare Linux

# 4. Configure
cp .env.example .env && nano .env    # set ANTHROPIC_API_KEY

# 5. Run
export $(cat .env | xargs)
python -m browseragent.app           # → http://localhost:5000

# Or for testing only (no browser needed):
make test
```

---

## Running on UTSA ARC HPC

UTSA ARC uses Slurm. Docker is **not available** on compute nodes — use Singularity or run directly.

### Option A — Interactive session (recommended for dev/testing)

```bash
# Request an interactive CPU node
srun --partition=compute --cpus-per-task=4 --mem=8G --time=2:00:00 --pty bash

# Once on the node:
module load anaconda3/2023.09
conda create -n browseragent python=3.10.12 -y
conda activate browseragent
cd $SCRATCH/browseragent
pip install -r requirements.txt
playwright install chromium          # installs to ~/.cache/ms-playwright

# Export your API key (never hardcode it in scripts)
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the app — it will bind to the node's hostname
python -m browseragent.app

# In another terminal, SSH-tunnel to access the UI locally:
# ssh -L 5000:<node-hostname>:5000 <your-utsa-id>@arc.utsa.edu
```

### Option B — Slurm batch job (for tests/evaluation)

Create `run_tests.slurm`:

```bash
#!/bin/bash
#SBATCH --job-name=browseragent
#SBATCH --partition=compute
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=1:00:00
#SBATCH --output=logs/slurm_%j.out

module load anaconda3/2023.09
conda activate browseragent

cd $SCRATCH/browseragent
export ANTHROPIC_API_KEY="$(cat ~/.secrets/anthropic_key)"

make test
```

Submit: `sbatch run_tests.slurm`

### Option C — Singularity (to run Docker image on HPC)

```bash
# On your laptop: save Docker image
docker save browseragent:latest | gzip > browseragent.tar.gz
scp browseragent.tar.gz <arc-user>@arc.utsa.edu:$SCRATCH/

# On ARC login node:
singularity build browseragent.sif docker-archive://browseragent.tar.gz
singularity exec --bind $SCRATCH:/app browseragent.sif \
  python -m browseragent.app
```

### ARC-Specific Notes

- Store code in `$SCRATCH` (not `$HOME`) — home has a 10 GB quota.
- Use `module load anaconda3/2023.09` before creating conda environments.
- Playwright downloads browsers to `~/.cache/ms-playwright` (≈ 300 MB for Chromium).
- The GPU partition (`gpu`) is NOT needed — inference uses the Anthropic API.
- For the 7B BrowserAgent-RFT model (optional, see paper), request `--gres=gpu:1` and use vLLM.

---

## Development Workflow

```bash
# Lint
make lint

# All tests
make test

# Security audit
make security

# Load test (app must be running)
make loadtest

# Full pre-submission check
bash scripts/preflight.sh

# Before pushing — update commit_sha in manifest
git rev-parse HEAD    # copy this into grading/manifest.yaml
```

---

## API Reference

**POST `/api/ask`**
```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who invented the telephone?", "max_steps": 6}'
```

**GET `/health`**  
Returns `{"status":"ok","service":"browseragent"}` — used by Docker health checks.

See `docs/STORIES.md` and `docs/usage.md` for the full manual walkthrough.
