# BrowserAgent — Model Documentation

## Primary Inference Model

| Field | Value |
|-------|-------|
| Model ID | `claude-sonnet-4-20250514` |
| Provider | Anthropic |
| Version | Sonnet 4, snapshot 2025-05-14 |
| License | Proprietary (Anthropic API Terms of Service) |
| Access | Via `ANTHROPIC_API_KEY` environment variable |
| Parameters | Not disclosed by Anthropic |
| Input | JSON string (question + memory + page text) |
| Output | JSON action object |
| Temperature | 0.0 (deterministic) |
| Max tokens | 512 |

### Why This Model

The rubric paper (Yu et al., 2025) trains a 7B parameter open-source model
(BrowserAgent-SFT/RFT). For this course project we use `claude-sonnet-4-20250514`
because:

1. It requires no GPU or local model download — works inside Docker with CPU only.
2. Its instruction-following is strong enough to reliably output valid JSON actions.
3. It is available to all students via the course-issued API key.

### Paper Models (for HPC / full reproduction)

| Model | HuggingFace ID | Notes |
|-------|---------------|-------|
| BrowserAgent-SFT | `TIGER-Lab/BrowserAgent-SFT` | 7B, supervised fine-tuned |
| BrowserAgent-RFT | `TIGER-Lab/BrowserAgent-RFT` | 7B, rejection fine-tuned (+20% over SFT) |

To use the paper models, deploy with vLLM and set `OPENAI_API_BASE` to your vLLM endpoint.
See `eval_script/` in the original BrowserAgent repository.

### No Local Model Download Required

```bash
make download-models
# Output: Model: Anthropic claude-sonnet-4-20250514 via API — no local download required
```
