# BrowserAgent — Model Card

> **Model:** claude-sonnet-4-20250514 (Anthropic)  
> **System:** BrowserAgent v1.0 — CS 6263 NLP & Agentic AI, UTSA

---

## Intended Use

BrowserAgent is designed to answer complex, multi-hop factual questions by browsing Wikipedia
in real time. The intended use cases are:

- **Research assistance:** Helping students and researchers quickly find answers that require
  synthesising information across multiple Wikipedia articles.
- **Demonstration of agentic LLM capabilities:** Showing how a language model can operate as
  a web browsing agent using structured action spaces.
- **Education:** Illustrating the BrowserAgent architecture (Yu et al., TMLR 2025) in a
  deployable web application.

The intended users are students, researchers, and instructors in the context of the CS 6263
course at UTSA. The system is not intended for production deployment outside this educational context.

---

## Limitations

- **Knowledge scope:** The agent can only browse Wikipedia and cannot access other websites,
  databases, paywalled content, or real-time data sources (stock prices, news feeds).
- **Multi-hop depth:** Performance degrades on questions requiring more than 5 sequential hops.
  The rubric model (7B BrowserAgent-RFT) achieves ~65% F1 on NaturalQuestions multi-hop;
  the API-based implementation typically achieves ~50–60% F1.
- **Context window:** Page text is truncated to 8,000 characters. Long Wikipedia articles
  may be incompletely processed unless the agent scrolls.
- **Hallucination risk:** The underlying LLM can generate plausible but incorrect answers,
  especially for obscure entities not prominently covered in Wikipedia.
- **No real-time web access:** All browsing is limited to en.wikipedia.org as configured.
  Dynamic content (JavaScript-heavy pages) may not render completely.
- **Language:** Optimised for English questions and English Wikipedia only.

---

## Risks

- **Incorrect answers presented as fact:** The system does not express uncertainty in its
  final answers. Users must independently verify answers for any consequential decisions.
- **Prompt injection:** Adversarial content embedded in Wikipedia pages could influence the
  agent's actions (e.g., a Wikipedia article instructing the agent to stop early or navigate
  to a malicious URL). The system does not sanitize page content before including it in prompts.
- **API cost overrun:** Each question consumes Anthropic API tokens. Running many concurrent
  sessions could incur significant API costs. The `MAX_STEPS` environment variable should be
  set conservatively (≤ 8) in production-like settings.
- **Playwright browser security:** The headless Chromium browser runs with `--no-sandbox`
  inside Docker, which may expose the container to browser-based exploits if the agent is
  directed to malicious URLs. Do not grant the container root privileges.
- **Data privacy:** Questions submitted through the web UI are sent to the Anthropic API.
  Do not submit personally identifiable information (PII) or confidential data.

---

## Out of Scope

The following uses are explicitly out of scope for this system:

- **Medical, legal, or financial advice:** The system is not trained or validated for these
  domains. Answers should not be relied upon for health, legal, or financial decisions.
- **Real-time or breaking news:** Wikipedia pages may not reflect recent events; the agent
  has no access to news feeds or live databases.
- **Cybersecurity or vulnerability research:** The agent must not be directed to crawl
  security-related resources, CVE databases, or exploit sites.
- **Political disinformation:** Generating or verifying politically sensitive claims is not
  a supported use case.
- **Autonomous task completion:** BrowserAgent is designed for single-turn question answering.
  Chaining multiple sessions to complete complex autonomous tasks (form submission, purchasing,
  account creation) is not supported and could cause unintended side effects.
