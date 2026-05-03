# BrowserAgent — System Specification

> **Version:** 1.0  |  **Course:** CS 6263 NLP & Agentic AI  |  **Instructor:** Dr. Peyman Najafirad

---

## 1. Purpose

BrowserAgent is a web agent that answers complex, multi-hop natural language questions by
browsing live Wikipedia pages through human-inspired browser actions (search, goto, scroll,
stop). Unlike retrieval-augmented generation pipelines that scrape pages into static text,
BrowserAgent reasons directly over raw page state at each step, maintaining an explicit
memory of key conclusions from earlier pages. The system is deployed as a Flask web
application with a streaming UI and a JSON REST API.

**Headline metric:** ≥ 0.50 token-F1 on a 50-question sample from the NaturalQuestions
multi-hop benchmark using the claude-sonnet-4-20250514 model at temperature 0.

---

## 2. Component Inventory

| Component | Module Path | Responsibility |
|-----------|-------------|----------------|
| Agent | `src/browseragent/agent.py` | Agentic loop: prompt construction, LLM call, action dispatch, memory update |
| Browser | `src/browseragent/browser.py` | Playwright-based headless Chrome session; search, goto, scroll, type, screenshot |
| Evaluator | `src/browseragent/evaluator.py` | Token-F1 and exact-match scoring against gold answers |
| App | `src/browseragent/app.py` | Flask web server: `/`, `/ask`, `/session/<id>`, `/stream/<id>`, `/health`, `/api/ask` |
| Logging | `src/browseragent/logging_config.py` | Structured JSON logging with `request_id` propagation via `ContextVar` |

---

## 3. Data Flow

```
User submits question via POST /ask
        │
        ▼
Flask creates session_id (uuid4[:8])
Spawns background thread → _run_agent(session_id, question)
        │
        ▼
BrowserAgent.stream(question):
  ┌─────────────────────────────────────────┐
  │  For each step (max MAX_STEPS):          │
  │  1. Build prompt from:                   │
  │     - question                           │
  │     - memory (List[str])                 │
  │     - current_url                        │
  │     - current_page (≤8000 chars)         │
  │  2. POST to Anthropic /v1/messages       │
  │  3. Parse JSON action from response      │
  │  4. Execute action in Playwright browser │
  │  5. Append memory_update to memory       │
  │  6. Yield step dict → SSE queue          │
  │  7. If action == "stop" → break           │
  └─────────────────────────────────────────┘
        │
        ▼
GET /stream/<session_id>  (SSE)
  → Yields {"event":"step", "step":{...}} per step
  → Yields {"event":"answer", "answer":"..."} when done
        │
        ▼
Browser renders steps + final answer in real time
```

**External dependencies:**
- Anthropic Claude API (HTTPS, outbound port 443)
- Wikipedia (HTTPS, outbound port 443, via Playwright)

---

## 4. Public Interfaces

### 4.1 Web UI

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Landing page with question input form |
| `/ask` | POST | Submit `question` field; redirects to `/session/<id>` |
| `/session/<id>` | GET | Session page with SSE-driven live step display |
| `/stream/<id>` | GET | SSE stream: `text/event-stream`; events: `step`, `answer`, `error` |
| `/health` | GET | Returns `{"status":"ok","service":"browseragent"}` |

### 4.2 JSON REST API

**POST `/api/ask`**

Request body (JSON):
```json
{
  "question": "Who is the spouse of the director of Schindler's List?",
  "max_steps": 8
}
```

Response (JSON):
```json
{
  "question": "...",
  "answer": "Kate Capshaw",
  "steps": 4,
  "success": true,
  "elapsed_seconds": 12.4,
  "request_id": "a1b2c3d4"
}
```

Error response (400):
```json
{"error": "question is required"}
```

### 4.3 Agent Action Schema

The LLM must respond with a JSON object (no markdown fences):

