"""Flask web application for BrowserAgent.

Routes:
  GET  /           -> landing page with question input form
  POST /ask        -> submit question, redirect to /session/<id>
  GET  /session/<id>   -> session page showing live step stream
  GET  /stream/<id>    -> SSE endpoint streaming agent steps as JSON
  GET  /health     -> health check (returns {"status": "ok"})
  GET  /api/ask    -> JSON API for programmatic use
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
from typing import Generator

from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for

from .agent import AgentConfig, BrowserAgent
from .logging_config import get_logger, new_request_id, set_request_id, setup_logging

setup_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

app = Flask(__name__)

# In-memory session store: session_id -> {"status", "steps", "answer", "question"}
_sessions: dict[str, dict] = {}

# ─────────────────────────────────────────────────────────────────── HTML ────

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BrowserAgent</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;background:#f8f9fa}
  h1{color:#1a237e}
  .subtitle{color:#555;margin-top:-8px}
  form{margin:24px 0}
  input[type=text]{width:72%;padding:10px 14px;font-size:1rem;border:2px solid #1a237e;border-radius:6px}
  button{padding:10px 22px;font-size:1rem;background:#1a237e;color:#fff;border:none;border-radius:6px;cursor:pointer}
  button:hover{background:#283593}
  .examples{margin:8px 0;color:#777;font-size:.9rem}
  .example-q{cursor:pointer;color:#1565c0;text-decoration:underline;margin-right:12px}
  footer{margin-top:60px;font-size:.8rem;color:#aaa}
</style>
</head>
<body>
<h1>🌐 BrowserAgent</h1>
<p class="subtitle">Answers complex questions by browsing Wikipedia — Yu et al. (TIGER AI Lab), TMLR 2025</p>
<form action="/ask" method="post">
  <input type="text" name="question" id="q" placeholder="Ask a multi-hop question…" required>
  <button type="submit">Ask</button>
</form>
<div class="examples">Try:
  <span class="example-q" onclick="document.getElementById('q').value=this.innerText">Who is the spouse of the director of Schindler's List?</span>
  <span class="example-q" onclick="document.getElementById('q').value=this.innerText">What is the birth city of the founder of Wikipedia?</span>
</div>
<footer>CS 6263 NLP &amp; Agentic AI — UTSA</footer>
</body>
</html>"""

