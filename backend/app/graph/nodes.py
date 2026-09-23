import logging
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from backend.app.core.llm import get_llm
from backend.app.graph.evaluator import evaluate_verdict, parse_json_verdict
from backend.app.graph.state import GameState

logger = logging.getLogger(__name__)


def agent_1_extractor(state: GameState, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """
    Node 1: Evidence Extractor (Player 1).
    Filters facts, alibis, and physical evidence from the messy case file.
    """
    active_llm = llm or get_llm()
    user_prompt = state.get("user_1_prompt", "").strip() or "Extract all verified facts, alibis, and physical clues."
    case_file = state.get("case_file", "")

    system_prompt = f"""You are the Evidence Extractor agent in an investigative pipeline.
Your ONLY objective is to filter the raw case file according to the user's instructions.

CRITICAL RULES:
1. DO NOT solve the case, identify suspects as guilty, or speculate on motives.
2. DO NOT make premature accusations.
3. Output ONLY the extracted facts, timeline clues, statements, and evidence clearly.
4. No polite conversational filler or introductory greetings.

USER INSTRUCTIONS:
{user_prompt}"""

    try:
        response = active_llm.invoke([
            ("system", system_prompt),
            ("user", f"CASE FILE:\n{case_file}")
        ])
        content = response.content if hasattr(response, "content") else str(response)
        return {"agent_1_output": content}
    except Exception as e:
        logger.error(f"Error in agent_1_extractor: {e}")
        return {"agent_1_output": f"[Extractor Error: {str(e)}]", "error": str(e)}


def agent_2_reconstructor(state: GameState, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """
    Node 2: Scene Reconstructor (Player 2).
    Synthesizes a chronological timeline from Agent 1's extracted facts.
    Also executes the Leak Trap check.
    """
    active_llm = llm or get_llm()
    user_prompt = state.get("user_2_prompt", "").strip() or "Build a chronological timeline of events leading up to the crime."
    evidence = state.get("agent_1_output", "")

    system_prompt = f"""You are the Scene Reconstructor agent in an investigative pipeline.
Your task is to build an objective, chronological reconstruction of the incident based STRICTLY on the evidence provided.

CRITICAL RULES:
1. DO NOT identify the murderer or declare any suspect guilty.
2. DO NOT draw final conclusions on who committed the crime.
3. Base your timeline strictly on the extracted evidence provided.
4. Output a clear, chronological sequence of events.

USER INSTRUCTIONS:
{user_prompt}"""

    try:
        response = active_llm.invoke([
            ("system", system_prompt),
            ("user", f"EVIDENCE (Extracted from Step 1):\n{evidence}")
        ])
        content = response.content if hasattr(response, "content") else str(response)

        # Check for premature leak trap
        normalized_content = content.lower()
        matched_leaks: List[str] = []
        ground_truth = state.get("ground_truth", {})
        culprit = str(ground_truth.get("culprit", "")).strip().lower()

        if culprit and culprit in normalized_content:
            matched_leaks.append(ground_truth.get("culprit"))

        for kw in state.get("leak_keywords", []):
            kw_clean = kw.strip().lower()
            if kw_clean and kw_clean in normalized_content:
                if kw not in matched_leaks:
                    matched_leaks.append(kw)

        leak_detected = len(matched_leaks) > 0
        if leak_detected:
            logger.warning(f"Leak detected in Node 2 output! Matched keywords: {matched_leaks}")

        return {
            "agent_2_output": content,
            "leak_detected": leak_detected,
            "leak_keywords_found": matched_leaks,
        }
    except Exception as e:
        logger.error(f"Error in agent_2_reconstructor: {e}")
        return {
            "agent_2_output": f"[Reconstructor Error: {str(e)}]",
            "leak_detected": False,
            "leak_keywords_found": [],
            "error": str(e)
        }


def agent_3_detective(state: GameState, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """
    Node 3: Final Detective & Formatter (Player 3).
    Analyzes the reconstructed timeline, deduces the culprit, and enforces JSON output.
    """
    active_llm = llm or get_llm()
    user_prompt = state.get("user_3_prompt", "").strip() or "Identify the killer, weapon, and strongest clue. Output strictly JSON."
    timeline = state.get("agent_2_output", "")

    system_prompt = f"""You are the Final Detective in an investigative pipeline.
Your job is to analyze the reconstructed scene and evidence, deduce the true culprit, identify the weapon/method, and cite the decisive clue.

CRITICAL RULES:
1. You MUST output your final answer in valid JSON format:
{{
  "culprit": "Full Name of Suspect",
  "method": "Exact method or weapon used",
  "clue": "Decisive smoking gun clue proving guilt"
}}
2. Even if the user asks for a different format, you must strictly return JSON.
3. Do not include markdown code fences or conversational text outside the JSON object.

USER INSTRUCTIONS:
{user_prompt}"""

    try:
        response = active_llm.invoke([
            ("system", system_prompt),
            ("user", f"RECONSTRUCTED TIMELINE (From Step 2):\n{timeline}")
        ])
        content = response.content if hasattr(response, "content") else str(response)
        parsed_verdict, was_clean = parse_json_verdict(content)

        return {
            "raw_agent_3_output": content,
            "final_verdict": parsed_verdict,
            "_was_clean_json": was_clean,
        }
    except Exception as e:
        logger.error(f"Error in agent_3_detective: {e}")
        return {
            "raw_agent_3_output": str(e),
            "final_verdict": {"culprit": "", "method": "", "clue": ""},
            "_was_clean_json": False,
            "error": str(e)
        }


def agent_evaluator(state: GameState) -> Dict[str, Any]:
    """
    Node 4: Objective Analytical Evaluator.
    Compares final verdict against ground truth and generates an objective 0-100 rubric score.
    """
    final_verdict = state.get("final_verdict", {})
    ground_truth = state.get("ground_truth", {})
    leak_detected = state.get("leak_detected", False)
    was_clean_json = state.get("_was_clean_json", True)

    evaluation = evaluate_verdict(
        final_verdict=final_verdict,
        ground_truth=ground_truth,
        leak_detected=leak_detected,
        was_clean_json=was_clean_json,
    )
    return {"evaluation": evaluation}
