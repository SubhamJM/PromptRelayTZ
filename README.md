# 🕵️ Prompt Relay: The Hot-Seat Sprint (Murder Mystery Edition)

**Prompt Relay** is a sequential prompt-engineering challenge where teams of 3 take turns at a single laptop station. Each player acts as the prompt engineer for one link in a chained AI pipeline to solve a murder mystery:

* **Player 1 (The Extractor):** Filters critical facts from a noisy case file without prematurely solving the case.
* **Player 2 (The Reconstructor):** Builds a chronological timeline based strictly on Player 1's extracted facts.
* **Player 3 (The Detective & Formatter):** Deduces the culprit, method, and key clue based on Player 2's timeline, outputting strict JSON.
* **Objective Evaluator:** Compares the final verdict against expected ground truth and scores the team on an objective 0–100 rubric.

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
* [event_vision_complete_flow.md](file:///home/ricing/Documents/code/PromptRelay/event_vision_complete_flow.md): Single-laptop station workflow, handoff mechanics, and scoring rubric.
* [project_phases.md](file:///home/ricing/Documents/code/PromptRelay/project_phases.md): Phased implementation roadmap from setup to tournament leaderboard.
* [prompt_relay_readme.md](file:///home/ricing/Documents/code/PromptRelay/prompt_relay_readme.md): Core LangGraph state schema and node specifications.