SESSION_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BrowserAgent — {{ question|e }}</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;background:#f8f9fa}
  h1{color:#1a237e;font-size:1.3rem}
  .question{background:#e8eaf6;padding:12px 18px;border-radius:8px;font-size:1.1rem;margin:16px 0}
  .step{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:14px 18px;margin:10px 0}
  .step-header{display:flex;gap:10px;align-items:center}
  .badge{background:#1a237e;color:#fff;border-radius:4px;padding:2px 8px;font-size:.8rem}
  .action{font-weight:bold;color:#283593}
  .reasoning{color:#555;font-size:.9rem;margin:6px 0}
  .url{color:#0077b6;font-size:.8rem;word-break:break-all}
  .memory{color:#2e7d32;font-size:.85rem;margin-top:6px}
  .answer-box{background:#e8f5e9;border:2px solid #2e7d32;border-radius:10px;padding:18px 24px;margin:20px 0;font-size:1.15rem}
  .answer-label{font-weight:bold;color:#2e7d32}
  #spinner{color:#888;font-style:italic}
  a.back{color:#1a237e}
</style>
</head>
<body>
<h1>🌐 BrowserAgent</h1>
<div class="question">❓ {{ question|e }}</div>
<div id="steps"></div>
<div id="spinner">Browsing Wikipedia…</div>
<div id="answer-area"></div>
<br><a class="back" href="/">← Ask another question</a>
<script>
const src = new EventSource('/stream/{{ session_id }}');
src.onmessage = function(e){
  const data = JSON.parse(e.data);
  if(data.event === 'step'){
    const s = data.step;
    const d = document.createElement('div');
    d.className = 'step';
    const args = JSON.stringify(s.args||{});
    d.innerHTML = `
      <div class="step-header"><span class="badge">Step ${s.step}</span>
      <span class="action">${s.action.toUpperCase()}</span></div>
      <div class="reasoning">${s.reasoning||''}</div>
      <div class="url">${s.url||''}</div>
      ${s.memory_update ? '<div class="memory">📌 '+s.memory_update+'</div>' : ''}
      <div style="font-size:.8rem;color:#aaa;margin-top:4px">args: ${args}</div>`;
    document.getElementById('steps').appendChild(d);
  } else if(data.event === 'answer'){
    document.getElementById('spinner').style.display='none';
    document.getElementById('answer-area').innerHTML =
      '<div class="answer-box"><span class="answer-label">✅ Answer:</span> '+data.answer+'</div>';
    src.close();
  } else if(data.event === 'error'){
    document.getElementById('spinner').innerText = '❌ Error: '+data.message;
    src.close();
  }
};
src.onerror = function(){
  document.getElementById('spinner').innerText = 'Stream closed.';
};
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────── Routes ──

@app.route("/")
def index() -> str:
    return INDEX_HTML


@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question", "").strip()
    if not question:
        return redirect(url_for("index"))
    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = {
        "question": question,
        "status": "running",
        "steps": [],
        "answer": "",
    }
    t = threading.Thread(target=_run_agent, args=(session_id, question), daemon=True)
    t.start()
    return redirect(url_for("session_page", session_id=session_id))


@app.route("/session/<session_id>")
def session_page(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return "Session not found", 404
    return render_template_string(
        SESSION_HTML,
        session_id=session_id,
        question=session["question"],
    )


@app.route("/stream/<session_id>")
def stream(session_id: str):
    """SSE endpoint that yields agent steps as JSON events."""
    if session_id not in _sessions:
        return "Session not found", 404

    def generate() -> Generator[str, None, None]:
        q: queue.Queue = _sessions[session_id].get("_queue")
        if q is None:
            yield _sse({"event": "error", "message": "No queue"})
            return
        while True:
            try:
                item = q.get(timeout=60)
            except queue.Empty:
                yield _sse({"event": "error", "message": "Timeout"})
                break
            yield _sse(item)
            if item.get("event") in ("answer", "error"):
                break

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "browseragent"})


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """Synchronous JSON API endpoint."""
    rid = new_request_id()
    logger.info("api_ask_received request_id=%s", rid)
    data = request.get_json(force=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400
    config = AgentConfig(
        max_steps=int(data.get("max_steps", 6)),
        headless=True,
    )
    agent = BrowserAgent(config)
    result = agent.run(question)
    logger.info("api_ask_done request_id=%s answer=%s", rid, result.answer[:80])
    return jsonify({
        "question": result.question,
        "answer": result.answer,
        "steps": result.total_steps,
        "success": result.success,
        "elapsed_seconds": round(result.elapsed_seconds, 2),
        "request_id": rid,
    })


# ─────────────────────────────────────────────────────────────────── Helpers ─

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _run_agent(session_id: str, question: str) -> None:
    """Background thread: run agent and push steps into a queue for SSE."""
    rid = new_request_id()
    logger.info("agent_start session=%s request_id=%s question=%s",
                session_id, rid, question[:80])
    q: queue.Queue = queue.Queue()
    _sessions[session_id]["_queue"] = q

    config = AgentConfig(max_steps=int(os.environ.get("MAX_STEPS", "8")), headless=True)
    agent = BrowserAgent(config)

    answer = ""
    try:
        for step in agent.stream(question):
            _sessions[session_id]["steps"].append(step)
            q.put({"event": "step", "step": step})
            if step.get("action") == "stop":
                answer = step.get("answer", "")

        _sessions[session_id]["status"] = "done"
        _sessions[session_id]["answer"] = answer
        q.put({"event": "answer", "answer": answer or "No answer found."})
        logger.info("agent_done session=%s request_id=%s answer=%s",
                    session_id, rid, answer[:80])
    except Exception as exc:
        logger.error("agent_error session=%s error=%s", session_id, exc)
        _sessions[session_id]["status"] = "error"
        q.put({"event": "error", "message": str(exc)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
