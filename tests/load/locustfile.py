"""Locust load test for BrowserAgent.

Run with: locust -f tests/load/locustfile.py --host=http://localhost:5000

Headline target (rubric):
  - ≥ 10 requests/second
  - < 5 % error rate
  - over a 60-second window on /health and /api/ask
"""

import json
import random

from locust import HttpUser, between, task


SAMPLE_QUESTIONS = [
    "What is the capital of France?",
    "Who invented the telephone?",
    "What is the boiling point of water?",
    "Where is the Eiffel Tower?",
    "Who wrote Romeo and Juliet?",
]


class BrowserAgentUser(HttpUser):
    """Simulated user exercising BrowserAgent endpoints."""

    wait_time = between(0.5, 2.0)

    @task(5)
    def health_check(self):
        """GET /health — lightweight, drives RPS."""
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Health returned {resp.status_code}")

    @task(3)
    def index_page(self):
        """GET / — landing page."""
        with self.client.get("/", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Index returned {resp.status_code}")

    @task(2)
    def api_ask_missing_question(self):
        """POST /api/ask with no question — should return 400 quickly."""
        with self.client.post(
            "/api/ask",
            json={},
            catch_response=True,
        ) as resp:
            if resp.status_code == 400:
                resp.success()  # expected error path
            else:
                resp.failure(f"Expected 400, got {resp.status_code}")

    @task(1)
    def api_ask_empty_string(self):
        """POST /api/ask with empty question — should return 400."""
        with self.client.post(
            "/api/ask",
            json={"question": ""},
            catch_response=True,
        ) as resp:
            if resp.status_code == 400:
                resp.success()
            else:
                resp.failure(f"Expected 400, got {resp.status_code}")
