# BrowserAgent — Reproduction Guide

## Hardware Profile

| Property | Value |
|----------|-------|
| CPU | Any x86-64 (≥ 2 cores recommended) |
| RAM | ≥ 4 GB |
| GPU | **Not required** (inference via Anthropic API) |
| Storage | ≥ 5 GB (Docker image + Playwright browsers) |
| OS | Linux (Ubuntu 22.04+ recommended) or macOS |
| Internet | Required (Wikipedia + Anthropic API) |

## Expected Runtime

| Step | Time |
|------|------|
| `docker compose build` | 5–8 minutes (first run) |
| `docker compose up` → healthy | < 10 minutes |
| `make test` (all suites) | 30–90 seconds |
| Per question (API mode) | 10–30 seconds |

## Expected Metrics (± tolerance)

| Metric | Expected | Tolerance |
|--------|----------|-----------|
| Token F1 (50-sample NQ) | 0.52 | ± 0.05 |
| Exact Match | 0.28 | ± 0.05 |
| Accuracy @ F1 ≥ 0.5 | 0.50 | ± 0.05 |

These metrics apply to `claude-sonnet-4-20250514` at temperature 0. Actual values depend
on Wikipedia content at evaluation time (live pages change).

## One-Command Replay

```bash
git clone <your-repo-url> browseragent && cd browseragent
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=<your key>
make reproduce
```

`make reproduce` runs in order:
1. `pip install -r requirements.txt`
2. `playwright install chromium`
3. `make lint`
4. `make test`

## Docker Quickstart (TA path)

```bash
git clone <your-repo-url> browseragent && cd browseragent
cp .env.example .env && nano .env   # set ANTHROPIC_API_KEY
docker compose up --build
# Wait for "healthy" status, then open http://localhost:5000
```

## HPC (UTSA ARC) Instructions

See `README.md` → **Running on UTSA ARC HPC** section.

## Seed Value

Random seed: `42` (set in `grading/manifest.yaml`). The agent is deterministic
(temperature=0) so the seed only affects data shuffling if you run batch evaluation.
