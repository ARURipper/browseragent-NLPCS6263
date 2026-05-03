# BrowserAgent — Usage Guide

## US-01: Submit a Question and Receive an Answer

1. Open your browser and go to `http://localhost:5000`.
2. In the text box, type your question (e.g., *"Who is the spouse of the director of Schindler's List?"*).
3. Click **Ask**.
4. The page refreshes to a session view. Watch step cards appear as the agent browses Wikipedia.
5. When the agent is done, a green **✅ Answer:** box shows the final answer.
6. Click **← Ask another question** to return to the home page.

---

## US-02: Live Streaming of Browsing Steps

The session page automatically streams agent steps via Server-Sent Events (SSE).
Each step card shows:
- **Step number** (blue badge)
- **Action** (SEARCH / GOTO / SCROLL / STOP)
- **Reasoning** — why the agent chose this action
- **URL** — current page being browsed
- **📌 Memory update** — key fact extracted from the page (when non-empty)

No refresh is needed. The stream closes automatically when the agent reaches a STOP action.

---

## US-03: JSON REST API

Send a POST request to `/api/ask`:

```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What country is the Eiffel Tower in?", "max_steps": 4}'
```

Response fields:
- `question` — echoed question
- `answer` — agent's final answer
- `steps` — number of browsing steps taken
- `success` — true if agent found an answer
- `elapsed_seconds` — wall clock time
- `request_id` — 8-char ID for log tracing (see docs/LOGGING.md)

---

## US-04: Health Check Endpoint

```bash
curl http://localhost:5000/health
# → {"status": "ok", "service": "browseragent"}
```

---

## US-05: Error — Empty Question

If you click **Ask** without entering a question, the browser stays on or redirects back to the
landing page. No error page is shown.

---

## US-06: Error — Invalid API Request

If `question` is missing or empty in a `/api/ask` call, the API returns:

```json
HTTP 400
{"error": "question is required"}
```

---

## US-07: Request Tracing via Logs

Every log line produced during an API request includes the same `request_id`.
Use it to trace a full request in `docker compose logs`:

```bash
# Get the request_id from the API response
RID=$(curl -s -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Capital of France?"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['request_id'])")

# Then search logs
docker compose logs app | grep "\"$RID\""
```

See `docs/LOGGING.md` for a full worked example.
