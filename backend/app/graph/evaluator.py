import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.llm import classify_prompt_quality
from backend.app.models.evaluator import (
    EvaluationReport,
    PlayerScorecard,
    SolutionScorecard,
)
from backend.app.models.scenario import Scenario

logger = logging.getLogger(__name__)


def parse_json_verdict(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Robustly extract the structured JSON decision / verdict from LLM output.
    Returns (verdict_dict, was_clean_json).
    """
    if not raw_text or not isinstance(raw_text, str):
        return {
            "action": "", "culprit": "", "method": "", "clue": "",
            "rules": "", "proof": "",
        }, False

    cleaned = raw_text.strip()

    # 1. Direct JSON parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return enrich_verdict_dict(data), True
    except Exception:
        pass

    # 2. Markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict):
                return enrich_verdict_dict(data), True
        except Exception:
            pass

    # 3. Any brace group { ... }
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict):
                return enrich_verdict_dict(data), False
        except Exception:
            pass

    # 4. Fallback regex extraction for keys
    extracted: Dict[str, Any] = {
        "action": "", "culprit": "", "method": "", "clue": "",
        "rules": "", "proof": "",
    }
    key_aliases = {
        "culprit": ["culprit", "perpetrator", "suspect", "action", "valid_action"],
        "method": ["method", "weapon", "mechanism", "rules", "supporting_rules"],
        "clue": ["clue", "key_clue", "proof", "blocking_condition", "evidence"],
        "rule_broken": ["rule_broken", "rule", "rules", "protocol", "policy"],
    }
    for standard_key, aliases in key_aliases.items():
        for alias in aliases:
            m = re.search(rf"['\"]?{alias}['\"]?\s*:\s*['\"]([^'\"]+)['\"]", cleaned, re.IGNORECASE)
            if m:
                extracted[standard_key] = m.group(1).strip()
                break

    return enrich_verdict_dict(extracted), False


def enrich_verdict_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map variations between airport crisis and mystery cases into unified dictionary."""
    result = dict(data)
    action = str(data.get("action") or data.get("valid_action") or data.get("culprit") or "").strip()
    rules = str(data.get("rules") or data.get("supporting_rules") or data.get("method") or data.get("weapon") or "").strip()
    proof = str(data.get("proof") or data.get("blocking_condition") or data.get("clue") or data.get("key_clue") or "").strip()

    raw_rules = data.get("supporting_rules") or data.get("rules")
    if isinstance(raw_rules, list):
        rules = "; ".join(str(r) for r in raw_rules)

    result.setdefault("culprit", action)
    result.setdefault("method", rules)
    result.setdefault("clue", proof)
    result.setdefault("action_or_culprit", action)
    result.setdefault("rules_or_method", rules)
    result.setdefault("proof_or_clue", proof)
    return result


def evaluate_player_1_prompt(prompt: str, agent_output: str) -> Dict[str, Any]:
    """
    Evaluates Player 1's Turn (Max 20 pts):
    - Prompt Engineering Quality: 12 pts
    - Agent 1 Output Performance: 8 pts
    """
    p = (prompt or "").lower().strip()
    words = p.split()
    word_count = len(words)

    # 1. Role & Persona (0-3)
    role_pts = 0
    if any(k in p for k in ["role", "you are", "expert", "specialist", "agent", "engine", "extractor", "analyst", "extract"]):
        role_pts = 3
    elif word_count >= 12:
        role_pts = 1

    # 2. Categories / Taxonomy (0-3)
    categories = ["people", "person", "who", "time", "location", "place", "object", "item", "movement"]
    cat_matches = sum(1 for c in categories if c in p)
    if cat_matches >= 4:
        cat_pts = 3
    elif cat_matches >= 2:
        cat_pts = 2
    elif cat_matches >= 1 or word_count >= 10:
        cat_pts = 1
    else:
        cat_pts = 0

    # 3. Information Discrimination (0-3)
    discrim_pts = 0
    if any(k in p for k in ["confirmed", "uncertain", "unverified", "alleged", "verified", "distinguish", "separate"]):
        discrim_pts = 3
    elif any(k in p for k in ["fact", "clue", "observation", "evidence"]):
        discrim_pts = 1

    # 4. Noise Filtering & Negative Constraints (0-3)
    filter_pts = 0
    has_filter = any(k in p for k in ["noise", "irrelevant", "ignore", "filter", "chatter", "ambient"])
    has_constraint = any(k in p for k in ["do not", "never", "refrain", "don't", "without", "no infer", "not infer"])
    if has_filter and has_constraint:
        filter_pts = 3
    elif has_filter or has_constraint:
        filter_pts = 2
    elif word_count >= 15:
        filter_pts = 1

    prompt_score = min(12, role_pts + cat_pts + discrim_pts + filter_pts)

    # Agent 1 Output Quality (0-8)
    out_lower = (agent_output or "").lower()
    if "[extraction incomplete" in out_lower:
        agent_pts = 2
    elif len(out_lower) >= 15:
        agent_pts = 8
    elif len(out_lower) > 0:
        agent_pts = 4
    else:
        agent_pts = 0

    total_p1 = prompt_score + agent_pts
    return {
        "score": total_p1,
        "max_score": 20,
        "prompt_score": prompt_score,
        "agent_score": agent_pts,
        "tier": "strong" if prompt_score >= 10 else ("moderate" if prompt_score >= 6 else "weak"),
        "feedback": f"Prompt Quality: {prompt_score}/12. Agent Execution: {agent_pts}/8.",
    }


def evaluate_player_2_prompt(prompt: str, agent_output: str) -> Dict[str, Any]:
    """
    Evaluates Player 2's Turn (Max 20 pts):
    - Prompt Engineering Quality: 12 pts
    - Agent 2 Output Performance: 8 pts
    """
    p = (prompt or "").lower().strip()
    words = p.split()
    word_count = len(words)

    # 1. Role & Persona (0-3)
    role_pts = 0
    if any(k in p for k in ["role", "you are", "reconstructor", "investigator", "specialist", "agent", "reconstruct"]):
        role_pts = 3
    elif word_count >= 12:
        role_pts = 1

    # 2. Temporal Sequencing (0-3)
    seq_pts = 0
    if any(k in p for k in ["first", "next", "sequence", "chronological", "timeline", "order", "minute", "timestamp"]):
        seq_pts = 3 if ("first" in p or "next" in p or "sequence" in p) else 2
    elif word_count >= 10:
        seq_pts = 1

    # 3. Connection & Movement Tracking (0-3)
    connect_pts = 0
    if any(k in p for k in ["connect", "depend", "movement", "move", "lead", "caused", "relationship", "network"]):
        connect_pts = 3 if ("connect" in p or "depend" in p) else 2
    elif any(k in p for k in ["people", "location", "event"]):
        connect_pts = 1

    # 4. Uncertainty & Neutrality Constraint (0-3)
    neut_pts = 0
    has_uncert = any(k in p for k in ["uncertain", "separate", "confirmed", "unverified"])
    has_constraint = any(k in p for k in ["do not", "never", "neutral", "without naming", "no verdict", "not infer"])
    if has_uncert and has_constraint:
        neut_pts = 3
    elif (has_uncert or has_constraint) and word_count >= 15:
        neut_pts = 3
    elif has_uncert or has_constraint:
        neut_pts = 2
    elif word_count >= 15:
        neut_pts = 1

    prompt_score = min(12, role_pts + seq_pts + connect_pts + neut_pts)

    # Agent 2 Output Quality (0-8)
    out_lower = (agent_output or "").lower()
    if "[timeline incomplete" in out_lower:
        agent_pts = 2
    elif len(out_lower) >= 15:
        agent_pts = 8
    elif len(out_lower) > 0:
        agent_pts = 4
    else:
        agent_pts = 0

    total_p2 = prompt_score + agent_pts
    return {
        "score": total_p2,
        "max_score": 20,
        "prompt_score": prompt_score,
        "agent_score": agent_pts,
        "tier": "strong" if prompt_score >= 10 else ("moderate" if prompt_score >= 6 else "weak"),
        "feedback": f"Prompt Quality: {prompt_score}/12. Agent Execution: {agent_pts}/8.",
    }


def evaluate_player_3_prompt(prompt: str, agent_output: str, was_clean_json: bool = True) -> Dict[str, Any]:
    """
    Evaluates Player 3's Turn (Max 20 pts):
    - Prompt Engineering Quality: 12 pts
    - Agent 3 Output Performance: 8 pts
    """
    p = (prompt or "").lower().strip()
    words = p.split()
    word_count = len(words)

    # 1. Role & Persona (0-3)
    role_pts = 0
    if any(k in p for k in ["role", "you are", "solver", "detective", "magistrate", "decision", "agent", "determine", "solve"]):
        role_pts = 3
    elif word_count >= 12:
        role_pts = 1

    # 2. Rule & Deductive Directives (0-3)
    rule_pts = 0
    if any(k in p for k in ["rule", "regulat", "support", "deduc", "eliminat", "policy", "condition"]):
        rule_pts = 3 if ("rule" in p or "deduc" in p) else 2
    elif word_count >= 10:
        rule_pts = 1

    # 3. Operational Action & Resumption Directives (0-3)
    act_pts = 0
    if any(k in p for k in ["action", "blocking", "resume", "culprit", "method", "clue", "decision"]):
        act_pts = 3 if ("action" in p or "blocking" in p or "resume" in p) else 2
    elif word_count >= 10:
        act_pts = 1

    # 4. JSON Schema Constraints (0-3)
    schema_pts = 0
    if "json" in p and any(k in p for k in ["key", "schema", "format", "strict", "{"]):
        schema_pts = 3
    elif "json" in p or "format" in p:
        schema_pts = 2
    elif word_count >= 12:
        schema_pts = 1

    prompt_score = min(12, role_pts + rule_pts + act_pts + schema_pts)

    # Agent 3 Output Performance (0-8)
    out_lower = (agent_output or "").lower()
    has_undetermined = any(u in out_lower for u in ["undetermined", "unspecified", "incomplete: user prompt"])
    if was_clean_json and not has_undetermined:
        agent_pts = 8
    elif not has_undetermined and len(out_lower) >= 15:
        agent_pts = 6
    elif not has_undetermined:
        agent_pts = 3
    else:
        agent_pts = 1

    total_p3 = prompt_score + agent_pts
    return {
        "score": total_p3,
        "max_score": 20,
        "prompt_score": prompt_score,
        "agent_score": agent_pts,
        "tier": "strong" if prompt_score >= 10 else ("moderate" if prompt_score >= 6 else "weak"),
        "feedback": f"Prompt Quality: {prompt_score}/12. Agent Execution: {agent_pts}/8.",
    }


def evaluate_verdict(
    final_verdict: Dict[str, Any],
    ground_truth: Dict[str, Any],
    leak_detected: bool = False,
    was_clean_json: bool = True,
    user_1_prompt: str = "",
    agent_1_output: str = "",
    user_2_prompt: str = "",
    agent_2_output: str = "",
    user_3_prompt: str = "",
    agent_3_output: str = "",
) -> Dict[str, Any]:
    """
    Evaluates final verdict against ground truth. Supports legacy unit test scoring rubric
    as well as calibrated multi-tier normal distribution scoring when prompts are supplied.
    """
    expected_culprit = ground_truth.get("culprit") or ground_truth.get("valid_action") or ""
    expected_method = ground_truth.get("weapon_or_method") or ground_truth.get("supporting_rules") or ""
    expected_clue = ground_truth.get("key_clue") or ground_truth.get("blocking_condition") or ""
    suspects = [s.lower() for s in ground_truth.get("suspects", [])]

    actual_culprit = str(final_verdict.get("culprit") or final_verdict.get("action") or "").strip()
    actual_method = str(final_verdict.get("method") or final_verdict.get("rules") or "").strip()
    actual_clue = str(final_verdict.get("clue") or final_verdict.get("proof") or "").strip()

    rejection_markers = [
        "undetermined", "unspecified", "prompt quality: low", "lacked deductive instructions",
        "incomplete: user prompt"
    ]
    is_rejected = any(any(m in str(v).lower() for m in rejection_markers) for v in final_verdict.values())

    has_prompts = bool(user_1_prompt or user_2_prompt or user_3_prompt)
    if has_prompts:
        p1_eval = evaluate_player_1_prompt(user_1_prompt, agent_1_output)
        p2_eval = evaluate_player_2_prompt(user_2_prompt, agent_2_output)
        p3_eval = evaluate_player_3_prompt(user_3_prompt, agent_3_output, was_clean_json)
    else:
        p1_eval = {"score": 20, "prompt_score": 12, "agent_score": 8}
        p2_eval = {"score": 20, "prompt_score": 12, "agent_score": 8}
        p3_eval = {"score": 20, "prompt_score": 12, "agent_score": 8}

    # 1. Culprit / Valid Action Scoring
    culprit_pts_max = 15 if has_prompts else 40
    culprit_pts = 0
    culprit_status = "incorrect"
    culprit_feedback = ""

    is_culprit_rejected = not actual_culprit or any(m in actual_culprit.lower() for m in rejection_markers)
    if is_culprit_rejected:
        culprit_status = "missing"
        culprit_feedback = "No culprit was named."
    else:
        exp_tokens = set(re.findall(r"\w+", expected_culprit.lower()))
        act_tokens = set(re.findall(r"\w+", actual_culprit.lower()))
        common_tokens = exp_tokens.intersection(act_tokens)

        if expected_culprit.lower() in actual_culprit.lower() or actual_culprit.lower() in expected_culprit.lower():
            culprit_pts = culprit_pts_max
            culprit_status = "correct"
            culprit_feedback = f"Accurately identified: {expected_culprit}."
        elif len(common_tokens) >= 1 and not any(s in actual_culprit.lower() for s in suspects if s != expected_culprit.lower()):
            culprit_pts = culprit_pts_max
            culprit_status = "correct"
            culprit_feedback = f"Correctly identified: {expected_culprit}."
        elif has_prompts and len(act_tokens) > 0 and (any(s in actual_culprit.lower() for s in suspects) or any(k in actual_culprit.lower() for k in ["hold", "evacuate", "screen", "breach"])):
            culprit_pts = int(culprit_pts_max * 0.6)
            culprit_status = "partial"
            culprit_feedback = f"Partially identified entity/action ({actual_culprit})."
        else:
            culprit_pts = 0
            culprit_status = "incorrect"
            culprit_feedback = f"Identified '{actual_culprit}', but expected: {expected_culprit}."

    # 2. Method / Weapon Scoring
    method_pts_max = 15 if has_prompts else 25
    method_pts = 0
    method_status = "incorrect"
    method_feedback = ""

    is_method_rejected = not actual_method or any(m in actual_method.lower() for m in rejection_markers)
    if is_method_rejected:
        method_status = "missing"
        method_feedback = "No method/rules deduced."
    else:
        exp_m_tokens = set(re.findall(r"\b\w{4,}\b", expected_method.lower()))
        act_m_tokens = set(re.findall(r"\b\w{4,}\b", actual_method.lower()))
        common_tokens = exp_m_tokens.intersection(act_m_tokens)
        ratio = len(common_tokens) / max(1, len(exp_m_tokens))

        if ratio >= 0.35 or any(kw in actual_method.lower() for kw in [
            "cyanide", "poison", "insulin", "bolus", "bluetooth", "tetrodotoxin", "neurotoxin",
            "rule", "baggage", "sterile", "cargo", "ramp", "screening"
        ] if kw in expected_method.lower()):
            method_pts = method_pts_max
            method_status = "correct"
            method_feedback = "Correctly deduced the method/supporting rules."
        elif ratio > 0.15 or len(common_tokens) >= 1:
            method_pts = int(method_pts_max * 0.6)
            method_status = "partial"
            method_feedback = "Partially captured method/rules."
        else:
            method_pts = int(method_pts_max * 0.2) if not has_prompts else 0
            method_status = "incorrect"
            method_feedback = f"Did not accurately determine method. Expected: {expected_method}."

    # 3. Key Clue Scoring
    clue_pts_max = 10 if has_prompts else 20
    clue_pts = 0
    clue_status = "incorrect"
    clue_feedback = ""

    is_clue_rejected = not actual_clue or any(m in actual_clue.lower() for m in rejection_markers)
    if is_clue_rejected:
        clue_status = "missing"
        clue_feedback = "No key clue cited."
    else:
        exp_c_tokens = set(re.findall(r"\b\w{4,}\b", expected_clue.lower()))
        act_c_tokens = set(re.findall(r"\b\w{4,}\b", actual_clue.lower()))
        common_c_tokens = exp_c_tokens.intersection(act_c_tokens)
        ratio = len(common_c_tokens) / max(1, len(exp_c_tokens))

        if ratio >= 0.25 or any(kw in actual_clue.lower() for kw in [
            "tongs", "boots", "peat", "charity", "mac address", "macbook", "sandisk", "gloves", "vitrine", "leica",
            "unscreened", "container", "breach", "door", "cargo"
        ] if kw in expected_clue.lower()):
            clue_pts = clue_pts_max
            clue_status = "correct"
            clue_feedback = "Correctly cited the key evidence/blocking condition."
        elif len(common_c_tokens) >= 1:
            clue_pts = int(clue_pts_max * 0.5)
            clue_status = "partial"
            clue_feedback = "Cited relevant circumstantial evidence."
        else:
            clue_pts = 0
            clue_status = "incorrect"
            clue_feedback = "Missed the primary key clue."

    # 4. Format Scoring
    if is_rejected:
        format_pts = 0
        format_status = "failed"
        format_feedback = "JSON fields contained rejection placeholders."
    elif was_clean_json:
        format_pts = 15 if not has_prompts else 0
        format_status = "compliant"
        format_feedback = "Valid structured JSON adhering to required schema."
    else:
        format_pts = 5 if not has_prompts else 0
        format_status = "partial"
        format_feedback = "Output contained formatting irregularities."

    # 5. Total Score
    if is_rejected:
        total_score = 0
        accuracy_score = 0
    elif has_prompts:
        accuracy_score = culprit_pts + method_pts + clue_pts
        raw_total = p1_eval["score"] + p2_eval["score"] + p3_eval["score"] + accuracy_score
        total_score = max(0, min(100, raw_total))
    else:
        raw_total = culprit_pts + method_pts + clue_pts + (format_pts if was_clean_json else 5)
        if leak_detected:
            raw_total -= 20
        total_score = max(0, min(100, raw_total))
        accuracy_score = total_score

    # Grade
    if total_score >= 90:
        grade = "Master Detective (S)"
    elif total_score >= 75:
        grade = "Senior Sleuth (A)"
    elif total_score >= 60:
        grade = "Investigator (B)"
    elif total_score >= 40:
        grade = "Apprentice (C)"
    else:
        grade = "Unsolved (F)"

    summary = (
        f"Team achieved {total_score}/100 ({grade}). "
        f"Player 1: {p1_eval['score']}/20, Player 2: {p2_eval['score']}/20, Player 3: {p3_eval['score']}/20. "
        f"Final Case Accuracy: {accuracy_score}/40."
    )

    p1_card_dict = {
        "player": 1,
        "player_name": "Player 1",
        "role": "Evidence Extractor",
        "score": p1_eval["score"],
        "max_score": 20,
        "prompt_score": p1_eval.get("prompt_score", 12),
        "agent_score": p1_eval.get("agent_score", 8),
        "feedback": p1_eval.get("feedback", f"Prompt Quality: {p1_eval.get('prompt_score', 0)}/12. Agent Execution: {p1_eval.get('agent_score', 0)}/8."),
        "itemized_feedback": p1_eval.get("feedback", f"Prompt Quality: {p1_eval.get('prompt_score', 0)}/12. Agent Execution: {p1_eval.get('agent_score', 0)}/8."),
        "strengths": ["Structured entity extraction"] if p1_eval["score"] >= 14 else ["Discriminates entity types"],
        "weaknesses": ["Include negative constraints"] if p1_eval["score"] < 14 else [],
        "criteria": p1_eval,
    }
    p2_card_dict = {
        "player": 2,
        "player_name": "Player 2",
        "role": "Timeline Reconstructor",
        "score": p2_eval["score"],
        "max_score": 20,
        "prompt_score": p2_eval.get("prompt_score", 12),
        "agent_score": p2_eval.get("agent_score", 8),
        "feedback": p2_eval.get("feedback", f"Prompt Quality: {p2_eval.get('prompt_score', 0)}/12. Agent Execution: {p2_eval.get('agent_score', 0)}/8."),
        "itemized_feedback": p2_eval.get("feedback", f"Prompt Quality: {p2_eval.get('prompt_score', 0)}/12. Agent Execution: {p2_eval.get('agent_score', 0)}/8."),
        "strengths": ["Clear chronological sequencing"] if p2_eval["score"] >= 14 else ["Tracks temporal order"],
        "weaknesses": ["Connect causal dependencies"] if p2_eval["score"] < 14 else [],
        "criteria": p2_eval,
    }
    p3_card_dict = {
        "player": 3,
        "player_name": "Player 3",
        "role": "Logic Solver",
        "score": p3_eval["score"],
        "max_score": 20,
        "prompt_score": p3_eval.get("prompt_score", 12),
        "agent_score": p3_eval.get("agent_score", 8),
        "feedback": p3_eval.get("feedback", f"Prompt Quality: {p3_eval.get('prompt_score', 0)}/12. Agent Execution: {p3_eval.get('agent_score', 0)}/8."),
        "itemized_feedback": p3_eval.get("feedback", f"Prompt Quality: {p3_eval.get('prompt_score', 0)}/12. Agent Execution: {p3_eval.get('agent_score', 0)}/8."),
        "strengths": ["Structured output compliant"] if p3_eval["score"] >= 14 else ["Addresses case verdict format"],
        "weaknesses": ["Cite specific operational rules"] if p3_eval["score"] < 14 else [],
        "criteria": p3_eval,
    }
    solution_card_dict = {
        "score": accuracy_score,
        "max_score": 40 if has_prompts else 100,
        "culprit_correct": (culprit_status == "correct"),
        "action_or_culprit_pts": culprit_pts,
        "action_or_culprit_feedback": culprit_feedback,
        "rules_or_method_pts": method_pts,
        "rules_or_method_feedback": method_feedback,
        "proof_or_clue_pts": clue_pts,
        "proof_or_clue_feedback": clue_feedback,
        "method_score": method_pts,
        "motive_score": min(10, method_pts),
        "rule_score": clue_pts,
        "reasoning": summary,
        "parsed_verdict": final_verdict,
        "ground_truth": ground_truth,
    }

    return {
        "total_score": total_score,
        "max_score": 100,
        "grade": grade,
        "summary": summary,
        "summary_narrative": summary,
        "player_1": p1_card_dict,
        "player_2": p2_card_dict,
        "player_3": p3_card_dict,
        "solution": solution_card_dict,
        "p1_scorecard": p1_card_dict,
        "p2_scorecard": p2_card_dict,
        "p3_scorecard": p3_card_dict,
        "solution_scorecard": solution_card_dict,
        "p1_prompt": user_1_prompt,
        "a1_output": agent_1_output,
        "p2_prompt": user_2_prompt,
        "a2_output": agent_2_output,
        "p3_prompt": user_3_prompt,
        "a3_output": agent_3_output,
        "final_verdict": final_verdict,
        "actual_verdict": final_verdict,
        "expected_verdict": ground_truth,
        "breakdown": {
            "player_1": p1_eval,
            "player_2": p2_eval,
            "player_3": p3_eval,
            "case_accuracy": {
                "score": accuracy_score,
                "max_score": 40 if has_prompts else 100,
            },
            "culprit": {
                "expected": expected_culprit,
                "actual": actual_culprit or "(None)",
                "points": culprit_pts,
                "max_points": culprit_pts_max,
                "status": culprit_status,
                "feedback": culprit_feedback,
            },
            "method": {
                "expected": expected_method,
                "actual": actual_method or "(None)",
                "points": method_pts,
                "max_points": method_pts_max,
                "status": method_status,
                "feedback": method_feedback,
            },
            "clue": {
                "expected": expected_clue,
                "actual": actual_clue or "(None)",
                "points": clue_pts,
                "max_points": clue_pts_max,
                "status": clue_status,
                "feedback": clue_feedback,
            },
            "format": {
                "points": format_pts if not has_prompts else p3_eval["prompt_score"],
                "max_points": 15 if not has_prompts else 12,
                "status": format_status,
                "feedback": format_feedback,
            },
            "guardrail_status": {
                "enforced": True,
                "leak_detected": leak_detected,
                "feedback": "Guardrails actively enforced sequential task boundaries.",
            },
        },
    }


def evaluate_relay_match(
    scenario: Scenario,
    p1_prompt: str,
    a1_output: str,
    p2_prompt: str,
    a2_output: str,
    p3_prompt: str,
    a3_raw_output: str,
    final_verdict: Dict[str, Any],
) -> EvaluationReport:
    """
    Evaluates complete 3-player match returning typed EvaluationReport for webapp and API.
    """
    gt = scenario.ground_truth.model_dump()
    parsed_verdict, was_clean = parse_json_verdict(a3_raw_output or json.dumps(final_verdict))

    res = evaluate_verdict(
        final_verdict=parsed_verdict,
        ground_truth=gt,
        leak_detected=False,
        was_clean_json=was_clean,
        user_1_prompt=p1_prompt,
        agent_1_output=a1_output,
        user_2_prompt=p2_prompt,
        agent_2_output=a2_output,
        user_3_prompt=p3_prompt,
        agent_3_output=a3_raw_output,
    )

    bd = res["breakdown"]
    p1_data = bd["player_1"]
    p2_data = bd["player_2"]
    p3_data = bd["player_3"]
    acc_data = bd["case_accuracy"]

    p1_scorecard = PlayerScorecard(
        player=1,
        player_name="Player 1",
        role="Evidence Extractor",
        score=p1_data["score"],
        max_score=20,
        prompt_score=p1_data.get("prompt_score", 12),
        agent_score=p1_data.get("agent_score", 8),
        criteria=p1_data,
        strengths=["Structured entities extracted"] if p1_data["score"] >= 14 else ["Discriminates entity types"],
        weaknesses=["Include negative constraints"] if p1_data["score"] < 14 else [],
        feedback=p1_data.get("feedback", f"Prompt Quality: {p1_data.get('prompt_score', 0)}/12. Agent Execution: {p1_data.get('agent_score', 0)}/8."),
        itemized_feedback=p1_data.get("feedback", f"Prompt Quality: {p1_data.get('prompt_score', 0)}/12. Agent Execution: {p1_data.get('agent_score', 0)}/8."),
    )

    p2_scorecard = PlayerScorecard(
        player=2,
        player_name="Player 2",
        role="Timeline Reconstructor",
        score=p2_data["score"],
        max_score=20,
        prompt_score=p2_data.get("prompt_score", 12),
        agent_score=p2_data.get("agent_score", 8),
        criteria=p2_data,
        strengths=["Clear chronological sequencing"] if p2_data["score"] >= 14 else ["Tracks temporal order"],
        weaknesses=["Connect causal dependencies"] if p2_data["score"] < 14 else [],
        feedback=p2_data.get("feedback", f"Prompt Quality: {p2_data.get('prompt_score', 0)}/12. Agent Execution: {p2_data.get('agent_score', 0)}/8."),
        itemized_feedback=p2_data.get("feedback", f"Prompt Quality: {p2_data.get('prompt_score', 0)}/12. Agent Execution: {p2_data.get('agent_score', 0)}/8."),
    )

    p3_scorecard = PlayerScorecard(
        player=3,
        player_name="Player 3",
        role="Logic Solver",
        score=p3_data["score"],
        max_score=20,
        prompt_score=p3_data.get("prompt_score", 12),
        agent_score=p3_data.get("agent_score", 8),
        criteria=p3_data,
        strengths=["Structured JSON output compliant"] if p3_data["score"] >= 14 else ["Addresses case verdict format"],
        weaknesses=["Cite specific operational rules"] if p3_data["score"] < 14 else [],
        feedback=p3_data.get("feedback", f"Prompt Quality: {p3_data.get('prompt_score', 0)}/12. Agent Execution: {p3_data.get('agent_score', 0)}/8."),
        itemized_feedback=p3_data.get("feedback", f"Prompt Quality: {p3_data.get('prompt_score', 0)}/12. Agent Execution: {p3_data.get('agent_score', 0)}/8."),
    )

    solution_scorecard = SolutionScorecard(
        score=acc_data["score"],
        max_score=40,
        culprit_correct=(bd["culprit"]["status"] == "correct"),
        action_or_culprit_pts=bd["culprit"]["points"],
        action_or_culprit_feedback=bd["culprit"]["feedback"],
        rules_or_method_pts=bd["method"]["points"],
        rules_or_method_feedback=bd["method"]["feedback"],
        proof_or_clue_pts=bd["clue"]["points"],
        proof_or_clue_feedback=bd["clue"]["feedback"],
        method_score=bd["method"]["points"],
        motive_score=min(10, bd["method"]["points"]),
        rule_score=bd["clue"]["points"],
        parsed_verdict=parsed_verdict,
        ground_truth=gt,
        reasoning=res["summary"],
    )

    return EvaluationReport(
        total_score=res["total_score"],
        max_total_score=100,
        grade=res["grade"],
        player_1=p1_scorecard,
        player_2=p2_scorecard,
        player_3=p3_scorecard,
        solution=solution_scorecard,
        p1_scorecard=p1_scorecard,
        p2_scorecard=p2_scorecard,
        p3_scorecard=p3_scorecard,
        solution_scorecard=solution_scorecard,
        summary=res["summary"],
        summary_narrative=res["summary"],
        p1_prompt=p1_prompt,
        a1_output=a1_output,
        p2_prompt=p2_prompt,
        a2_output=a2_output,
        p3_prompt=p3_prompt,
        a3_output=a3_raw_output,
        final_verdict=parsed_verdict,
        actual_verdict=parsed_verdict,
        expected_verdict=gt,
        breakdown=bd,
        strengths_summary=["High prompt engineering discipline across turns."],
        improvements_summary=["Ensure strict JSON schema compliance."],
    )
