# BrowserAgent — User Stories

> **Format:** stable ID (US-NN) · Given/When/Then acceptance criteria · numbered manual steps · reference screenshot  
> **Deadline:** May 10, 11:59 PM  |  **TA:** Mohammad Bahrami Karkevandi

---

## US-01 — Submit a Question and Receive an Answer

**As a** researcher,  
**I want to** type a question into the web UI and receive a final answer from the agent,  
**so that** I can quickly get answers to complex multi-hop questions without browsing manually.

**Given** the application is running at `http://localhost:5000`,  
**When** I type a question into the input field and click Ask,  
**Then** I should be redirected to a session page that streams browsing steps and ultimately shows a final answer.

**Manual walkthrough steps:**
1. Open a browser and navigate to `http://localhost:5000`.
2. Observe the landing page with a text input and an "Ask" button.
3. Type: `Who is the spouse of the director of Schindler's List?`
4. Click the **Ask** button.
5. Observe that the page redirects to `/session/<id>`.
6. Observe that browsing steps appear one by one (action name, reasoning, URL).
7. Wait for the green "✅ Answer:" box to appear.
8. Verify the answer box contains a non-empty string (expected: "Kate Capshaw" or similar).

**Expected screenshot:** `docs/assets/stories/us_01_expected.png`

---

## US-02 — Live Streaming of Browsing Steps

**As a** user,  
**I want to** see each browsing step appear in real time as the agent works,  
**so that** I can follow the agent's reasoning and trust its process.

**Given** I have submitted a question (US-01),  
**When** the agent is running,  
**Then** each step card should appear within 30 seconds of the previous one, showing action type, reasoning, and current URL.

**Manual walkthrough steps:**
1. Submit any question from the landing page (e.g., `What is the birth city of the founder of Wikipedia?`).
2. On the session page, observe that step cards appear sequentially without a full page reload.
3. Confirm each step card shows: step number badge, action type (SEARCH / GOTO / SCROLL / STOP), reasoning text, and URL.
4. Confirm that at least one step shows a non-empty "📌 memory update" line.
5. Confirm the final step shows action STOP with the "✅ Answer" box below.

**Expected screenshot:** `docs/assets/stories/us_02_expected.png`

---

## US-03 — JSON REST API

**As a** developer,  
**I want to** call `POST /api/ask` with a JSON body and receive a JSON answer,  
**so that** I can integrate BrowserAgent into automated pipelines.

**Given** the application is running,  
**When** I send `POST /api/ask` with body `{"question": "What country is the Eiffel Tower in?", "max_steps": 4}`,  
**Then** I receive a 200 JSON response with `answer`, `steps`, `success`, and `request_id` fields.

**Manual walkthrough steps:**
1. Open a terminal.
2. Run:
   ```bash
   curl -s -X POST http://localhost:5000/api/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What country is the Eiffel Tower in?", "max_steps": 4}'
   ```
3. Observe the JSON response printed to the terminal.
4. Verify `"success": true` and `"answer"` is not empty.
5. Note the `"request_id"` value (8-character hex string).

**Expected screenshot:** `docs/assets/stories/us_03_expected.png`

---

## US-04 — Health Check Endpoint

**As a** DevOps engineer,  
**I want to** call `GET /health` and receive a JSON status response,  
**so that** container orchestrators can determine if the service is healthy.

**Given** the application is running,  
**When** I send `GET /health`,  
**Then** I receive `{"status": "ok", "service": "browseragent"}` with HTTP 200.

**Manual walkthrough steps:**
1. Open a terminal.
2. Run: `curl -s http://localhost:5000/health`
3. Observe output: `{"service":"browseragent","status":"ok"}` (key order may vary).
4. Run: `curl -o /dev/null -s -w "%{http_code}" http://localhost:5000/health`
5. Confirm the output is `200`.

**Expected screenshot:** `docs/assets/stories/us_04_expected.png`

---

## US-05 — Error: Empty Question (Error Path)

**As a** user,  
**I want** the system to gracefully handle an empty question submission,  
**so that** the app does not crash and I am returned to the input form.

**Given** the landing page is open,  
**When** I click Ask without typing anything,  
**Then** the browser should remain on or redirect back to the landing page (no 500 error).

**Manual walkthrough steps:**
1. Open `http://localhost:5000`.
2. Leave the input field blank.
3. Click **Ask**.
4. Observe that the browser does NOT navigate to a session page or show a 500 error.
5. Verify the landing page (or a redirect to it) is shown.

**Expected screenshot:** `docs/assets/stories/us_05_expected.png`

---

## US-06 — Error: Invalid API Request (Error Path)

**As a** developer,  
**I want** `POST /api/ask` with a missing `question` field to return a 400 error with a helpful message,  
**so that** API clients can detect and correct malformed requests.

**Given** the application is running,  
**When** I send `POST /api/ask` with an empty JSON body `{}`,  
**Then** I receive HTTP 400 with body `{"error": "question is required"}`.

**Manual walkthrough steps:**
1. Open a terminal.
2. Run:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" \
     -X POST http://localhost:5000/api/ask \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
3. Confirm the output is `400`.
4. Run:
   ```bash
   curl -s -X POST http://localhost:5000/api/ask \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
5. Confirm the response body contains `"error"` key with value `"question is required"`.

**Expected screenshot:** `docs/assets/stories/us_06_expected.png`

---

## US-07 — Request Tracing via Logs

**As a** site reliability engineer,  
**I want** every log line for a request to carry the same `request_id`,  
**so that** I can trace a complete request end-to-end in `docker compose logs`.

**Given** the application is running via `docker compose up`,  
**When** I submit a question via `POST /api/ask` and note the `request_id` in the response,  
**Then** every log line related to that request in `docker compose logs app` contains the same `request_id`.

**Manual walkthrough steps:**
1. In one terminal run: `docker compose logs -f app`
2. In another terminal run:
   ```bash
   curl -s -X POST http://localhost:5000/api/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the capital of France?", "max_steps": 3}'
   ```
3. Note the `request_id` value from the JSON response (e.g., `"a1b2c3d4"`).
4. In the log terminal, search for that `request_id`.
5. Confirm at least 3 log lines appear with that `request_id`: `api_ask_received`, an `agent_action` step, and `api_ask_done`.

**Expected screenshot:** `docs/assets/stories/us_07_expected.png`
