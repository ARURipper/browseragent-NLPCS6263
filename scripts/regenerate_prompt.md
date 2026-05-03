# BrowserAgent — Spec Regeneration Prompt

You are an expert Python software engineer. Your task is to implement a complete, working Flask web application from the specification below.

## Requirements

1. Implement **every** public interface described in the spec exactly as specified.
2. All routes, function signatures, dataclass fields, and return types must match the spec.
3. Output Python source files with this marker format:
   ````
   ```python
   # FILE: src/browseragent/app.py
   <code>
   ```
   ````
4. Implement these files:
   - `src/browseragent/__init__.py`
   - `src/browseragent/logging_config.py`
   - `src/browseragent/evaluator.py`
   - `src/browseragent/agent.py`
   - `src/browseragent/browser.py`
   - `src/browseragent/app.py`
5. The application must pass these tests:
   - `GET /health` returns `{"status": "ok", "service": "browseragent"}`
   - `POST /api/ask` with `{}` body returns HTTP 400 with `{"error": "question is required"}`
   - `POST /api/ask` with `{"question": "..."}` returns HTTP 200 with keys: `question`, `answer`, `steps`, `success`, `elapsed_seconds`, `request_id`
   - `GET /` returns HTTP 200 with an HTML form that POSTs to `/ask`
   - `token_f1("Paris", "Paris")` returns `1.0`
   - `token_f1("London", "Paris")` returns `0.0`
   - `exact_match("france", "France")` returns `True`
6. Use only these imports (from standard library or pinned packages):
   - `flask`, `anthropic`, `playwright`, `dataclasses`, `typing`, `json`, `re`, `uuid`, `os`, `threading`, `queue`, `time`, `logging`, `contextvars`
7. The `request_id` must be an 8-character hex string generated per request.
8. The BrowserSession must use Playwright's `sync_api` with `--no-sandbox` and `--disable-dev-shm-usage` args.
9. `AgentConfig.model` must default to `"claude-sonnet-4-20250514"`.

Implement the full application now, following the spec exactly.
