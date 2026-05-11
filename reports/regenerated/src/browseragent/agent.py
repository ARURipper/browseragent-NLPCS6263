"""Agentic loop: prompt construction, LLM call, action dispatch, memory update."""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Generator, Optional

import anthropic

from .browser import BrowserSession
from .logging_config import get_request_id

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for the BrowserAgent."""
    model: str = "claude-sonnet-4-20250514"
    max_steps: int = 10
    temperature: float = 0.0
    max_tokens: int = 512
    start_url: str = "https://en.wikipedia.org"
    headless: bool = True


@dataclass
class AgentResult:
    """Result from running the agent."""
    question: str
    answer: str
    steps: List[dict]
    success: bool
    total_steps: int
    elapsed_seconds: float


SYSTEM_PROMPT = """You are a web browsing agent that answers questions by navigating Wikipedia pages.

You must respond with ONLY a JSON object (no markdown fences, no extra text) with these exact keys:
- "reasoning": A single sentence explaining your thought process
- "action": One of "search", "goto", "scroll", or "stop"
- "args": An object containing action-specific arguments:
  - For "search": {"query": "search terms"}
  - For "goto": {"url": "full URL to navigate to"}
  - For "scroll": {"direction": "down" or "up"}
  - For "stop": {"answer": "your final answer"}
- "memory_update": A single factual sentence to remember, or empty string if nothing new learned

Rules:
1. Use "search" to look up entities on Wikipedia
2. Use "goto" to navigate to specific Wikipedia article links you see on the page
3. Use "scroll" to see more content on the current page
4. Use "stop" ONLY when you are confident you have found the final answer
5. Keep memory_update factual and under one sentence
6. For multi-hop questions, gather information step by step before answering

Example response:
{"reasoning": "I need to find information about the director first.", "action": "search", "args": {"query": "Schindler's List director"}, "memory_update": ""}"""


class BrowserAgent:
    """Agent that browses the web to answer questions."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration. Uses defaults if not provided.
        """
        self.config = config or AgentConfig()
        self._client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self._browser: Optional[BrowserSession] = None
        self._memory: List[str] = []

    def _build_user_prompt(
        self, question: str, current_url: str, current_page: str
    ) -> str:
        """Build the user prompt for the LLM."""
        # Truncate page content to 8000 chars
        truncated_page = current_page[:8000] if len(current_page) > 8000 else current_page
        
        # Format memory as bullet list
        memory_str = ""
        if self._memory:
            memory_str = "\n".join(f"- {m}" for m in self._memory)
        
        prompt_data = {
            "question": question,
            "memory": memory_str,
            "current_url": current_url,
            "current_page": truncated_page,
        }
        return json.dumps(prompt_data)

    def _parse_action(self, response_text: str) -> dict:
        """Parse the LLM response into an action dict."""
        # Strip markdown fences if present
        text = response_text.strip()
        if text.startswith("