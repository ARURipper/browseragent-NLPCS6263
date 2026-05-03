# BrowserAgent — Logging Guide

All log output is structured JSON. Every entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO 8601 UTC | When the log was emitted |
| `level` | string | `INFO`, `WARNING`, `ERROR` |
| `module` | string | Python module name |
| `request_id` | string | 8-char hex, unique per API request |
| `message` | string | Human-readable description |

---

## Worked Example

### 1. Make a request

```bash
curl -s -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?", "max_steps": 3}'
```

Response:
```json
{
  "question": "What is the capital of France?",
  "answer": "Paris",
  "steps": 2,
  "success": true,
  "elapsed_seconds": 6.3,
  "request_id": "a1b2c3d4"
}
```

### 2. Trace in docker compose logs

```bash
docker compose logs app | grep '"request_id": "a1b2c3d4"'
```

Example output (one line per component touched):

```json
{"timestamp":"2025-05-03T14:22:01","level":"INFO","module":"app","request_id":"a1b2c3d4","message":"api_ask_received request_id=a1b2c3d4"}
{"timestamp":"2025-05-03T14:22:01","level":"INFO","module":"agent","request_id":"a1b2c3d4","message":"agent_start session=None request_id=a1b2c3d4 question=What is the capital of France?"}
{"timestamp":"2025-05-03T14:22:02","level":"INFO","module":"agent","request_id":"a1b2c3d4","message":"agent_step step=1 url=https://en.wikipedia.org"}
{"timestamp":"2025-05-03T14:22:04","level":"INFO","module":"agent","request_id":"a1b2c3d4","message":"agent_action step=1 action=search args={\"query\": \"capital France\"}"}
{"timestamp":"2025-05-03T14:22:05","level":"INFO","module":"browser","request_id":"a1b2c3d4","message":"goto url=https://en.wikipedia.org/w/index.php?search=capital+France"}
{"timestamp":"2025-05-03T14:22:06","level":"INFO","module":"agent","request_id":"a1b2c3d4","message":"agent_step step=2 url=https://en.wikipedia.org/wiki/France"}
{"timestamp":"2025-05-03T14:22:07","level":"INFO","module":"agent","request_id":"a1b2c3d4","message":"agent_action step=2 action=stop args={\"answer\": \"Paris\"}"}
{"timestamp":"2025-05-03T14:22:07","level":"INFO","module":"app","request_id":"a1b2c3d4","message":"api_ask_done request_id=a1b2c3d4 answer=Paris"}
```

The trace shows: **input arrival → agent start → model call → browser navigation → stop action → output delivery.**

---

## How request_id is propagated

The `request_id` is generated in `app.py` via `new_request_id()` at the start of each
`/api/ask` call. It is stored in a Python `ContextVar` (`request_id_var`) so that all
code running in the same thread — including `agent.py` and `browser.py` — automatically
includes the same ID in every log line through the `JSONFormatter`.

For the background-thread path (web UI sessions), `set_request_id(rid)` is called at
the start of `_run_agent` to propagate the ID into the worker thread's context.

---

## Viewing logs in production

```bash
# Follow all logs
docker compose logs -f app

# Filter by request_id (replace a1b2c3d4 with your id)
docker compose logs app | grep '"request_id": "a1b2c3d4"'

# Pretty-print (requires jq)
docker compose logs app | grep '"request_id": "a1b2c3d4"' | jq .
```
