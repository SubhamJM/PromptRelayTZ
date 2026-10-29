import json
import logging
from typing import Any, Dict, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from backend.app.core.llm import MockOfflineChatModel, get_llm, get_runtime_config
from backend.app.graph.evaluator import evaluate_relay_match, evaluate_verdict, parse_json_verdict
from backend.app.graph.guardrails import (
    sanitize_extractor_output,
    sanitize_reconstructor_output,
)
from backend.app.graph.state import RelayState
from backend.app.models.scenario import Scenario

logger = logging.getLogger(__name__)


def extract_text_from_response(response: Any) -> str:
    """Normalize LangChain response or object into a string."""
    if hasattr(response, "content"):
        content = response.content
    else:
        content = response

    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


extract_text_content = extract_text_from_response


SYSTEM_PROMPT_EXTRACTOR = """You are Agent 1: The Evidence Extractor Agent for an investigative multi-agent pipeline.
You are equipped with high-fidelity visual and documentary evidence ledgers.

MISSION:
Be helpful, observant, and thorough. Your objective is to extract key factual evidence from the evidence dossier and visual feeds:
- Identify key people, personnel, passengers, and suspect descriptions
- Extract specific timestamps and chronological markers
- Record locations, sectors, gates, and room layouts
- Document physical objects, items, luggage tags, tools, and movements
- Distinguish confirmed facts from uncertain/unverified observations
- Filter out obvious irrelevant peripheral noise

COOPERATIVE GUIDANCE:
Be supportive and proactive. Even if the player's instructions are brief, conversational, or casual, extract the essential facts and clues clearly so the team can build an accurate timeline.

STRICT BOUNDARIES:
1. DO NOT render final accusations or operational dispatch actions (Reserved for Agent 3).
2. DO NOT assemble a full minute-by-minute chronology (Reserved for Agent 2).
3. Maintain objective factual reporting."""


def format_evidence_dossier_with_ledger(scenario: Any) -> str:
    """Constructs the high-fidelity evidence briefing and OCR ledger."""
    if isinstance(scenario, dict):
        try:
            scenario = Scenario.model_validate(scenario)
        except Exception:
            pass

    if not isinstance(scenario, Scenario):
        if isinstance(scenario, dict):
            return scenario.get("dossier_text") or scenario.get("noisy_case_file") or ""
        return str(scenario or "")

    lines = [
        f"=== SCENARIO EVIDENCE DOSSIER: {scenario.title.upper()} ===",
        f"Difficulty: {scenario.difficulty} | Mode: {scenario.type.value.upper()}",
        "",
        scenario.dossier_text,
        "",
        "--- HIGH-FIDELITY EVIDENCE & OCR VISUAL LEDGER ---",
    ]

    for idx, item in enumerate(scenario.evidence_items, start=1):
        lines.append(f"\n[EVIDENCE ITEM {idx}: {item.title}] ({item.category} | {item.badge})")
        if item.timestamp:
            lines.append(f"Timestamp: {item.timestamp}")
        if item.description:
            lines.append(f"Visual / Contextual Summary: {item.description}")
        if item.ocr_ledger:
            lines.append(f"OCR Data & Fine Observations:\n{item.ocr_ledger}")

    lines.append("\n=== END EVIDENCE DOSSIER ===")
    return "\n".join(lines)


