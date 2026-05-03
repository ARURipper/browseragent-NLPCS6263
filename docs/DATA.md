# BrowserAgent — Data Documentation

## Evaluation Dataset

| Field | Value |
|-------|-------|
| Name | NaturalQuestions (multi-hop sample) |
| Version | Live Wikipedia — snapshot 2025-05 |
| License | CC BY-SA 4.0 (Wikipedia content) |
| Source | [Natural Questions](https://ai.google.com/research/NaturalQuestions) |
| Hash | N/A (live Wikipedia; benchmark questions are static) |
| Size | 50 questions (evaluation sample) |

### Sample Question Format

```json
{"question": "Who is the spouse of the director of Schindler's List?", "answer": "Kate Capshaw"}
```

### Download

No bulk download required. Wikipedia is accessed live via Playwright.
To run offline, deploy a local Wikipedia mirror:

```bash
docker run -d --name=wikipedia \
  -p 22015:80 \
  ghcr.io/kiwix/kiwix-serve:3.3.0 \
  wikipedia_en_all_maxi_2022-05.zim
```

Then set `WIKI_URL=http://localhost:22015` in `.env`.

### Benchmark Data (BrowserAgent-SeedData)

The original paper uses:
- `TIGER-Lab/BrowserAgent-SeedData` on HuggingFace
- Datasets: nq, hotpot, 2wiki, popqa, musique, bamboogle

For this course project we use a 50-question NQ sample from the seed data.

```bash
make download-data
```
