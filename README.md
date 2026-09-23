# 🕵️ Prompt Relay: The Hot-Seat Sprint (Murder Mystery Edition)

**Prompt Relay** is a sequential, high-stakes prompt-engineering party game designed for live crowds, meetups, hackathons, and conferences. Teams of 3 take turns at a single laptop ("hot seat" style), with each player acting as a human manager for a step in a chained AI pipeline solving a murder mystery.

* **Player 1 (The Extractor):** Filters facts from a noisy case file.
* **Player 2 (The Reconstructor):** Builds a chronological timeline from Player 1's facts (without leaking the killer).
* **Player 3 (The Formatter):** Deduces the culprit and outputs strict JSON.
* **The Roastmaster:** A final judge AI evaluates the pipeline, checks against ground truth, and roasts the teammate who broke the chain.

---

## ⚡ Default LLM Configuration
* **Default LLM Provider:** Google (`gemini`)
* **Default Model:** `gemini-3.5-flash-lite`
* Also supports Anthropic, OpenAI, or local Ollama models.

---

## 🚀 Quickstart

### 1. Prerequisites
* Python 3.12+
* `uv` or `pip`
* Google Gemini API Key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)

### 2. Environment Setup
```bash
cp .env.example .env
# Add your GEMINI_API_KEY into .env
```

### 3. Run the Backend
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```
Interactive API docs will be available at `http://localhost:8000/docs`.

---

## 📚 Documentation & Roadmap
* [event_vision_complete_flow.md](file:///home/ricing/Documents/code/PromptRelay/event_vision_complete_flow.md): Minute-by-minute spectator flow, stage vs. Jumbotron view, and event mechanics.
* [project_phases.md](file:///home/ricing/Documents/code/PromptRelay/project_phases.md): Phased implementation roadmap from setup to production.
* [prompt_relay_readme.md](file:///home/ricing/Documents/code/PromptRelay/prompt_relay_readme.md): Core LangGraph state schema and node specifications.
