import json
import re
from typing import Any, Dict, List, Optional, Tuple


def parse_json_verdict(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Robustly extract the JSON verdict from LLM output.
    Returns:
        (parsed_dict, was_clean_json_bool)
    """
    if not raw_text or not isinstance(raw_text, str):
        return {"culprit": "", "method": "", "clue": ""}, False

    cleaned = raw_text.strip()
    was_clean = False

    # Attempt 1: Direct JSON parsing
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data, True
    except Exception:
        pass

    # Attempt 2: Strip markdown code blocks (```json ... ```)
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        try:
            data = json.loads(code_block_match.group(1).strip())
            if isinstance(data, dict):
                return data, True
        except Exception:
            pass

    # Attempt 3: Find any substring enclosed in braces { ... }
    brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if brace_match:
        try:
            data = json.loads(brace_match.group(1).strip())
            if isinstance(data, dict):
                return data, False
        except Exception:
            pass

    # Attempt 4: Fallback heuristic regex extraction for fields
    result: Dict[str, Any] = {"culprit": "", "method": "", "clue": ""}
    culprit_match = re.search(r"['\"]?culprit['\"]?\s*:\s*['\"]([^'\"]+)['\"]", cleaned, re.IGNORECASE)
    method_match = re.search(r"['\"]?method['\"]?\s*:\s*['\"]([^'\"]+)['\"]", cleaned, re.IGNORECASE)
    clue_match = re.search(r"['\"]?clue['\"]?\s*:\s*['\"]([^'\"]+)['\"]", cleaned, re.IGNORECASE)

    if culprit_match:
        result["culprit"] = culprit_match.group(1).strip()
    if method_match:
        result["method"] = method_match.group(1).strip()
    if clue_match:
        result["clue"] = clue_match.group(1).strip()

    return result, False


def evaluate_verdict(
    final_verdict: Dict[str, Any],
    ground_truth: Dict[str, Any],
    leak_detected: bool = False,
    was_clean_json: bool = True,
) -> Dict[str, Any]:
    """
    Analytical evaluation engine comparing pipeline verdict against expected ground truth.
    Scoring Rubric (100 Max):
      - Culprit Identification: 40 pts
      - Method / Weapon:        25 pts
      - Key Clue:               20 pts
      - Format Compliance:      15 pts
      - Premature Leak Penalty: -20 pts
    """
    expected_culprit = str(ground_truth.get("culprit", "")).strip()
    expected_method = str(ground_truth.get("weapon_or_method", "")).strip()
    expected_clue = str(ground_truth.get("key_clue", "")).strip()
    suspects = [s.lower() for s in ground_truth.get("suspects", [])]

    actual_culprit = str(final_verdict.get("culprit", "")).strip()
    actual_method = str(final_verdict.get("method", "")).strip()
    actual_clue = str(final_verdict.get("clue", "")).strip()

    # 1. Culprit Scoring (Max 40)
    culprit_pts = 0
    culprit_status = "incorrect"
    culprit_feedback = ""

    if not actual_culprit:
        culprit_feedback = "No culprit was named."
        culprit_status = "missing"
    else:
        # Check direct or token overlap with expected culprit
        exp_tokens = set(re.findall(r"\w+", expected_culprit.lower()))
        act_tokens = set(re.findall(r"\w+", actual_culprit.lower()))
        
        # Exact or surname/forename match
        if expected_culprit.lower() in actual_culprit.lower() or actual_culprit.lower() in expected_culprit.lower():
            culprit_pts = 40
            culprit_status = "correct"
            culprit_feedback = f"Accurately identified the true culprit: {expected_culprit}."
        elif len(exp_tokens.intersection(act_tokens)) >= 1 and not any(
            s in actual_culprit.lower() for s in suspects if s != expected_culprit.lower()
        ):
            # Matched surname or distinctive token without naming a wrong suspect
            culprit_pts = 40
            culprit_status = "correct"
            culprit_feedback = f"Correctly identified {expected_culprit}."
        else:
            culprit_pts = 0
            culprit_status = "incorrect"
            culprit_feedback = f"Identified '{actual_culprit}', but the true culprit was {expected_culprit}."

    # 2. Method / Weapon Scoring (Max 25)
    method_pts = 0
    method_status = "incorrect"
    method_feedback = ""

    if not actual_method:
        method_status = "missing"
        method_feedback = "No murder method was specified."
    else:
        # Key concept keyword overlap
        exp_m_tokens = set(re.findall(r"\b\w{4,}\b", expected_method.lower()))
        act_m_tokens = set(re.findall(r"\b\w{4,}\b", actual_method.lower()))
        common_tokens = exp_m_tokens.intersection(act_m_tokens)

        ratio = len(common_tokens) / max(1, len(exp_m_tokens))
        if ratio >= 0.35 or any(kw in actual_method.lower() for kw in [
            "cyanide", "poison", "insulin", "bolus", "bluetooth", "tetrodotoxin", "neurotoxin"
        ] if kw in expected_method.lower()):
            method_pts = 25
            method_status = "correct"
            method_feedback = "Correctly deduced the murder weapon/method."
        elif ratio > 0.15 or len(common_tokens) >= 1:
            method_pts = 15
            method_status = "partial"
            method_feedback = "Partially captured the method, but lacked key specific details."
        else:
            method_pts = 5
            method_status = "incorrect"
            method_feedback = f"Did not accurately determine the method. Expected: {expected_method}."

    # 3. Key Clue Scoring (Max 20)
    clue_pts = 0
    clue_status = "incorrect"
    clue_feedback = ""

    if not actual_clue:
        clue_status = "missing"
        clue_feedback = "No key clue was cited."
    else:
        exp_c_tokens = set(re.findall(r"\b\w{4,}\b", expected_clue.lower()))
        act_c_tokens = set(re.findall(r"\b\w{4,}\b", actual_clue.lower()))
        common_c_tokens = exp_c_tokens.intersection(act_c_tokens)

        ratio = len(common_c_tokens) / max(1, len(exp_c_tokens))
        if ratio >= 0.25 or any(kw in actual_clue.lower() for kw in [
            "tongs", "boots", "peat", "charity", "mac address", "macbook", "sandisk", "gloves", "vitrine", "leica"
        ] if kw in expected_clue.lower()):
            clue_pts = 20
            clue_status = "correct"
            clue_feedback = "Correctly cited the definitive smoking gun clue."
        elif len(common_c_tokens) >= 1:
            clue_pts = 10
            clue_status = "partial"
            clue_feedback = "Cited relevant circumstantial evidence, but missed the decisive clue."
        else:
            clue_pts = 0
            clue_status = "incorrect"
            clue_feedback = "Missed the primary smoking gun clue."

    # 4. Format & Schema Compliance (Max 15)
    format_pts = 0
    format_status = "failed"
    format_feedback = ""

    has_all_keys = all(k in final_verdict and bool(final_verdict[k]) for k in ("culprit", "method", "clue"))
    if was_clean_json and has_all_keys:
        format_pts = 15
        format_status = "compliant"
        format_feedback = "Perfect JSON formatting adhering to required schema."
    elif has_all_keys:
        format_pts = 10
        format_status = "partial"
        format_feedback = "Extracted valid keys, but output contained formatting irregularities or code fences."
    elif any(k in final_verdict and bool(final_verdict[k]) for k in ("culprit", "method", "clue")):
        format_pts = 5
        format_status = "partial"
        format_feedback = "Incomplete schema: some required fields were missing."
    else:
        format_pts = 0
        format_status = "failed"
        format_feedback = "Failed to output compliant JSON."

    # 5. Premature Leak Penalty (-20)
    leak_penalty_applied = False
    leak_penalty_pts = 0
    leak_feedback = "No premature leak detected. The pipeline respected sequential discovery."

    if leak_detected:
        leak_penalty_applied = True
        leak_penalty_pts = 20
        leak_feedback = "Penalty (-20 pts): Player 2's timeline prematurely leaked the culprit."

    # Calculate Total Score
    raw_total = culprit_pts + method_pts + clue_pts + format_pts - leak_penalty_pts
    total_score = max(0, min(100, raw_total))

    # Determine Grade
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
        f"Culprit was {culprit_status} ({culprit_pts}/40), "
        f"Method was {method_status} ({method_pts}/25), "
        f"and Key Clue was {clue_status} ({clue_pts}/20)."
    )
    if leak_penalty_applied:
        summary += " A 20-point penalty was deducted for premature leak in Step 2."

    return {
        "total_score": total_score,
        "max_score": 100,
        "grade": grade,
        "summary": summary,
        "breakdown": {
            "culprit": {
                "expected": expected_culprit,
                "actual": actual_culprit or "(None)",
                "points": culprit_pts,
                "max_points": 40,
                "status": culprit_status,
                "feedback": culprit_feedback,
            },
            "method": {
                "expected": expected_method,
                "actual": actual_method or "(None)",
                "points": method_pts,
                "max_points": 25,
                "status": method_status,
                "feedback": method_feedback,
            },
            "clue": {
                "expected": expected_clue,
                "actual": actual_clue or "(None)",
                "points": clue_pts,
                "max_points": 20,
                "status": clue_status,
                "feedback": clue_feedback,
            },
            "format": {
                "points": format_pts,
                "max_points": 15,
                "status": format_status,
                "feedback": format_feedback,
            },
            "leak_penalty": {
                "applied": leak_penalty_applied,
                "penalty": leak_penalty_pts,
                "feedback": leak_feedback,
            },
        },
    }
