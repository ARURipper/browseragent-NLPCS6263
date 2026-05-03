"""BrowserAgent core: uses OpenAI API to decide browser actions."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Generator, List, Optional

from openai import OpenAI

from .browser import BrowserSession
from .logging_config import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are BrowserAgent, a web agent that answers complex multi-hop questions by browsing Wikipedia. You receive a JSON with question, memory, current_url, current_page. Respond ONLY with a JSON object with keys: reasoning, action, args, memory_update. action must be one of: search, goto, scroll, stop. args schemas: search->{"query":"..."}, goto->{"url":"..."}, scroll->{"direction":"down"|"up"}, stop->{"answer":"..."}. Use stop only when confident."""


@dataclass
class AgentConfig:
    model: str = "gpt-4o-mini"
    max_steps: int = 10
    temperature: float = 0.0
    max_tokens: int = 512
    start_url: str = "https://en.wikipedia.org"
    headless: bool = True


@dataclass
class AgentResult:
    question: str
    answer: str
    steps: List[dict] = field(default_factory=list)
    success: bool = False
    total_steps: int = 0
    elapsed_seconds: float = 0.0


def _parse_action(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Cannot parse action JSON from: {raw[:200]}")


class BrowserAgent:
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self.config = config or AgentConfig()
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def run(self, question: str) -> AgentResult:
        steps = []
        for step_event in self.stream(question):
            steps.append(step_event)
        answer = ""
        for s in reversed(steps):
            if s.get("action") == "stop":
                answer = s.get("args", {}).get("answer", "")
                break
        return AgentResult(
            question=question,
            answer=answer,
            steps=steps,
            success=bool(answer),
            total_steps=len(steps),
            elapsed_seconds=sum(s.get("elapsed", 0) for s in steps),
        )

    def stream(self, question: str) -> Generator[dict, None, None]:
        config = self.config
        memory: List[str] = []
        browser = BrowserSession(start_url=config.start_url, headless=config.headless)
        browser.start()
        page_text = browser._extract_text()
        current_url = browser.current_url()
        try:
            for step_num in range(1, config.max_steps + 1):
                t0 = time.time()
                memory_str = "\n".join(f"- {m}" for m in memory) if memory else "None yet."
                user_content = json.dumps({"question": question, "memory": memory_str, "current_url": current_url, "current_page": page_text}, ensure_ascii=False)
                logger.info("agent_step step=%d url=%s", step_num, current_url)
                response = self._client.chat.completions.create(
                    model=config.model,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                )
                raw = response.choices[0].message.content
                try:
                    action_obj = _parse_action(raw)
                except (ValueError, json.JSONDecodeError) as exc:
                    logger.error("parse_error step=%d error=%s", step_num, exc)
                    yield {"step": step_num, "action": "error", "error": str(exc), "elapsed": time.time() - t0}
                    break
                action = action_obj.get("action", "stop")
                args = action_obj.get("args", {})
                reasoning = action_obj.get("reasoning", "")
                mem_update = action_obj.get("memory_update", "")
                if mem_update:
                    memory.append(mem_update)
                step_data = {"step": step_num, "action": action, "args": args, "reasoning": reasoning, "memory_update": mem_update, "url": current_url, "elapsed": time.time() - t0}
                logger.info("agent_action step=%d action=%s", step_num, action)
                if action == "stop":
                    step_data["answer"] = args.get("answer", "")
                    yield step_data
                    break
                elif action == "search":
                    page_text = browser.search_wikipedia(args.get("query", ""))
                elif action == "goto":
                    page_text = browser.goto(args.get("url", config.start_url))
                elif action == "scroll":
                    page_text = browser.scroll(direction=args.get("direction", "down"))
                current_url = browser.current_url()
                yield step_data
        finally:
            browser.close()
