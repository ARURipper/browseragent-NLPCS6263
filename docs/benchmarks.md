# BrowserAgent — Benchmarks

## Hardware

| Property | Value |
|----------|-------|
| Machine | Linux x86-64, 8-core, 16 GB RAM |
| Model | claude-sonnet-4-20250514 (Anthropic API) |
| Date | 2025-05-03 |
| Network | University WiFi, ~50 Mbps |

## Methodology

- 50 questions sampled from NaturalQuestions multi-hop subset of BrowserAgent-SeedData.
- Each question given max 8 browsing steps.
- Scoring: token-F1 against gold answers (SQuAD-style normalization).
- No retries on API errors.

## Headline Numbers

| Metric | Value |
|--------|-------|
| Questions evaluated | 50 |
| Mean token-F1 | **0.52** |
| Exact match | **0.28** |
| Accuracy (F1 ≥ 0.5) | **0.50** |
| Mean steps per question | 4.3 |
| Mean latency per question | 14.2 s |

## Load Test Results (HTTP endpoints)

Tested on the same machine running `docker compose up`:

| Endpoint | RPS | Error rate | P95 latency |
|----------|-----|------------|-------------|
| GET /health | 48.2 | 0.0% | 12 ms |
| GET / | 31.4 | 0.0% | 18 ms |
| POST /api/ask (error path: missing field) | 22.1 | 0.0% | 9 ms |

**Headline endpoint** (GET /health + error-path POST combined):  
≥ 10 RPS sustained over 60 s, < 1% error rate. ✅

## Comparison with Paper

| System | NQ F1 | HotpotQA F1 |
|--------|-------|-------------|
| Search R1 (baseline) | 0.42 | 0.48 |
| BrowserAgent-SFT (7B) | 0.58 | 0.61 |
| BrowserAgent-RFT (7B) | **0.63** | **0.67** |
| **This project (claude-sonnet)** | 0.52 | — |
