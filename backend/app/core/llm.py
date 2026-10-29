import json
import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel, SimpleChatModel
from langchain_core.messages import BaseMessage

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def classify_prompt_tier(prompt_text: str, agent_role: str) -> str:
    """Return tier string ('weak', 'moderate', 'strong') for prompt."""
    return classify_prompt_quality(prompt_text, agent_role)["tier"]


def classify_prompt_quality(prompt_text: str, agent_role: str) -> Dict[str, Any]:
    """
    Evaluates the quality of a user's prompt engineering instruction (Max 12 pts).
    - Role & Persona directive (0-3 pts)
    - Specific Taxonomies / Scopes (0-3 pts)
    - Discrimination / Ordering directives (0-3 pts)
    - Filtering & Negative Constraints (0-3 pts)
    Returns:
        dict with {tier: 'weak'|'moderate'|'strong', score: int, details: dict}
    """
    clean = (prompt_text or "").strip().lower()
    words = clean.split()
    word_count = len(words)

    if word_count < 8 or clean.startswith("[no prompt"):
        return {
            "tier": "weak",
            "score": min(4, word_count // 2),
            "role_pts": 1 if word_count >= 5 else 0,
            "taxonomy_pts": 0,
            "discrimination_pts": 0,
            "constraints_pts": 0,
        }

    # 1. Role Directive (0-3)
    role_pts = 0
    if any(k in clean for k in ["you are", "role", "act as", "specialist", "agent", "expert", "analyst", "solver", "detective"]):
        role_pts = 3
    elif any(k in clean for k in ["extract", "identify", "analyze", "order", "deduce", "solve", "reconstruct", "construct", "synthesize"]):
        role_pts = 2
    elif word_count >= 8 and any(k in clean for k in ["find", "look", "check", "review", "organize"]):
        role_pts = 1

    # 2. Scope & Taxonomy (0-3)
    tax_pts = 0
    if agent_role == "extractor":
        keywords = [
            "person", "people", "time", "timestamp", "location", "object", "movement",
            "tag", "badge", "flight", "cctv", "clue", "forensic", "chemical", "residue",
            "alibi", "suspect", "evidence", "log", "luggage", "bag"
        ]
        matches = sum(1 for k in keywords if k in clean)
        tax_pts = 3 if matches >= 3 else (2 if matches >= 2 else 1)
    elif agent_role == "reconstructor":
        keywords = ["first", "next", "chronological", "sequence", "timeline", "order", "minute", "timestamp", "step", "movement"]
        matches = sum(1 for k in keywords if k in clean)
        tax_pts = 3 if matches >= 3 else (2 if matches >= 1 else 1)
    else:  # solver / detective
        keywords = ["action", "decision", "rule", "protocol", "blocking", "resume", "culprit", "method", "clue", "weapon", "motive"]
        matches = sum(1 for k in keywords if k in clean)
        tax_pts = 3 if matches >= 3 else (2 if matches >= 1 else 1)

    # 3. Discrimination / Connecting (0-3)
    disc_pts = 0
    if agent_role == "extractor":
        if any(k in clean for k in ["confirmed", "uncertain", "unverified", "distinguish", "separate", "verify", "verified"]):
            disc_pts = 3
        elif any(k in clean for k in ["fact", "evidence", "observation"]):
            disc_pts = 1
    elif agent_role == "reconstructor":
        if any(k in clean for k in ["connect", "depend", "cause", "lead to", "relationship", "track"]):
            disc_pts = 3
        elif any(k in clean for k in ["between", "link", "move"]):
            disc_pts = 1
    else:
        if any(k in clean for k in ["evaluate", "satisfy", "violate", "deduce", "prove", "disprove", "eliminate"]):
            disc_pts = 3
        elif any(k in clean for k in ["why", "because", "condition"]):
            disc_pts = 1

    # 4. Constraints & Resolution Clarity (0-3) - NO MANDATORY JSON FORMATTING
    con_pts = 0
    has_constraint = any(k in clean for k in ["do not", "never", "refrain", "don't", "avoid", "without", "no "])
    if agent_role in ("extractor", "reconstructor"):
        has_filter = any(k in clean for k in ["noise", "ignore", "filter", "chatter", "distraction", "neutral"])
        if has_constraint and has_filter:
            con_pts = 3
        elif has_constraint or has_filter:
            con_pts = 2
        elif word_count >= 15:
            con_pts = 1
    else:
        has_format = any(k in clean for k in ["json", "format", "schema", "keys", "valid json"])
        has_decision_focus = any(k in clean for k in ["culprit", "method", "motive", "rule", "clue", "evidence", "verdict", "decision", "action"])
        if (has_constraint and (has_format or has_decision_focus)) or (has_format and has_decision_focus):
            con_pts = 3
        elif has_constraint or has_format or has_decision_focus:
            con_pts = 2
        elif word_count >= 15:
            con_pts = 1

    total_score = min(12, role_pts + tax_pts + disc_pts + con_pts)
    tier = "strong" if total_score >= 9 else ("moderate" if total_score >= 6 else "weak")

    return {
        "tier": tier,
        "score": total_score,
        "role_pts": role_pts,
        "taxonomy_pts": tax_pts,
        "discrimination_pts": disc_pts,
        "constraints_pts": con_pts,
    }


class MockOfflineChatModel(SimpleChatModel):
    """
    Self-contained offline simulation model for live demos without internet access.
    Produces scaled agent outputs based on prompt engineering quality.
    """
    model_name: str = "offline-relay-simulator"

    @property
    def _llm_type(self) -> str:
        return "offline-relay-simulator"

    def _call(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        text_joined = " ".join([m.content if isinstance(m.content, str) else str(m.content) for m in messages])

        # Extract user prompt snippet
        user_prompt = ""
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            if "USER PROMPT:" in content:
                user_prompt = content.split("USER PROMPT:", 1)[1].split("\n\n", 1)[0].strip()
                break

        is_museum = any(k in text_joined.lower() for k in [
            "celestial madonna", "gallery 4", "riverton", "julian vance", "marcus thorne",
            "breaker b-04", "locker 14", "c-408", "consv-408", "rm-1887-04"
        ])
        is_airport = not is_museum
        sys_message = str(messages[0].content) if messages else ""

        is_reconstructor = "You are Agent 2" in sys_message or "Agent 2:" in sys_message or "Timeline & Incident Reconstructor" in sys_message
        is_solver = "You are Agent 3" in sys_message or "Agent 3:" in sys_message or "Logic Solver" in sys_message

        # Agent 2 (Reconstructor)
        if is_reconstructor:
            eval_res = classify_prompt_quality(user_prompt, "reconstructor")
            tier = eval_res["tier"]
            if is_museum:
                if tier == "weak":
                    return (
                        "Preliminary Timeline (Incomplete):\n"
                        "- Evening: Gala began.\n"
                        "- Later: Power tripped and painting was missing.\n"
                        "[TIMELINE INCOMPLETE: Chronological sequencing omitted.]"
                    )
                elif tier == "moderate":
                    return (
                        "Chronological Order of Events:\n"
                        "• 21:15: Dr. Julian Vance checks in with Conservation credentials.\n"
                        "• 23:40: Breaker B-04 trips and Chief Thorne goes to sub-station.\n"
                        "• 23:41: Gallery 4 alarm trips during blackout.\n"
                        "• 23:42: Suspect flees through basement passage carrying canvas tube.\n"
                        "• 23:48: Officer Carter finds token C-408 and card in Locker 14."
                    )
                else:
                    return (
                        "Reconstructed Chronological Sequence of Events:\n"
                        "• 21:15:42: Dr. Julian Vance enters with Conservation clearance CONSV-04.\n"
                        "• 23:40:42.286: Breaker B-04 manually tripped, initiating 90-second auxiliary failover and disabling Beam Grid #7.\n"
                        "• 23:40:50: Chief Marcus Thorne dispatched to sub-station, providing inside cover.\n"
                        "• 23:41:00: Original 'The Celestial Madonna' sliced and replaced with Vance's synthetic acrylic forgery RM-1887-04.\n"
                        "• 23:42:10: Masked courier flees CAM-18 basement passage carrying canvas tube, depositing it at Locker 14 within the 90-second gap.\n"
                        "• 23:48:00: Officer Carter recovers Cloakroom token No. C-408 and Conservation RFID badge #408 from Locker 14.\n"
                        "• Causal Dependency: The 90-second Breaker B-04 blackout directly enabled the canvas forgery swap and drop-off at Locker 14."
                    )
            else:  # Airport Crisis
                if tier == "weak":
                    return "Preliminary Timeline (Incomplete):\n- Morning: Passenger checked in.\n- Later: Bag was seen near gate.\n[TIMELINE INCOMPLETE: Chronological sequencing omitted.]"
                elif tier == "moderate":
                    return (
                        "Chronological Order of Events:\n"
                        "• 08:14: Daniel Kim checks in blue suitcase.\n"
                        "• 08:30: Flight SW 472 boarding initiated at Gate B07.\n"
                        "• 08:46: Aarav Mehta spots unattended blue suitcase.\n"
                        "• 08:49: Officer R. Nair alerts control desk."
                    )
                else:
                    return (
                        "Reconstructed Chronological Sequence of Events:\n"
                        "• 08:14:23: Daniel Kim completes check-in at Counter A04 for SW 472; genuine 18.4 kg diamond suitcase tagged.\n"
                        "• 08:16:05: Supervisor Tariq Malik (RAMP-882) prints duplicate bag tag via override REPRINT-MGR-02.\n"
                        "• 08:30:00: Terminal 1 FIDS calls priority boarding for Flight SW 472 at Gate B07.\n"
                        "• 08:35:00: Aarav Mehta arrives at Gate B07 waiting bay.\n"
                        "• 08:46:00: Unattended 12.1 kg sandbag decoy suitcase abandoned under Gate B07 window seats.\n"
                        "• 08:47:10: Suspect in dark hooded windbreaker with orange-soled ramp boots flees through staff door B-Staff-03 (logged to Tariq Malik at 08:47:45).\n"
                        "• 08:49:00: Officer R. Nair establishes observation perimeter, logs 6.3 kg weight discrepancy, and requests K9 sweep.\n"
                        "• 09:02:55: On Apron Bay 3, Tariq Malik diverts genuine 18.4 kg diamond suitcase off the belt into Maintenance Cart #MC-08.\n"
                        "• Causal Dependency: Abandoning the decoy bag at Gate B07 triggered a sterile zone security distraction under Rule SEC-101, directly enabling the insider luggage swap on Apron Bay 3 into Cart #MC-08."
                    )

        # Agent 3 (Solver / Detective)
        elif is_solver:
            eval_res = classify_prompt_quality(user_prompt, "solver")
            tier = eval_res["tier"]
            score = eval_res["score"]
            user_p_lower = user_prompt.lower()
            if is_airport:
                if tier == "weak":
                    return json.dumps({
                        "action": "Undetermined (User prompt lacked operational safety directives)",
                        "supporting_rules": "Unspecified (Incomplete prompt)",
                        "blocking_condition": "Unspecified (Incomplete prompt)"
                    }, indent=2)
                elif tier == "moderate" or score < 8 or not any(r in user_p_lower for r in ["ops-204", "sec-101", "bagg-204"]):
                    return json.dumps({
                        "action": "HOLD Flight SW 472 at Gate B07",
                        "culprit": "Tariq Malik (suspected on Flight SW 472)",
                        "supporting_rules": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol)",
                        "method": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol)",
                        "rule_broken": "SEC-101",
                        "blocking_condition": "Unattended blue bag awaiting K9 unit sweep at Gate B07",
                        "clue": "Unattended blue bag awaiting K9 unit sweep at Gate B07",
                        "evidence_keys": ["Unattended blue bag awaiting K9 unit sweep at Gate B07"]
                    }, indent=2)
                elif not any(k in user_p_lower for k in ["evidence_keys", "skw-", "daniel kim", "barcode", "tag", "malik", "tariq", "reprint", "cart"]):
                    return json.dumps({
                        "action": "HOLD Flight SW 472 at Gate B07 and suspend passenger boarding",
                        "culprit": "Tariq Malik (Flight SW 472 Ramp Supervisor)",
                        "supporting_rules": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "method": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "rule_broken": "Rule SEC-101 and Rule OPS-204",
                        "blocking_condition": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance",
                        "clue": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance",
                        "motive": "Illicit diamond smuggling and theft via baggage swap",
                        "evidence_keys": [
                            "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49",
                            "Awaiting K9 explosive sweep clearance before departure authorization"
                        ]
                    }, indent=2)
                else:
                    return json.dumps({
                        "action": "HOLD Flight SW 472 at Gate B07 immediately, suspend passenger boarding, cordon off the Gate B07 seating area, and dispatch the K9 explosive detection unit to inspect the unattended blue baggage",
                        "culprit": "Tariq Malik (Flight SW 472 Ramp Supervisor)",
                        "supporting_rules": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "method": "Baggage swap using duplicate tag #SKW-78921-472 printed via supervisor override card REPRINT-MGR-02, leaving a 12.1 kg decoy bag at Gate B07 to trigger a sterile zone security hold while diverting the authentic 18.4 kg diamond consignment on Apron Bay 3 into Cart #MC-08 under Rule SEC-101 and Rule BAGG-204",
                        "rule_broken": "Rule SEC-101, Rule OPS-204, and Rule BAGG-204",
                        "blocking_condition": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance and passenger ownership verification (tag: Daniel Kim #SKW-78921-472 reprinted by RAMP-882)",
                        "clue": "Baggage tag reprint authorization REPRINT-MGR-02 matching Tariq Malik (RAMP-882), orange-soled tarmac boots on CAM 12, door B-Staff-03 badge swipe log at 08:47:45, and 6.3 kg weight discrepancy between check-in scale (18.4 kg) and gate decoy (12.1 kg)",
                        "motive": "Illicit $3.5M industrial diamond smuggling and theft by diverting cargo manifest #DIA-904 into an apron maintenance cart before flight departure",
                        "evidence_keys": [
                            "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49",
                            "Bag tag #SKW-78921-472 belongs to Daniel Kim (Counter A04)",
                            "CCTV CAM 12 captures unidentified hooded individual fleeing Gate B07 corridor at 08:47:10 with orange-soled tarmac boots",
                            "Door B-Staff-03 electronic card swipe at 08:47:45 logged to Badge #RAMP-882 (Tariq Malik)",
                            "Reprint authorization REPRINT-MGR-02 on decoy bag tag matches supervisor Tariq Malik",
                            "Awaiting K9 explosive sweep clearance before departure authorization"
                        ]
                    }, indent=2)
            elif is_museum:
                if tier == "weak":
                    return json.dumps({
                        "culprit": "Undetermined (User prompt lacked deductive instructions)",
                        "method": "Unspecified (Incomplete prompt)",
                        "clue": "Unspecified (Incomplete prompt)"
                    }, indent=2)
                elif tier == "moderate" or score < 8 or not any(r in user_p_lower for r in ["sec-401", "art-302", "401", "302", "lockdown protocol", "custody standard"]):
                    return json.dumps({
                        "culprit": "Dr. Julian Vance (suspected, pending verification)",
                        "method": "Blackout during museum gala",
                        "clue": "Locker 14 in service corridor",
                        "rule_broken": "Rule SEC-401",
                        "motive": "Priceless artwork theft and forgery distribution"
                    }, indent=2)
                elif not any(k in user_p_lower for k in ["evidence_keys", "consv-408", "c-408", "token", "sub-station", "acrylic"]):
                    return json.dumps({
                        "culprit": "Dr. Julian Vance and Marcus Thorne",
                        "method": "Breaker B-04 blackout exploiting 90-second auxiliary power gap to swap canvas with synthetic forgery under Rule SEC-401 and Rule ART-302",
                        "clue": "Torn memo scrap recovered from Gallery 4 Row B seating area",
                        "rule_broken": "Rule SEC-401 and Rule ART-302",
                        "motive": "Replace historic masterpiece with synthetic acrylic forgery for illicit overseas private sale",
                        "evidence_keys": [
                            "Breaker B-04 tripped at 23:40:42 disabling Beam Grid #7 for 90-second generator window",
                            "Torn memo scrap recovered from Gallery 4 Row B seating area"
                        ]
                    }, indent=2)
                else:
                    return json.dumps({
                        "culprit": "Dr. Julian Vance (Head of Conservation) and Chief Marcus Thorne (Security Accomplice)",
                        "method": "Breaker B-04 intentional blackout exploiting 90-second auxiliary power failover to swap original canvas with synthetic acrylic forgery and drop tube at Locker 14 under Rule SEC-401 and Rule ART-302",
                        "rule_broken": "Rule SEC-401, Rule ART-302, and Rule CLR-505",
                        "clue": "Locker 14 search yielded Conservation RFID keycard CONSV-408 and Private Vault cloakroom token C-408 matching Julian Vance, disproving Thorne's sub-station sabotage alibi and proving canvas swap forgery RM-1887-04",
                        "motive": "Replace authentic Renaissance masterpiece with synthetic acrylic forgery for illicit high-value private sale",
                        "evidence_keys": [
                            "Recovered Conservation staff access card #408 (CONSV-408) and Gala Cloakroom token No. C-408 from Locker 14",
                            "Lab spectrometry confirming wall painting RM-1887-04 is a 2023 synthetic acrylic forgery with zinc white",
                            "SCADA telemetry and Evidence #04 memo confirming Breaker B-04 trip 90-second blackout loop",
                            "Thorne sub-station sabotage alibi disproven by insider timing and Locker 14 drop"
                        ]
                    }, indent=2)

        # Agent 1 (Extractor)
        else:
            eval_res = classify_prompt_quality(user_prompt, "extractor")
            tier = eval_res["tier"]
            if is_museum:
                if tier == "weak":
                    return (
                        "Surface Observations (Extraction Incomplete):\n"
                        "- Winter Gala at Riverton Museum was attended by hundreds of patrons.\n"
                        "- Luxe Catering delivered champagne and broke a crate at 21:25.\n"
                        "- Elena Rossi was coordinating the event schedule.\n"
                        "[EXTRACTION INCOMPLETE: Timestamps, SCADA logs, lab spectrometry, torn notes, and evidence locker items were omitted because user prompt lacked specific extraction directives.]"
                    )
                elif tier == "moderate":
                    return (
                        "Extracted Evidence (Partial):\n"
                        "- 21:15: Dr. Julian Vance (Badge CONSV-04) checked into gala.\n"
                        "- 23:40:42: Breaker B-04 tripped, disrupting Wing C Gallery 4 Beam Grid #7.\n"
                        "- 23:42:10: CCTV CAM-18 caught masked individual with canvas tube in basement passage.\n"
                        "- Lab analysis RM-1887-04 showed synthetic acrylic binder in the framed painting.\n"
                        "- Locker 14 search yielded Gala token C-408 and staff card #408."
                    )
                else:
                    return (
                        "Verified Clues & Factual Evidence Extracted:\n"
                        "- 21:15:42: Dr. Julian Vance (Head of Conservation, Badge CONSV-04) checked into gala with access to Gallery 4 and Private Vault.\n"
                        "- 23:40:42.286: SCADA logged Breaker B-04 trip causing 90-second auxiliary power blackout loop and disrupting Beam Grid #7.\n"
                        "- 23:40: Chief Marcus Thorne dispatched in person to basement sub-station.\n"
                        "- 23:42:10: CCTV CAM-18 recorded masked suspect fleeing basement corridor carrying canvas travel tube toward Stairwell C1 / Fire Exit.\n"
                        "- 23:48:00: Officer J. Carter searched Locker 14, recovering Gala Cloakroom token No. C-408 and Conservation staff RFID access card #408 (CONSV-408).\n"
                        "- Lab Spectrometry: Painting RM-1887-04 left on wall confirmed as modern synthetic acrylic forgery (circa 2023) with zinc white.\n"
                        "- Evidence #04 Memo: 'Breaker B-04 loop: 90 sec gap before aux power - switch canvas - drop tube at Locker 14.'\n"
                        "- Filtered Distractions: Luxe Catering dropped crate at 21:25 and Elena Rossi logistics disregarded as peripheral noise."
                    )
            else:  # Airport Crisis
                if tier == "weak":
                    return (
                        "Surface Observations (Extraction Incomplete):\n"
                        "- Terminal 1 was bustling with morning departures.\n"
                        "- Daily Chronicle newspaper noted city marathon with 25,000 runners.\n"
                        "- Flight SW 561 to Dubai delayed at Gate B09.\n"
                        "[EXTRACTION INCOMPLETE: Timestamps, baggage tags, CCTV feeds, and security logs were omitted because user prompt lacked specific extraction directives.]"
                    )
                elif tier == "moderate":
                    return (
                        "Extracted Information (Partial):\n"
                        "- 08:30: Flight SW 472 to New York boarding at Gate B07.\n"
                        "- 08:35: Passenger Aarav Mehta at Gate B07 noticed a blue bag.\n"
                        "- Blue hard-shell suitcase reported near window seats.\n"
                        "- Security Officer R. Nair on patrol.\n"
                        "- Checked baggage conveyor active."
                    )
                else:  # strong
                    return (
                        "Verified Clues & Factual Evidence Extracted:\n"
                        "- 08:14:23: Passenger Daniel Kim checked in 18.4 kg blue polycarbonate suitcase at Counter A04 for Flight SW 472 (Consignment #DIA-904 diamonds).\n"
                        "- 08:16:05: Supervisor terminal accessed with keycard REPRINT-MGR-02 (Tariq Malik, Badge RAMP-882).\n"
                        "- 08:30:00: Flight SW 472 to New York commences priority boarding at Gate B07.\n"
                        "- 08:35 - 08:47: Passenger Aarav Mehta spots unattended blue bag under Gate B07 window seats with no owner present; sees hooded person with orange-soled ramp boots slip into staff door.\n"
                        "- 08:47:10: CCTV CAM 12 captures suspect in hooded windbreaker and orange-soled tarmac boots (Spec RAMP-882) unlocking Door B-Staff-03 at 08:47:45.\n"
                        "- 08:49:00: Officer R. Nair logs decoy blue suitcase; portable scale reads 12.1 kg (6.3 kg discrepancy); X-ray shows sand ballast.\n"
                        "- 09:02:55: CAM 21 shows genuine 18.4 kg diamond suitcase diverted into Maintenance Cart #MC-08 on Apron Bay 3 by Tariq Malik.\n"
                        "- Baggage Tag Barcode: Decoy bag tag #SKW-78921-472 has bottom watermark: REPRINT-MGR-02 / AUTH: RAMP-882.\n"
                        "- Filtered Distractions: Daily Chronicle marathon news and catering coffee deliveries disregarded as peripheral noise."
                    )

        return "Analysis completed successfully."


class RuntimeLLMConfig:
    def __init__(self):
        settings = get_settings()
        self.provider: str = getattr(settings, "DEFAULT_LLM_PROVIDER", "gemini")
        self.model_name: str = getattr(settings, "DEFAULT_MODEL_NAME", "gemini-3.8-flash")
        self.temperature: float = getattr(settings, "MODEL_TEMPERATURE", 0.2)
        self.timeout_seconds: int = getattr(settings, "MODEL_TIMEOUT_SECONDS", 30)
        self.fallback_to_offline: bool = getattr(settings, "FALLBACK_TO_OFFLINE", True)

    def update(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout_seconds: Optional[int] = None,
        fallback_to_offline: Optional[bool] = None,
    ):
        if provider is not None:
            self.provider = provider.lower()
        if model_name is not None:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = float(temperature)
        if timeout_seconds is not None:
            self.timeout_seconds = int(timeout_seconds)
        if fallback_to_offline is not None:
            self.fallback_to_offline = bool(fallback_to_offline)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "fallback_to_offline": self.fallback_to_offline,
        }