def node_extractor(state: RelayState, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """Node 1: Evidence Extractor."""
    scenario = state.get("scenario")
    if isinstance(scenario, dict):
        try:
            scenario = Scenario.model_validate(scenario)
        except Exception:
            pass
    user_prompt = (state.get("p1_prompt") or state.get("user_1_prompt") or "").strip()
    active_llm = llm or get_llm()

    if scenario:
        dossier = format_evidence_dossier_with_ledger(scenario)
    else:
        dossier = state.get("case_file") or ""

    prompt_str = user_prompt if user_prompt else "[No specific user prompt provided]"
    user_message = f"USER PROMPT:\n{prompt_str}\n\n{dossier}"

    try:
        res = active_llm.invoke([
            ("system", SYSTEM_PROMPT_EXTRACTOR),
            ("user", user_message),
        ])
        content = extract_text_from_response(res)
    except Exception as e:
        logger.warning(f"Error in node_extractor: {e}. Checking fallback...")
        if get_runtime_config().fallback_to_offline:
            res = MockOfflineChatModel().invoke([
                ("system", SYSTEM_PROMPT_EXTRACTOR),
                ("user", user_message),
            ])
            content = extract_text_from_response(res)
        else:
            content = f"Error generating extraction: {str(e)}"

    sanitized = sanitize_extractor_output(content)
    return {
        "a1_output": sanitized,
        "agent_1_output": sanitized,
    }


SYSTEM_PROMPT_RECONSTRUCTOR = """You are Agent 2: The Timeline & Incident Reconstructor Agent.
You receive structured facts and extracted evidence provided by Agent 1.

MISSION:
Be helpful, analytical, and structured. Your objective is to synthesize the extracted facts into a clear, chronological sequence of events:
- Organize verified events by minute and timestamp
- Trace key persons, personnel, and movements from start to finish
- Connect causal chains: how one event or action led to the next condition
- Highlight critical security events or discrepancies

COOPERATIVE GUIDANCE:
Even if the player's prompt is simple or conversational, build a clear, readable timeline that connects the key facts so Agent 3 can make a sound deduction.

STRICT BOUNDARIES:
1. DO NOT render a final accusation or verdict (Reserved for Agent 3).
2. Maintain objective neutrality."""


def node_reconstructor(state: RelayState, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """Node 2: Timeline & Incident Reconstructor."""
    user_prompt = (state.get("p2_prompt") or state.get("user_2_prompt") or "").strip()
    evidence_text = state.get("a1_output") or state.get("agent_1_output") or ""
    active_llm = llm or get_llm()

    prompt_str = user_prompt if user_prompt else "[No specific user prompt provided]"
    user_message = (
        f"USER PROMPT:\n{prompt_str}\n\n"
        f"EXTRACTED EVIDENCE FROM AGENT 1:\n{evidence_text}"
    )

    try:
        res = active_llm.invoke([
            ("system", SYSTEM_PROMPT_RECONSTRUCTOR),
            ("user", user_message),
        ])
        content = extract_text_from_response(res)
    except Exception as e:
        logger.warning(f"Error in node_reconstructor: {e}. Checking fallback...")
        if get_runtime_config().fallback_to_offline:
            res = MockOfflineChatModel().invoke([
                ("system", SYSTEM_PROMPT_RECONSTRUCTOR),
                ("user", user_message),
            ])
            content = extract_text_from_response(res)
        else:
            content = f"Error reconstructing timeline: {str(e)}"

    # Determine leak keywords to guardrail
    scenario = state.get("scenario")
    if isinstance(scenario, dict):
        try:
            scenario = Scenario.model_validate(scenario)
        except Exception:
            pass
    gt = (scenario.ground_truth if isinstance(scenario, Scenario) else None) or state.get("ground_truth") or {}
    if hasattr(gt, "culprit"):
        culprit = gt.culprit
        suspects = gt.suspects
    elif isinstance(gt, dict):
        culprit = gt.get("culprit", "")
        suspects = gt.get("suspects", [])
    else:
        culprit, suspects = "", []

    leak_keywords = state.get("leak_keywords", [])
    sanitized = sanitize_reconstructor_output(
        content,
        spoilers=leak_keywords,
        culprit=culprit,
        suspects=suspects,
        additional_keywords=leak_keywords,
    )

    return {
        "a2_output": sanitized,
        "agent_2_output": sanitized,
        "leak_detected": False,
        "leak_keywords_found": [],
    }


SYSTEM_PROMPT_SOLVER = """You are Agent 3: The Logic Solver and Security Decision Agent.
You receive the reconstructed incident timeline alongside governing operational rules to determine the final resolution.

MISSION:
Apply deductive reasoning and rule analysis to deduce the definitive case resolution based on the user's prompt:
- Identify the true culprit or authorized dispatch action
- Explain the precise method, breach mechanism, or protocol followed
- Cite the governing operational rules or protocols applicable to the case
- State the decisive evidence, clues, or blocking conditions

CRITICAL AUTOMATION FORMATTING REQUIREMENT:
The human player may write their prompt in natural, everyday English. You MUST ALWAYS format your final response as a VALID JSON OBJECT for the game scoring system, regardless of whether the user mentions JSON or not:
{
  "culprit": "Exact culprit name or authorized operational dispatch action",
  "method": "Exact breach mechanism or operational safety protocol",
  "motive": "Goal, motive, or security hazard addressed",
  "rule_broken": "Specific rule codes cited (e.g. SEC-101 or OPS-204)",
  "evidence_keys": ["key decisive evidence items, timestamps, and clues"]
}
Do NOT output commentary outside the JSON block. Output valid JSON only."""


def node_solver(state: RelayState, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """Node 3: Logic Solver / Final Detective."""
    scenario = state.get("scenario")
    if isinstance(scenario, dict):
        try:
            scenario = Scenario.model_validate(scenario)
        except Exception:
            pass
    user_prompt = (state.get("p3_prompt") or state.get("user_3_prompt") or "").strip()
    timeline = state.get("a2_output") or state.get("agent_2_output") or ""
    active_llm = llm or get_llm()

    if isinstance(scenario, Scenario) and scenario.operational_rules:
        rules_formatted = "\n".join([f"- {r}" for r in scenario.operational_rules])
    elif isinstance(scenario, dict) and scenario.get("operational_rules"):
        rules_formatted = "\n".join([f"- {r}" for r in scenario["operational_rules"]])
    else:
        rules_formatted = "Standard Operating Protocols and Governing Directives"

    prompt_str = user_prompt if user_prompt else "[No specific user prompt provided]"
    user_message = (
        f"USER PROMPT:\n{prompt_str}\n\n"
        f"GOVERNING OPERATIONAL RULES & PROTOCOLS:\n{rules_formatted}\n\n"
        f"RECONSTRUCTED INCIDENT TIMELINE (From Step 2):\n{timeline}"
    )

    try:
        res = active_llm.invoke([
            ("system", SYSTEM_PROMPT_SOLVER),
            ("user", user_message),
        ])
        content = extract_text_from_response(res)
    except Exception as e:
        logger.warning(f"Error in node_solver: {e}. Checking fallback...")
        if get_runtime_config().fallback_to_offline:
            res = MockOfflineChatModel().invoke([
                ("system", SYSTEM_PROMPT_SOLVER),
                ("user", user_message),
            ])
            content = extract_text_from_response(res)
        else:
            content = json.dumps({"culprit": f"Error: {str(e)}", "method": "", "clue": ""})

    parsed_verdict, was_clean = parse_json_verdict(content)
    return {
        "a3_raw_output": content,
        "agent_3_output": content,
        "raw_agent_3_output": content,
        "final_verdict": parsed_verdict,
        "_was_clean_json": was_clean,
    }


def node_evaluator(state: RelayState) -> Dict[str, Any]:
    """Node 4: Evaluator."""
    scenario = state.get("scenario")
    if isinstance(scenario, dict):
        try:
            scenario = Scenario.model_validate(scenario)
        except Exception:
            pass
    if scenario:
        report = evaluate_relay_match(
            scenario=scenario,
            p1_prompt=state.get("p1_prompt") or state.get("user_1_prompt", ""),
            a1_output=state.get("a1_output") or state.get("agent_1_output", ""),
            p2_prompt=state.get("p2_prompt") or state.get("user_2_prompt", ""),
            a2_output=state.get("a2_output") or state.get("agent_2_output", ""),
            p3_prompt=state.get("p3_prompt") or state.get("user_3_prompt", ""),
            a3_raw_output=state.get("a3_raw_output") or state.get("raw_agent_3_output", ""),
            final_verdict=state.get("final_verdict", {}),
        )
        return {"evaluation": report}
    else:
        # Legacy evaluator
        gt = state.get("ground_truth") or {}
        report = evaluate_verdict(
            final_verdict=state.get("final_verdict", {}),
            ground_truth=gt,
            leak_detected=state.get("leak_detected", False),
            was_clean_json=state.get("_was_clean_json", True),
            user_1_prompt=state.get("user_1_prompt", ""),
            agent_1_output=state.get("agent_1_output", ""),
            user_2_prompt=state.get("user_2_prompt", ""),
            agent_2_output=state.get("agent_2_output", ""),
            user_3_prompt=state.get("user_3_prompt", ""),
            agent_3_output=state.get("raw_agent_3_output", ""),
        )
        return {"evaluation": report}


# Aliases
agent_1_extractor = node_extractor
agent_2_reconstructor = node_reconstructor
agent_3_detective = node_solver
agent_evaluator = node_evaluator
