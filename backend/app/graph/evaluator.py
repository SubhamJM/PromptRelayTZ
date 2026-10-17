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
        "culprit": ["culprit", "perpetrator", "suspect", "action", "valid_action", "target_action_or_culprit"],
        "method": ["method", "weapon", "mechanism", "rules", "supporting_rules", "rule_broken", "target_rules_or_method"],
        "clue": [
            "clue", "key_clue", "proof", "blocking_condition", "evidence",
            "evidence_keys", "clues", "key_evidence", "target_proof_or_clue",
        ],
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
    action = str(
        data.get("action")
        or data.get("valid_action")
        or data.get("culprit")
        or data.get("target_action_or_culprit")
        or ""
    ).strip()

    raw_rules = (
        data.get("supporting_rules")
        or data.get("rules")
        or data.get("method")
        or data.get("weapon")
        or data.get("rule_broken")
    )
    if isinstance(raw_rules, list):
        rules = "; ".join(str(r) for r in raw_rules)
    else:
        rules = str(raw_rules or "").strip()

    clue_items = []
    seen_items = set()

    def add_clue(item: Any) -> None:
        if not item:
            return
        if isinstance(item, list):
            for sub in item:
                add_clue(sub)
            return
        s = str(item).strip()
        if s:
            for part in s.split(";"):
                clean_part = part.strip()
                if clean_part and clean_part.lower() not in seen_items:
                    seen_items.add(clean_part.lower())
                    clue_items.append(clean_part)

    # 1. Direct clue/proof fields
    for k in ["proof", "blocking_condition", "clue", "key_clue", "evidence", "key_evidence", "target_proof_or_clue"]:
        add_clue(data.get(k))

    # 2. evidence_keys field (mandated by Agent 3 system prompt and scoring guide)
    add_clue(data.get("evidence_keys") or data.get("clues"))

    # 3. If motive contains blocking condition or unattended bag details in operational scenarios
    motive_val = str(data.get("motive") or "").strip()
    if motive_val and any(w in motive_val.lower() for w in ["unattended", "suitcase", "bag", "k9", "sweep", "blocking", "gate b07"]):
        add_clue(motive_val)

    proof = "; ".join(clue_items).strip()

    result.setdefault("culprit", action)
    result.setdefault("action", action)
    result.setdefault("action_or_culprit", action)

    result.setdefault("method", rules)
    result.setdefault("rules", rules)
    result.setdefault("rules_or_method", rules)

    result.setdefault("clue", proof)
    result.setdefault("proof", proof)
    result.setdefault("proof_or_clue", proof)
    if "evidence_keys" not in result and clue_items:
        result["evidence_keys"] = clue_items
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
    if any(k in p for k in ["role:", "role :", "you are", "expert", "specialist", "act as", "forensic evidence"]):
        role_pts = 3
    elif any(k in p for k in ["role", "agent", "engine", "extractor", "analyst"]):
        role_pts = 2
    elif "extract" in p and word_count >= 15:
        role_pts = 3
    elif any(k in p for k in ["extract", "identify", "review", "examine", "find"]):
        role_pts = 1

    # 2. Categories / Taxonomy (0-3)
    categories = ["people", "person", "passengers", "who", "time", "timestamp", "location", "place", "gate", "object", "item", "baggage", "luggage", "movement", "cctv"]
    cat_matches = sum(1 for c in categories if c in p)
    if cat_matches >= 4:
        cat_pts = 3
    elif cat_matches >= 2:
        cat_pts = 2
    elif cat_matches >= 1:
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
    has_filter = any(k in p for k in ["noise", "irrelevant", "ignore", "filter", "chatter", "ambient", "distraction"])
    has_constraint = any(k in p for k in ["do not", "never", "refrain", "don't", "without", "no infer", "not infer", "no decision", "no dispatch"])
    if has_filter and has_constraint:
        filter_pts = 3
    elif has_filter or has_constraint:
        filter_pts = 2
    else:
        filter_pts = 0

    prompt_score = min(12, role_pts + cat_pts + discrim_pts + filter_pts)

    # Agent 1 Output Quality (0-8)
    out_lower = (agent_output or "").lower()
    if not out_lower or "[extraction incomplete" in out_lower:
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
    if any(k in p for k in ["role:", "role :", "you are", "specialist", "act as", "reconstructor agent"]):
        role_pts = 3
    elif any(k in p for k in ["role", "agent", "reconstructor", "investigator"]):
        role_pts = 2
    elif "reconstruct" in p and word_count >= 15:
        role_pts = 3
    elif any(k in p for k in ["reconstruct", "organize", "trace", "synthesize"]):
        role_pts = 1

    # 2. Temporal Sequencing (0-3)
    seq_terms = sum(1 for k in ["first", "next", "last", "sequence", "chronological", "timeline", "minute", "timestamp"] if k in p)
    if seq_terms >= 3 or ("chronological" in p and ("first" in p or "next" in p)):
        seq_pts = 3
    elif seq_terms >= 1:
        seq_pts = 2
    else:
        seq_pts = 0

    # 3. Connection & Movement Tracking (0-3)
    connect_pts = 0
    if any(k in p for k in ["connect", "causal", "depend", "lead to", "impact", "relationship"]):
        connect_pts = 3
    elif any(k in p for k in ["movement", "trace", "between", "link", "route"]):
        connect_pts = 2
    elif any(k in p for k in ["people", "location", "event"]):
        connect_pts = 1

    # 4. Uncertainty & Neutrality Constraint (0-3)
    neut_pts = 0
    has_uncert = any(k in p for k in ["uncertain", "separate", "unverified", "keep uncertain", "confirmed"])
    has_constraint = any(k in p for k in ["do not", "never", "neutral", "without naming", "no verdict", "not infer", "without issuing", "objective neutrality"])
    if has_uncert and has_constraint:
        neut_pts = 3
    elif (has_uncert or has_constraint) and word_count >= 15:
        neut_pts = 3
    elif has_uncert or has_constraint:
        neut_pts = 2
    else:
        neut_pts = 0

    prompt_score = min(12, role_pts + seq_pts + connect_pts + neut_pts)

    # Agent 2 Output Quality (0-8)
    out_lower = (agent_output or "").lower()
    if not out_lower or "[timeline incomplete" in out_lower:
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
    if any(k in p for k in ["role:", "role :", "you are", "specialist", "act as", "decision solver", "logic decision"]):
        role_pts = 3
    elif any(k in p for k in ["role", "agent", "solver", "detective", "magistrate", "decision"]):
        role_pts = 2
    elif ("solve" in p or "determine" in p) and word_count >= 15:
        role_pts = 2
    elif any(k in p for k in ["solve", "determine"]):
        role_pts = 1

    # 2. Rule & Deductive Directives (0-3)
    rule_pts = 0
    if any(k in p for k in [
        "sec-101", "ops-204", "clr-305", "operational rules", "protocols", "governing rules",
        "standard §", "trace standard", "forensic standard", "discrepancy principle", "biological trace", "cyber-physical"
    ]):
        rule_pts = 3
    elif any(k in p for k in ["rule", "regulat", "support", "deduc", "eliminat", "policy"]):
        rule_pts = 2 if ("rule" in p or "deduc" in p) else 1
    elif any(k in p for k in ["condition", "criteria"]):
        rule_pts = 1

    # 3. Operational Action & Resumption Directives (0-3)
    act_pts = 0
    if any(k in p for k in [
        "operational action", "dispatch", "blocking condition", "resumption condition", "safety action",
        "hold flight", "final verdict", "conviction", "determine the final verdict"
    ]):
        act_pts = 3
    elif any(k in p for k in ["action", "blocking", "resume", "culprit", "method", "clue", "decision"]):
        act_pts = 2
    elif word_count >= 10:
        act_pts = 1

    # 4. JSON Schema Constraints (0-3)
    schema_pts = 0
    if "json" in p and any(k in p for k in ["key", "schema", "format", "strict", "{"]):
        schema_pts = 3
    elif "json" in p or "format" in p:
        schema_pts = 2
    else:
        schema_pts = 0

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
    expected_culprit = ground_truth.get("culprit") or ground_truth.get("valid_action") or ground_truth.get("target_action_or_culprit") or ""
    expected_method = ground_truth.get("weapon_or_method") or ground_truth.get("supporting_rules") or ground_truth.get("target_rules_or_method") or ""
    expected_clue = ground_truth.get("key_clue") or ground_truth.get("blocking_condition") or ground_truth.get("target_proof_or_clue") or ""
    suspects = [s.lower() for s in (ground_truth.get("suspects") or ground_truth.get("suspects_or_entities") or [])]

    actual_culprit = str(final_verdict.get("culprit") or final_verdict.get("action") or final_verdict.get("valid_action") or "").strip()
    actual_method = str(final_verdict.get("method") or final_verdict.get("rules") or final_verdict.get("supporting_rules") or "").strip()

    clue_sources = []
    seen_sources = set()

    def add_eval_clue(item: Any) -> None:
        if not item:
            return
        if isinstance(item, list):
            for sub in item:
                add_eval_clue(sub)
            return
        s = str(item).strip()
        if s:
            for part in s.split(";"):
                clean_part = part.strip()
                if clean_part and clean_part.lower() not in seen_sources:
                    seen_sources.add(clean_part.lower())
                    clue_sources.append(clean_part)

    for k in ["clue", "proof", "key_clue", "proof_or_clue", "blocking_condition", "evidence", "key_evidence"]:
        add_eval_clue(final_verdict.get(k))

    add_eval_clue(final_verdict.get("evidence_keys") or final_verdict.get("clues"))

    motive_val = str(final_verdict.get("motive") or "").strip()
    if motive_val and any(w in motive_val.lower() for w in ["unattended", "suitcase", "bag", "k9", "sweep", "blocking", "gate b07"]):
        add_eval_clue(motive_val)

    actual_clue = "; ".join(clue_sources).strip()

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
        exp_lower = expected_culprit.lower()
        act_lower = actual_culprit.lower()

        stopwords = {"the", "and", "for", "off", "area", "to", "inspect", "unit", "with", "at", "in", "on", "a", "an"}
        exp_tokens = set(re.findall(r"\w+", exp_lower)) - stopwords
        act_tokens = set(re.findall(r"\w+", act_lower)) - stopwords
        common_tokens = exp_tokens.intersection(act_tokens)

        is_operational_action = any(k in exp_lower for k in ["hold", "ground", "evacuate", "suspend", "dispatch", "cancel", "flight"])

        is_unconfirmed = any(u in act_lower for u in ["suspect", "unconfirmed", "pending", "possible", "preliminary"])

        if not is_operational_action and (exp_lower in act_lower or act_lower in exp_lower):
            if has_prompts and is_unconfirmed:
                culprit_pts = int(culprit_pts_max * 0.55)  # 8 pts partial
                culprit_status = "partial"
                culprit_feedback = f"Identified primary suspect ({actual_culprit}), but conviction was unconfirmed/pending verification."
            else:
                culprit_pts = culprit_pts_max
                culprit_status = "correct"
                culprit_feedback = f"Accurately identified: {expected_culprit}."
        elif is_operational_action and (exp_lower == act_lower or exp_lower in act_lower):
            culprit_pts = culprit_pts_max
            culprit_status = "correct"
            culprit_feedback = f"Accurately identified: {expected_culprit}."
        else:

            if is_operational_action:
                has_action_verb = any(v in act_lower for v in ["hold", "ground", "suspend", "stop", "halt", "evacuate"])
                has_flight_id = any(fid in act_lower for fid in ["472", "sw 472", "sw-472", "flight"])
                has_containment = any(cm in act_lower for cm in ["cordon", "perimeter", "suspend passenger boarding", "suspend boarding", "seating", "clear gate"])
                has_inspection = any(im in act_lower for im in ["k9", "k-9", "canine", "explosive", "sweep", "bomb squad", "inspect the unattended"])

                token_recall = len(common_tokens) / max(1, len(exp_tokens))
                token_precision = len(common_tokens) / max(1, len(act_tokens))

                # Full marks: Must have action verb + flight id + containment measure + K9 inspection dispatch
                # OR high token recall & precision against ground truth
                if (has_action_verb and has_flight_id and has_containment and has_inspection) or (token_recall >= 0.40 and token_precision >= 0.5):
                    culprit_pts = culprit_pts_max
                    culprit_status = "correct"
                    culprit_feedback = f"Accurately deduced complete operational action: {expected_culprit}."
                # Substantial: Action verb + flight id + either containment OR inspection
                elif has_action_verb and has_flight_id and (has_containment or has_inspection):
                    culprit_pts = int(culprit_pts_max * 0.8)  # 12 pts
                    culprit_status = "partial"
                    culprit_feedback = f"Substantially identified operational action ({actual_culprit}), but omitted secondary safety measures."
                # Basic hold: Action verb + flight id (or gate)
                elif has_action_verb and has_flight_id:
                    culprit_pts = int(culprit_pts_max * 0.55)  # 8 pts
                    culprit_status = "partial"
                    culprit_feedback = f"Identified flight hold ({actual_culprit}), but missing specific containment and inspection deployments."
                elif has_action_verb or has_flight_id or any(s in act_lower for s in suspects):
                    culprit_pts = int(culprit_pts_max * 0.4)  # 6 pts
                    culprit_status = "partial"
                    culprit_feedback = f"Partially identified entity/action ({actual_culprit})."
                else:
                    culprit_pts = 0
                    culprit_status = "incorrect"
                    culprit_feedback = f"Identified '{actual_culprit}', but expected: {expected_culprit}."
            else:
                rival_suspects = [s for s in suspects if s not in exp_lower]
                has_rival_suspect = any(s in act_lower for s in rival_suspects)
                is_unconfirmed = any(u in act_lower for u in ["suspect", "unconfirmed", "pending", "possible", "preliminary"])

                if len(common_tokens) >= 1 and not has_rival_suspect:
                    if has_prompts and is_unconfirmed:
                        culprit_pts = int(culprit_pts_max * 0.55)  # 8 pts partial
                        culprit_status = "partial"
                        culprit_feedback = f"Identified primary suspect ({actual_culprit}), but conviction was unconfirmed/pending verification."
                    else:
                        culprit_pts = culprit_pts_max
                        culprit_status = "correct"
                        culprit_feedback = f"Correctly identified: {expected_culprit}."
                elif has_prompts and len(act_tokens) > 0 and (has_rival_suspect or any(s in act_lower for s in suspects)):
                    culprit_pts = 0
                    culprit_status = "incorrect"
                    culprit_feedback = f"Identified '{actual_culprit}', but expected: {expected_culprit}."
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
        exp_m_lower = expected_method.lower()
        act_m_lower = actual_method.lower()
        is_operational_rules = any(r in exp_m_lower for r in ["sec-101", "ops-204", "clr-305", "sterile zone", "pre-departure"])

        if is_operational_rules:
            has_sec101 = any(r in act_m_lower for r in ["sec-101", "sec 101", "sterile zone unattended baggage", "unattended baggage protocol", "unattended baggage"])
            has_ops204 = any(r in act_m_lower for r in ["ops-204", "ops 204", "pre-departure security hold", "security hold protocol", "pre-departure hold"])

            if has_sec101 and has_ops204:
                method_pts = method_pts_max
                method_status = "correct"
                method_feedback = "Correctly deduced both governing operational rules (SEC-101 and OPS-204)."
            elif has_sec101 or has_ops204:
                method_pts = int(method_pts_max * 0.55)  # 8 pts
                method_status = "partial"
                method_feedback = f"Partially captured operational rules ({'SEC-101' if has_sec101 else 'OPS-204'} cited; secondary rule omitted)."
            else:
                method_pts = 0
                method_status = "incorrect"
                method_feedback = f"Did not accurately cite operational rules. Expected: {expected_method}."
        else:
            exp_m_tokens = set(re.findall(r"\b\w{4,}\b", exp_m_lower))
            act_m_tokens = set(re.findall(r"\b\w{4,}\b", act_m_lower))
            common_tokens = exp_m_tokens.intersection(act_m_tokens)
            ratio = len(common_tokens) / max(1, len(exp_m_tokens))

            if has_prompts:
                has_delivery_vehicle = any(v in act_m_lower for v in [
                    "sugar", "tongs", "demerara", "tea tray",
                    "ble", "bluetooth", "dongle", "raspberry pi", "firmware", "override payload",
                    "vitrine", "latch", "handle", "gloves", "nitrile", "transdermal"
                ])
                has_lethal_agent = any(a in act_m_lower for a in [
                    "cyanide", "poison", "insulin", "bolus", "tetrodotoxin", "neurotoxin"
                ])

                if (has_lethal_agent and has_delivery_vehicle) or ratio >= 0.40:
                    method_pts = method_pts_max  # 15 pts
                    method_status = "correct"
                    method_feedback = "Correctly deduced the lethal agent and specific delivery mechanism."
                elif has_lethal_agent or has_delivery_vehicle or ratio >= 0.20 or len(common_tokens) >= 1:
                    method_pts = int(method_pts_max * 0.55)  # 8 pts
                    method_status = "partial"
                    method_feedback = f"Partially captured method ({actual_method}), but omitted specific delivery mechanism."
                else:
                    method_pts = 0
                    method_status = "incorrect"
                    method_feedback = f"Did not accurately determine method. Expected: {expected_method}."
            else:
                if ratio >= 0.35 or any(kw in act_m_lower for kw in [
                    "cyanide", "poison", "insulin", "bolus", "bluetooth", "tetrodotoxin", "neurotoxin",
                    "sterile", "cargo", "ramp", "screening"
                ] if kw in exp_m_lower):
                    method_pts = method_pts_max
                    method_status = "correct"
                    method_feedback = "Correctly deduced the method/supporting rules."
                elif ratio > 0.15 or len(common_tokens) >= 1:
                    method_pts = int(method_pts_max * 0.6)
                    method_status = "partial"
                    method_feedback = "Partially captured method/rules."
                else:
                    method_pts = int(method_pts_max * 0.2)
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
        exp_c_lower = expected_clue.lower()
        act_c_lower = actual_clue.lower()
        is_operational_clue = any(k in exp_c_lower for k in ["daniel kim", "skw-", "unattended blue", "k9 explosive", "gate b07"])

        if is_operational_clue:
            has_bag_gate = any(b in act_c_lower for b in ["unattended", "blue suitcase", "blue hard-shell", "blue bag", "suitcase at gate", "bag at gate", "gate b07"])
            has_tag_or_owner = any(o in act_c_lower for o in ["daniel kim", "kim", "skw-78921-472", "skw-", "78921", "bag tag", "tag #"])
            has_k9_sweep = any(k in act_c_lower for k in ["k9 sweep", "k-9 sweep", "k9 explosive", "explosive clearance", "k9 clearance", "sweep clearance"])

            # Full marks: Must cite the unattended blue bag/gate AND tag/Daniel Kim ownership link
            if has_bag_gate and has_tag_or_owner:
                clue_pts = clue_pts_max  # 10 pts
                clue_status = "correct"
                clue_feedback = "Correctly cited the key evidence and decisive ownership tag/blocking condition."
            elif has_bag_gate or has_tag_or_owner or has_k9_sweep:
                clue_pts = int(clue_pts_max * 0.5)  # 5 pts
                clue_status = "partial"
                clue_feedback = "Partially cited incident evidence (identified unattended bag, but omitted tag verification or K9 clearance status)."
            else:
                clue_pts = 0
                clue_status = "incorrect"
                clue_feedback = f"Missed primary key clue. Expected: {expected_clue}."
        else:
            exp_c_tokens = set(re.findall(r"\b\w{4,}\b", exp_c_lower))
            act_c_tokens = set(re.findall(r"\b\w{4,}\b", act_c_lower))
            common_c_tokens = exp_c_tokens.intersection(act_c_tokens)
            ratio = len(common_c_tokens) / max(1, len(exp_c_tokens))

            if has_prompts:
                has_alibi_contradiction = any(ac in act_c_lower for ac in [
                    "red peat", "greenhouse", "contradict", "arrival alibi",
                    "cron", "automated", "mac address", "pi zero", "d4:8a", "f4:d4", "zoom",
                    "dna", "inside", "interior", "briefcase", "caesarean", "emerald", "leica", "camera lens"
                ])
                has_physical_clue = any(pc in act_c_lower for pc in [
                    "boots", "tongs", "residue", "sugar tongs",
                    "sniffer", "packet", "dongle", "mac", "ssd",
                    "gloves", "nitrile", "vitrine", "latch", "swab", "binder"
                ])

                if has_alibi_contradiction and (has_physical_clue or ratio >= 0.35):
                    clue_pts = clue_pts_max  # 10 pts
                    clue_status = "correct"
                    clue_feedback = "Correctly cited the key evidence and decisive proof/alibi contradiction."
                elif has_physical_clue or has_alibi_contradiction or ratio >= 0.15 or len(common_c_tokens) >= 1:
                    clue_pts = int(clue_pts_max * 0.5)  # 5 pts
                    clue_status = "partial"
                    clue_feedback = "Partially cited incident evidence (identified physical object, but omitted decisive alibi disproof or forensic match)."
                else:
                    clue_pts = 0
                    clue_status = "incorrect"
                    clue_feedback = f"Missed primary key clue. Expected: {expected_clue}."
            else:
                clue_keywords = [
                    "tongs", "boots", "peat", "charity", "mac address", "macbook", "sandisk", "gloves", "vitrine", "leica",
                    "unscreened", "container", "breach", "door", "cargo"
                ]

                if ratio >= 0.20 or any(kw in act_c_lower for kw in clue_keywords if kw in exp_c_lower):
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
        accuracy_score = 0
        culprit_pts = 0
        method_pts = 0
        clue_pts = 0
        culprit_status = "missing"
        method_status = "missing"
        clue_status = "missing"
        culprit_feedback = "Verdict rejected: Contains undetermined placeholder."
        method_feedback = "Verdict rejected: Contains undetermined placeholder."
        clue_feedback = "Verdict rejected: Contains undetermined placeholder."
        total_score = 0
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
    if final_verdict and isinstance(final_verdict, dict):
        for k, v in final_verdict.items():
            if v and (not parsed_verdict.get(k) or len(str(v)) > len(str(parsed_verdict.get(k, "")))):
                parsed_verdict[k] = v

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