```json
{
  "reasoning": "one sentence",
  "action": "search | goto | scroll | stop",
  "args": {
    "query": "...",    // for search
    "url": "...",      // for goto
    "direction": "down | up",  // for scroll
    "answer": "..."    // for stop
  },
  "memory_update": "one sentence or empty string"
}
```

### 4.4 AgentConfig

```python
@dataclass
class AgentConfig:
    model: str = "claude-sonnet-4-20250514"
    max_steps: int = 10
    temperature: float = 0.0
    max_tokens: int = 512
    start_url: str = "https://en.wikipedia.org"
    headless: bool = True
```

### 4.5 AgentResult

```python
@dataclass
class AgentResult:
    question: str
    answer: str
    steps: List[dict]
    success: bool
    total_steps: int
    elapsed_seconds: float
```

### 4.6 Evaluator Public Functions

```python
def token_f1(prediction: str, gold: str) -> float:
    """Token-level F1 between prediction and gold (SQuAD-style). Range [0,1]."""

def exact_match(prediction: str, gold: str) -> bool:
    """Case-insensitive, punctuation-stripped exact match."""

def evaluate_batch(
    predictions: List[str], golds: List[str], threshold: float = 0.5
) -> dict:
    """Returns {"num_samples", "mean_f1", "exact_match", "accuracy_at_threshold", "threshold"}."""
```

### 4.7 BrowserSession Public Methods

```python
class BrowserSession:
    def start(self) -> None
    def close(self) -> None
    def goto(self, url: str) -> str           # returns page text
    def scroll(self, direction: str) -> str   # "up" or "down"
    def search_wikipedia(self, query: str) -> str
    def current_url(self) -> str
    def screenshot_base64(self) -> str
```

---

## 5. Model and Prompt Selection

### 5.1 LLM

| Property | Value |
|----------|-------|
| Provider | Anthropic |
| Model | `claude-sonnet-4-20250514` |
| Temperature | 0.0 (deterministic) |
| Max tokens | 512 |
| Input format | JSON string with `question`, `memory`, `current_url`, `current_page` |
| Output format | JSON action object (no markdown fences) |

### 5.2 System Prompt Contract

The system prompt instructs the model to:
1. Return ONLY a JSON object with keys: `reasoning`, `action`, `args`, `memory_update`
2. Choose `action` from: `search`, `goto`, `scroll`, `stop`
3. Use `search` to look up entities on Wikipedia
4. Use `stop` only when confident in the final answer
5. Keep `memory_update` factual and under one sentence

### 5.3 Prompt Construction (per step)

```
SYSTEM: <system prompt from §5.2>

USER: {
  "question": "<user question>",
  "memory": "<bullet list of facts from prior steps>",
  "current_url": "<current page URL>",
  "current_page": "<visible page text, truncated to 8000 chars>"
}
```

### 5.4 Action Parsing

Raw LLM output is stripped of markdown fences and parsed as JSON.
On `JSONDecodeError`, the parser falls back to extracting the first `{...}` block.
On second failure, the step is logged as an error and the loop terminates.

---

## 6. Environment Contract

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `PORT` | | 5000 | Flask listening port |
| `LOG_LEVEL` | | INFO | Python log level |
| `MAX_STEPS` | | 8 | Max browsing steps per question |

---

## 7. Deployment

The application is packaged as a multi-stage Docker image.
`docker compose up` brings the system to healthy in under 10 minutes on a machine
with internet access. No GPU is required (all inference is via Anthropic API).

See `docs/REPRODUCE.md` for exact hardware profile and expected runtime.

---

## 8. Testing Contract

Each user story in `docs/STORIES.md` has:
- A `@pytest.mark.user_story("US-NN")` test in `tests/user_stories/`
- Numbered manual steps a TA can follow against the live UI
- A reference screenshot in `docs/assets/stories/us_NN_expected.png`

Coverage threshold: 70% on `src/browseragent/`.
