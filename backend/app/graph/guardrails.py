import re
from typing import Any, List, Optional

ACCUSATION_PATTERNS = [
    r"(?i)\b(?:the\s+)?(?:killer|murderer|culprit|perpetrator|thief)\s+(?:is|was|must\s+be)\s+[^.,;\n]+",
    r"(?i)\b[^.,;\n]+\s+(?:is|was|must\s+be)\s+(?:the\s+)?(?:killer|murderer|culprit|thief|guilty\s+of\s+murder|guilty\s+of\s+theft)",
    r"(?i)\b(?:guilty\s+suspect|true\s+culprit|identified\s+killer|identified\s+thief)\s*:\s*[^.,;\n]+",
    r"(?i)\b(?:i\s+conclude|we\s+can\s+conclude|it\s+is\s+clear)\s+that\s+[^.,;\n]+\s+(?:killed|murdered|poisoned|stole)",
    r"(?i)\bconclusion\s*:\s*[^.,;\n]+(?:killed|murdered|guilty|stole)",
]

FINAL_ACTION_PATTERNS = [
    r"(?i)\b(?:final\s+decision|final\s+action|recommended\s+action|verdict)\s*:\s*[^.,;\n]+",
    r"(?i)\b(?:hold\s+flight|ground\s+flight|cancel\s+flight|arrest\s+suspect)\b[^.,;\n]*",
]

JSON_BLOCK_PATTERN = r"```(?:json)?\s*\{.*?\}\s*```|\{[^{}]*(?:\"culprit\"|\"action\"|\"valid_action\")[^{}]*\}"


def strip_premature_json(text: str) -> str:
    """Removes premature JSON schema blocks intended exclusively for Agent 3."""
    cleaned = re.sub(JSON_BLOCK_PATTERN, "", text, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def sanitize_extractor_output(
    text: str,
    spoilers: Optional[List[str]] = None,
) -> str:
    """
    Guardrail for Agent 1 (Evidence Extractor).
    - Removes premature JSON verdict structures.
    - Strips direct accusations or premature operational decisions.
    - Preserves factual evidence observations and timestamps.
    """
    if not text:
        return text

    cleaned = strip_premature_json(text)
    lines = cleaned.split("\n")
    sanitized = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sanitized.append("")
            continue

        # Check for premature accusation
        for pat in ACCUSATION_PATTERNS:
            if re.search(pat, stripped):
                line = re.sub(pat, "[Accusation omitted: Reserved for Step 3]", line)

        # Check for spoilers
        if spoilers:
            for sp in spoilers:
                if len(sp) > 3 and sp.lower() in line.lower():
                    # Only neutralize if used as a definitive conclusion
                    if any(w in line.lower() for w in ["killed", "murdered", "verdict", "guilty", "action"]):
                        line = re.sub(rf"(?i)\b{re.escape(sp)}\b", "[Entity]", line)

        sanitized.append(line)

    return "\n".join(sanitized).strip()


def sanitize_reconstructor_output(
    text: str,
    spoilers: Optional[List[str]] = None,
    **kwargs: Any,
) -> str:
    """
    Guardrail for Agent 2 (Timeline Reconstructor).
    - Preserves chronological sequences and dependencies.
    - Neutralizes premature verdicts, accusations, or final flight dispatch orders.
    - Removes premature JSON structures.
    """
    if not text:
        return text

    all_spoilers = list(spoilers or [])
    if "additional_keywords" in kwargs and kwargs["additional_keywords"]:
        all_spoilers.extend(kwargs["additional_keywords"])
    if "culprit" in kwargs and kwargs["culprit"]:
        all_spoilers.append(kwargs["culprit"])
    if "suspects" in kwargs and kwargs["suspects"]:
        pass

    cleaned = strip_premature_json(text)
    lines = cleaned.split("\n")
    sanitized = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sanitized.append("")
            continue

        for pat in ACCUSATION_PATTERNS:
            if re.search(pat, stripped):
                line = re.sub(pat, "[Observation recorded neutrally]", line)

        for pat in FINAL_ACTION_PATTERNS:
            if re.search(pat, stripped):
                line = re.sub(pat, "[Chronological sequence noted without final resolution]", line)

        for sp in all_spoilers:
            if sp and len(sp) > 3 and sp.lower() in line.lower():
                if any(w in line.lower() for w in ["killed", "poisoned", "murdered", "verdict", "guilty", "ground", "arrest", "killer", "stole", "theft"]):
                    line = re.sub(rf"(?i)\b{re.escape(sp)}\b", "[Entity]", line)

        sanitized.append(line)

    return "\n".join(sanitized).strip()