_runtime_config = RuntimeLLMConfig()


def get_runtime_config() -> RuntimeLLMConfig:
    return _runtime_config


@lru_cache(maxsize=16)
def _get_cached_llm(
    chosen_provider: str,
    chosen_model: str,
    temp: float,
    timeout: int,
    api_key: str,
) -> BaseChatModel:
    if chosen_provider in ("gemini", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=chosen_model or "gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=temp,
            timeout=timeout,
            max_output_tokens=700,
        )
    elif chosen_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=chosen_model or "gpt-4o-mini",
            api_key=api_key,
            temperature=temp,
            timeout=timeout,
            max_tokens=700,
        )
    elif chosen_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=chosen_model or "claude-3-5-haiku-20241022",
            api_key=api_key,
            temperature=temp,
            timeout=timeout,
            max_tokens=700,
        )
    return MockOfflineChatModel(model_name=chosen_model or "offline-relay-simulator")


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """Initialize and return the configured ChatModel (with keep-alive pooling)."""
    settings = get_settings()
    config = get_runtime_config()

    chosen_provider = (provider or config.provider).lower()
    chosen_model = model_name or config.model_name
    temp = temperature if temperature is not None else config.temperature
    timeout = config.timeout_seconds or settings.MODEL_TIMEOUT_SECONDS

    if chosen_provider in ("offline", "mock"):
        return MockOfflineChatModel(model_name=chosen_model or "offline-relay-simulator")

    if chosen_provider in ("gemini", "google"):
        api_key = settings.gemini_key
        if not api_key:
            logger.warning("No GEMINI_API_KEY found; falling back to MockOfflineChatModel")
            return MockOfflineChatModel()
        return _get_cached_llm(chosen_provider, chosen_model, temp, timeout, api_key)

    elif chosen_provider == "openai":
        return _get_cached_llm(chosen_provider, chosen_model, temp, timeout, settings.OPENAI_API_KEY or "")

    elif chosen_provider == "anthropic":
        return _get_cached_llm(chosen_provider, chosen_model, temp, timeout, settings.ANTHROPIC_API_KEY or "")

    elif chosen_provider == "ollama":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=settings.OLLAMA_BASE_URL,
            api_key="ollama",
            model=chosen_model or "qwen3:4b",
            temperature=temp,
            timeout=timeout,
            max_tokens=700,
        )

    return MockOfflineChatModel()


def test_llm_connection() -> Dict[str, Any]:
    """Test LLM connectivity and report status and latency."""
    start_time = time.time()
    config = get_runtime_config()
    try:
        model = get_llm()
        response = model.invoke("Ping. Return pong.")
        latency = round((time.time() - start_time) * 1000, 1)
        return {
            "status": "connected",
            "provider": config.provider,
            "model_name": config.model_name,
            "latency_ms": latency,
            "message": "Connection verified successfully.",
        }
    except Exception as e:
        latency = round((time.time() - start_time) * 1000, 1)
        logger.error(f"LLM connection test failed: {e}")
        return {
            "status": "error",
            "provider": config.provider,
            "model_name": config.model_name,
            "latency_ms": latency,
            "message": str(e),
        }
