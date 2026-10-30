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


BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[\.\)])\s+")
TIME_RE = re.compile(
    r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?\s*(am|pm)?\b",
    re.IGNORECASE,
)


def parse_first_timestamp(line: str) -> Optional[int]:
    """Parse the first time marker in a string into seconds from midnight."""
    m = TIME_RE.search(line)
    if not m:
        m2 = re.search(r"\b(\d{1,2})\s*(am|pm)\b", line, re.IGNORECASE)
        if m2:
            hr = int(m2.group(1))
            meridiem = m2.group(2).lower()
            if meridiem == "pm" and hr < 12:
                hr += 12
            elif meridiem == "am" and hr == 12:
                hr = 0
            return hr * 3600
        return None
    hr = int(m.group(1))
    mn = int(m.group(2))
    sc = int(m.group(3)) if m.group(3) else 0
    meridiem = (m.group(4) or "").lower()
    if meridiem == "pm" and hr < 12:
        hr += 12
    elif meridiem == "am" and hr == 12:
        hr = 0
    return hr * 3600 + mn * 60 + sc


def is_chronological(items: List[str]) -> bool:
    """Return True if timestamps extracted from items appear in non-decreasing chronological order."""
    times = []
    for it in items:
        t = parse_first_timestamp(it)
        if t is not None:
            times.append(t)
    if len(times) < 2:
        return False
    return all(times[i] <= times[i + 1] for i in range(len(times) - 1))


def reformat_numbered_item(item_text: str, new_idx: int) -> str:
    """Re-index a numbered list item like '3. Check-in' -> '1. Check-in'."""
    m = re.match(r"^(\s*)\d+([\.\)])(\s+)(.*)$", item_text, re.DOTALL)
    if m:
        indent, delim, space, rest = m.groups()
        return f"{indent}{new_idx}{delim}{space}{rest}"
    return item_text


def shuffle_item_list(items: List[str]) -> List[str]:
    """
    Shuffles items by interleaving later and earlier events,
    guaranteeing that timestamps are NOT in chronological order.
    """
    if len(items) <= 1:
        return items
    is_numbered = all(bool(re.match(r"^\s*\d+[\.\)]\s+", it)) for it in items)

    mid = len(items) // 2
    part1 = items[:mid]
    part2 = items[mid:]

    interleaved = []
    for p2, p1 in zip(part2, part1):
        interleaved.append(p2)
        interleaved.append(p1)
    if len(part2) > len(part1):
        interleaved.append(part2[-1])

    if is_chronological(interleaved):
        interleaved.reverse()

    if is_numbered:
        interleaved = [reformat_numbered_item(it, idx) for idx, it in enumerate(interleaved, 1)]

    return interleaved


def shuffle_extracted_events(text: str) -> str:
    """
    Ensures Agent 1 extracted evidence items and timestamps are NOT in chronological order
    by shuffling and interleaving bullet points and events, forcing Agent 2 to reconstruct the timeline.
    """
    if not text or not isinstance(text, str):
        return text

    lines = text.split("\n")
    output_lines: List[str] = []
    current_bullet_block: List[str] = []
    bullet_found = False

    def flush_bullet_block() -> None:
        nonlocal current_bullet_block
        if not current_bullet_block:
            return
        if len(current_bullet_block) >= 2:
            shuffled = shuffle_item_list(current_bullet_block)
            output_lines.extend(shuffled)
        else:
            output_lines.extend(current_bullet_block)
        current_bullet_block = []

    current_item_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        is_bullet = bool(BULLET_RE.match(stripped))
        is_footer = any(stripped.startswith(k) for k in [
            "[EXTRACTION INCOMPLETE", "Filtered Distractions:", "Disregarded Distractions:", "Filtered Noise:"
        ])

        if is_footer:
            if current_item_lines:
                current_bullet_block.append("\n".join(current_item_lines))
                current_item_lines = []
            flush_bullet_block()
            output_lines.append(line)
            continue

        if is_bullet:
            bullet_found = True
            if current_item_lines:
                current_bullet_block.append("\n".join(current_item_lines))
                current_item_lines = []
            current_item_lines.append(line)
        elif current_item_lines:
            if stripped:
                current_item_lines.append(line)
            else:
                current_item_lines.append(line)
        else:
            flush_bullet_block()
            output_lines.append(line)

    if current_item_lines:
        current_bullet_block.append("\n".join(current_item_lines))
    flush_bullet_block()

    if bullet_found:
        return "\n".join(output_lines).strip()

    # Fallback for non-bullet paragraph blocks
    paras = text.split("\n\n")
    para_times = [p for p in paras if parse_first_timestamp(p) is not None]
    if len(para_times) >= 2 and len(paras) >= 2:
        return "\n\n".join(shuffle_item_list(paras)).strip()

    return text.strip()


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
    - Shuffles evidence items and timestamps so they are NOT in chronological order,
      giving Agent 2 meaningful timeline reconstruction work.
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

    sanitized_text = "\n".join(sanitized).strip()
    return shuffle_extracted_events(sanitized_text)


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
