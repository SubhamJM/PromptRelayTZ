import json
import logging
import time
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
    if any(k in clean for k in ["you are", "role", "act as", "specialist", "agent", "expert", "analyst"]):
        role_pts = 3
    elif any(k in clean for k in ["extract", "identify", "analyze", "order", "deduce", "solve", "reconstruct", "construct", "synthesize"]):
        role_pts = 2
    elif word_count >= 8 and any(k in clean for k in ["find", "look", "check", "review"]):
        role_pts = 1

    # 2. Scope & Taxonomy (0-3)
    tax_pts = 0
    if agent_role == "extractor":
        keywords = [
            "person", "people", "time", "timestamp", "location", "object", "movement",
            "tag", "badge", "flight", "cctv", "clue", "forensic", "chemical", "residue",
            "alibi", "suspect", "evidence", "log"
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

    # 4. Negative Constraints & Formatting (0-3)
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
        has_json = any(k in clean for k in ["json", "format", "schema", "keys", "valid json"])
        if has_constraint and has_json:
            con_pts = 3
        elif has_constraint or has_json:
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

        is_airport = any(k in text_joined.lower() for k in ["airport", "sw 472", "flight", "gate b07", "baggage", "daniel kim"])
        is_synthai = any(k in text_joined.lower() for k in ["synthai", "marcus vance", "elena rostova", "viktor kane", "maya lin", "omnipod", "omnidose", "cleanroom", "cyber-physical", "§404", "404"])
        is_gallery = any(k in text_joined.lower() for k in ["vernissage", "delacroix", "julian thorne", "maximillian cross", "helena rostova", "vitrine", "tetrodotoxin", "caesarean", "ruby", "gallery", "vault", "biological trace", "§201", "201"])
        is_blackwood = not (is_airport or is_synthai or is_gallery) or any(k in text_joined.lower() for k in ["blackwood", "reginald", "arthur bell", "higgins", "sugar tongs", "earl grey", "cyanide", "manor", "§102", "102", "peat"])
        sys_message = str(messages[0].content) if messages else ""

        is_reconstructor = "You are Agent 2" in sys_message or "Agent 2:" in sys_message or "Timeline & Incident Reconstructor" in sys_message
        is_solver = "You are Agent 3" in sys_message or "Agent 3:" in sys_message or "Logic Solver" in sys_message

        # Agent 2 (Reconstructor)
        if is_reconstructor:
            eval_res = classify_prompt_quality(user_prompt, "reconstructor")
            tier = eval_res["tier"]
            if is_airport:
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
                        "• 08:14:23: Daniel Kim completes check-in at Counter A04 for SW 472; blue suitcase tagged.\n"
                        "• 08:30:00: Terminal 1 FIDS calls priority boarding for Flight SW 472 at Gate B07.\n"
                        "• 08:35:00: Aarav Mehta arrives at Gate B07 waiting bay.\n"
                        "• 08:46:00: Unattended blue suitcase identified under Gate B07 window seats with no custodian.\n"
                        "• 08:47:10: Unidentified person in dark hooded windbreaker flees Gate B07 corridor.\n"
                        "• 08:49:00: Officer R. Nair establishes observation perimeter and initiates K9 explosive sweep request.\n"
                        "• Causal Dependency: Presence of an uninspected unattended suitcase directly impacts departure safety clearance for Flight SW 472."
                    )
            elif is_synthai:
                if tier == "weak":
                    return (
                        "Preliminary Timeline (Incomplete):\n"
                        "- Evening: Access logged.\n"
                        "- Later: Colleague found.\n"
                        "[TIMELINE INCOMPLETE: Chronological sequencing omitted.]"
                    )
                elif tier == "moderate":
                    return (
                        "Chronological Order of Events:\n"
                        "• 22:15: Dr. Elena Rostova enters cleanroom.\n"
                        "• 22:30: Marcus Vance checks into cleanroom.\n"
                        "• 22:42: Insulin pump override command delivered.\n"
                        "• 23:45: Dr. Rostova discovered collapsed in cleanroom."
                    )
                else:
                    return (
                        "Reconstructed Chronological Sequence of Events:\n"
                        "• 22:15:00: Dr. Elena Rostova enters Cleanroom 03.\n"
                        "• 22:30:00: Marcus Vance checks in to monitor model deployment.\n"
                        "• 22:42:14: BLE wireless sniffer captures encrypted payload broadcast from MAC D4:8A:3F:11:C9:82.\n"
                        "• 22:42:15: Omnipod pump receives external override command FORCE_BOLUS_MAX(25.0U).\n"
                        "• 22:41:00: Git commit pushed under Marcus Vance's name via automated cron shell script.\n"
                        "• 22:50:00: Marcus Vance checks out of cleanroom.\n"
                        "• 23:45:00: Dr. Rostova discovered unresponsive in Cleanroom 03.\n"
                        "• Causal Dependency: Concealed Pi Zero BLE transmission at 22:42:14 directly caused the fatal 25-unit insulin overdose."
                    )
            elif is_gallery:
                if tier == "weak":
                    return (
                        "Preliminary Timeline (Incomplete):\n"
                        "- Evening: Gala started.\n"
                        "- Later: Owner died in vault.\n"
                        "[TIMELINE INCOMPLETE: Chronological sequencing omitted.]"
                    )
                elif tier == "moderate":
                    return (
                        "Chronological Order of Events:\n"
                        "• 20:30: VIP champagne preview opens.\n"
                        "• 21:15: Display vitrine opened.\n"
                        "• 21:35: Gallery circuit breaker trips.\n"
                        "• 21:40: Henri Delacroix found collapsed in vault room."
                    )
                else:
                    return (
                        "Reconstructed Chronological Sequence of Events:\n"
                        "• 20:30:00: VIP champagne preview begins in Vernissage Grand Rotunda.\n"
                        "• 20:45 - 21:15: Julian Thorne observed near garden terrace and display vitrine.\n"
                        "• 21:15:00: Vitrine latch #V-02 coated with tetrodotoxin neurotoxin using black nitrile gloves.\n"
                        "• 21:35:00: Henri Delacroix touches brass vitrine latch barehanded, absorbing transdermal toxin.\n"
                        "• 21:40:00: Delacroix collapses; Caesarean Emerald Intaglio missing from vitrine.\n"
                        "• 22:45:00: Nitrile gloves recovered from restroom bin with Thorne DNA inside.\n"
                        "• Causal Dependency: Discarded nitrile gloves link the vitrine latch poisoning directly to Julian Thorne."
                    )
            else:
                if tier == "weak":
                    return (
                        "Preliminary Timeline:\n"
                        "- 8:00 PM: Tea served.\n"
                        "- Later: Body discovered.\n"
                        "[TIMELINE INCOMPLETE: Precise chronological minute sequencing and causal movements were omitted because the user prompt lacked reconstruction directives.]"
                    )
                elif tier == "moderate":
                    return (
                        "Chronological Sequence of Events:\n"
                        "• 8:00 PM: Butler Higgins serves Earl Grey tea with sugar cubes.\n"
                        "• 8:05 - 8:15 PM: Cellar leak emergency; tea tray unattended on sideboard.\n"
                        "• 8:35 PM: Lady Beatrice hears garden footsteps near conservatory.\n"
                        "• 9:05 PM: Dr. Bell claims arrival from clinic.\n"
                        "• 9:15 PM: Lord Reginald Blackwood discovered dead in study."
                    )
                else:
                    return (
                        "Reconstructed Chronological Sequence of Events:\n"
                        "• 8:00 PM: Butler Higgins brews tea with sugar cubes.\n"
                        "• 8:05 - 8:15 PM: Cellar leak emergency; tea tray left unattended in drawing room.\n"
                        "• 8:15 PM: Charles Blackwood spills red wine decanter in billiards room.\n"
                        "• 8:35 PM: Lady Beatrice hears garden footsteps; red peat mud deposited along conservatory path.\n"
                        "• 9:05 PM: Dr. Bell claims arrival, but riding boots already contain dried red peat greenhouse mud.\n"
                        "• 9:15 PM: Lord Reginald Blackwood discovered deceased in locked study.\n"
                        "• Causal Dependency: Unattended tea tray between 8:05-8:15 PM enabled poison application before Lord Reginald consumed it."
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
                elif tier == "moderate" or score < 8 or not any(r in user_p_lower for r in ["ops-204", "sec-101"]):
                    return json.dumps({
                        "action": "HOLD Flight SW 472 at Gate B07",
                        "culprit": "HOLD Flight SW 472 at Gate B07",
                        "supporting_rules": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol)",
                        "method": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol)",
                        "rule_broken": "SEC-101",
                        "blocking_condition": "Unattended blue bag awaiting K9 unit sweep at Gate B07",
                        "clue": "Unattended blue bag awaiting K9 unit sweep at Gate B07",
                        "evidence_keys": ["Unattended blue bag awaiting K9 unit sweep at Gate B07"]
                    }, indent=2)
                elif not any(k in user_p_lower for k in ["evidence_keys", "skw-", "daniel kim", "barcode", "tag"]):
                    return json.dumps({
                        "action": "HOLD Flight SW 472 at Gate B07 and suspend passenger boarding",
                        "culprit": "HOLD Flight SW 472 at Gate B07 and suspend passenger boarding",
                        "supporting_rules": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "method": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "rule_broken": "Rule SEC-101 and Rule OPS-204",
                        "blocking_condition": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance",
                        "clue": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance",
                        "motive": "Potential improvised explosive device (IED) or sterile zone contraband breach",
                        "evidence_keys": [
                            "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49",
                            "Awaiting K9 explosive sweep clearance before departure authorization"
                        ]
                    }, indent=2)
                else:
                    return json.dumps({
                        "action": "HOLD Flight SW 472 at Gate B07 immediately, suspend passenger boarding, cordon off the Gate B07 seating area, and dispatch the K9 explosive detection unit to inspect the unattended blue baggage",
                        "culprit": "HOLD Flight SW 472 at Gate B07 immediately, suspend passenger boarding, cordon off the Gate B07 seating area, and dispatch the K9 explosive detection unit to inspect the unattended blue baggage",
                        "supporting_rules": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "method": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
                        "rule_broken": "Rule SEC-101 and Rule OPS-204",
                        "blocking_condition": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance and passenger ownership verification (tag: Daniel Kim #SKW-78921-472)",
                        "clue": "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance and passenger ownership verification (tag: Daniel Kim #SKW-78921-472)",
                        "motive": "Potential improvised explosive device (IED) or sterile zone contraband breach",
                        "evidence_keys": [
                            "Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49",
                            "Bag tag #SKW-78921-472 belongs to Daniel Kim (Counter A04)",
                            "CCTV CAM 12 captures unidentified hooded individual fleeing Gate B07 corridor at 08:47:10",
                            "Awaiting K9 explosive sweep clearance before departure authorization"
                        ]
                    }, indent=2)
            elif is_synthai:
                if tier == "weak":
                    return json.dumps({
                        "culprit": "Undetermined (User prompt lacked deductive instructions)",
                        "method": "Unspecified (Incomplete prompt)",
                        "clue": "Unspecified (Incomplete prompt)"
                    }, indent=2)
                elif tier == "moderate" or score < 8 or not any(r in user_p_lower for r in ["standard §404", "§404", "404", "cyber-physical", "alibi integrity", "contradiction"]):
                    return json.dumps({
                        "culprit": "Marcus Vance (suspected, pending verification)",
                        "method": "Remote insulin pump overdose",
                        "clue": "Cleanroom BLE wireless packet capture",
                        "rule_broken": "Standard §404",
                        "motive": "AI safety audit benchmark score dispute"
                    }, indent=2)
                elif not any(k in user_p_lower for k in ["evidence_keys", "cron", "raspberry pi", "pi zero", "d4:8a"]):
                    return json.dumps({
                        "culprit": "Marcus Vance",
                        "method": "Remote Bluetooth Low Energy (BLE) override payload delivering a fatal 25-unit insulin bolus via concealed Raspberry Pi dongle",
                        "clue": "Cleanroom wireless sniffer captured Bluetooth BLE override transmission broadcast at 22:42:14",
                        "rule_broken": "Cyber-Physical Forensics Standard §404 and Alibi Integrity Rule",
                        "motive": "Dr. Rostova had discovered Marcus faked critical safety audit benchmark scores on the commercial AI model",
                        "evidence_keys": [
                            "Cleanroom wireless sniffer captured Bluetooth BLE override transmission broadcast at 22:42:14",
                            "Omnipod Serial #OP-9941 received external override command FORCE_BOLUS_MAX(25.0U)"
                        ]
                    }, indent=2)
                else:
                    return json.dumps({
                        "culprit": "Marcus Vance",
                        "method": "Remote Bluetooth Low Energy (BLE) override payload delivering a fatal 25-unit insulin bolus via concealed Raspberry Pi dongle",
                        "rule_broken": "Cyber-Physical Forensics Standard §404 and Alibi Integrity Rule",
                        "clue": "BLE sniffer matched MAC address D4:8A:3F:11:C9:82 on the concealed Pi Zero in Marcus Vance's drawer, and his commit was scheduled via automated cron",
                        "motive": "Dr. Rostova had discovered Marcus faked critical safety audit benchmark scores on the commercial AI model",
                        "evidence_keys": [
                            "BLE sniffer matched MAC address D4:8A:3F:11:C9:82 on the concealed Pi Zero in Marcus Vance's drawer",
                            "Terminal history reveals Marcus's git commit was executed by an automated cron shell script",
                            "Omnipod Serial #OP-9941 received external BLE override command FORCE_BOLUS_MAX(25.0U) at 22:42:15"
                        ]
                    }, indent=2)
            elif is_gallery:
                if tier == "weak":
                    return json.dumps({
                        "culprit": "Undetermined (User prompt lacked deductive instructions)",
                        "method": "Unspecified (Incomplete prompt)",
                        "clue": "Unspecified (Incomplete prompt)"
                    }, indent=2)
                elif tier == "moderate" or score < 8 or not any(r in user_p_lower for r in ["standard §201", "§201", "201", "biological trace", "property recovery", "contradiction"]):
                    return json.dumps({
                        "culprit": "Julian Thorne (suspected, pending verification)",
                        "method": "Tetrodotoxin neurotoxin poisoning",
                        "clue": "Black gloves found in restroom bin",
                        "rule_broken": "Standard §201",
                        "motive": "Dispute over counterfeit museum gem replicas"
                    }, indent=2)
                elif not any(k in user_p_lower for k in ["evidence_keys", "dna", "briefcase", "caesarean", "emerald"]):
                    return json.dumps({
                        "culprit": "Julian Thorne",
                        "method": "Tetrodotoxin neurotoxin coated onto the brass latch of the display vitrine, worn with nitrile gloves",
                        "clue": "Recovered black nitrile gloves in restroom tested positive for tetrodotoxin on the exterior",
                        "rule_broken": "Biological Trace Principle §201 and Property Recovery Presumption",
                        "motive": "Delacroix had discovered that Thorne had substituted fake replicas for museum gems in Julian's restoration workshop",
                        "evidence_keys": [
                            "Vitrine latch #V-02 coated with lethal transdermal dose of tetrodotoxin",
                            "Recovered black nitrile gloves in restroom tested positive for tetrodotoxin on the exterior"
                        ]
                    }, indent=2)
                else:
                    return json.dumps({
                        "culprit": "Julian Thorne",
                        "method": "Tetrodotoxin neurotoxin coated onto the brass latch of the display vitrine, worn with nitrile gloves",
                        "rule_broken": "Biological Trace Principle §201 and Property Recovery Presumption",
                        "clue": "Recovered nitrile gloves tested positive for tetrodotoxin on exterior and Julian Thorne's DNA inside, with the stolen Caesarean Emerald in his briefcase",
                        "motive": "Delacroix had discovered that Thorne had substituted fake replicas for three museum gems in Julian's restoration workshop",
                        "evidence_keys": [
                            "Black nitrile gloves recovered in bin tested positive for tetrodotoxin on exterior and Julian Thorne's DNA inside",
                            "Antique velvet jeweler's pouch containing the Caesarean Emerald Intaglio recovered from Julian Thorne's briefcase",
                            "Vitrine latch #V-02 coated with lethal transdermal dose of tetrodotoxin"
                        ]
                    }, indent=2)
            else:  # Blackwood Manor
                if tier == "weak":
                    return json.dumps({
                        "culprit": "Undetermined (User prompt lacked deductive instructions)",
                        "method": "Unspecified (Incomplete prompt)",
                        "clue": "Unspecified (Incomplete prompt)"
                    }, indent=2)
                elif tier == "moderate" or score < 8 or not any(r in user_p_lower for r in ["standard §102", "§102", "102", "timeline discrepancy", "forensic trace", "timeline contradiction", "contradiction"]):
                    return json.dumps({
                        "culprit": "Dr. Arthur Bell (suspected, pending verification)",
                        "method": "Potassium cyanide poisoning",
                        "clue": "Muddy riding boots in cloakroom",
                        "rule_broken": "Standard §102",
                        "motive": "Impending charity trust financial audit"
                    }, indent=2)
                elif not any(k in user_p_lower for k in ["evidence_keys", "sugar tongs", "tongs", "red peat", "greenhouse"]):
                    return json.dumps({
                        "culprit": "Dr. Arthur Bell",
                        "method": "Potassium cyanide coated onto Demerara sugar cubes using silver sugar tongs",
                        "clue": "Dr. Bell's riding boots were found in the cloakroom caked in dried mud",
                        "rule_broken": "Forensic Trace Standard §102 and Timeline Discrepancy Principle",
                        "motive": "Financial embezzlement of Lord Reginald's charitable foundation about to be exposed by an audit",
                        "evidence_keys": [
                            "Dr. Bell's riding boots were found in the cloakroom caked in dried mud",
                            "Tea tray left unattended on drawing room sideboard from 8:05 to 8:15 PM during cellar disturbance"
                        ]
                    }, indent=2)
                else:
                    return json.dumps({
                        "culprit": "Dr. Arthur Bell",
                        "method": "Potassium cyanide coated onto Demerara sugar cubes using silver sugar tongs",
                        "rule_broken": "Forensic Trace Standard §102 and Timeline Discrepancy Principle",
                        "clue": "Dr. Bell's boots were caked in red peat mud from the greenhouse path contradicting his 9:05 PM arrival alibi, and cyanide residue was found on the sugar tongs",
                        "motive": "Financial embezzlement of Lord Reginald's charitable foundation about to be exposed by an audit",
                        "evidence_keys": [
                            "Dr. Bell's boots were caked in red peat mud from the greenhouse path contradicting his 9:05 PM arrival alibi",
                            "Silver sugar tongs tested positive for potassium cyanide residue",
                            "Tea tray left unattended on drawing room sideboard from 8:05 to 8:15 PM during cellar disturbance",
                            "Bank seals on charity trust audit scrap found in Dr. Bell's pocket"
                        ]
                    }, indent=2)

        # Agent 1 (Extractor)
        else:
            eval_res = classify_prompt_quality(user_prompt, "extractor")
            tier = eval_res["tier"]
            if is_airport:
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
                        "- 08:14:23: Passenger Daniel Kim checked in blue polycarbonate suitcase at Counter A04 (Flight SW 472).\n"
                        "- 08:30:00: Flight SW 472 to New York commences boarding at Gate B07.\n"
                        "- 08:35 - 08:47: Passenger Aarav Mehta spots unattended blue bag under Gate B07 window seats with no owner present.\n"
                        "- 08:47:10: CCTV CAM 12 captures unidentified person in hooded windbreaker moving rapidly away from Gate B07.\n"
                        "- 08:49:00: Security Officer R. Nair logs unattended blue suitcase, cordons area, requests urgent K9 explosive sweep.\n"
                        "- Baggage Tag Barcode: Tag on unattended blue suitcase belongs to Daniel Kim (Flight SW 472).\n"
                        "- Filtered Distractions: Daily Chronicle marathon news and catering coffee deliveries disregarded as peripheral noise."
                    )
            elif is_synthai:
                if tier == "weak":
                    return (
                        "Surface Observations (Extraction Incomplete):\n"
                        "- Cleanroom 03 had high security.\n"
                        "- Dr. Rostova was found collapsed.\n"
                        "- Office had pizza boxes.\n"
                        "[EXTRACTION INCOMPLETE: Badge entries, wireless sniffer packets, and telemetry logs were omitted because user prompt lacked specific extraction directives.]"
                    )
                elif tier == "moderate":
                    return (
                        "Extracted Evidence (Partial):\n"
                        "- 22:15: Dr. Elena Rostova badge entry #004.\n"
                        "- 22:30: Marcus Vance badge entry #019.\n"
                        "- Omnipod insulin pump telemetry recorded bolus.\n"
                        "- Concealed USB battery pack in desk."
                    )
                else:
                    return (
                        "Verified Clues & Factual Evidence Extracted:\n"
                        "- 22:15: Dr. Elena Rostova (Badge #004) enters Cleanroom 03.\n"
                        "- 22:30 - 22:50: Marcus Vance (Badge #019) in cleanroom monitoring model deployment.\n"
                        "- 22:42:14: BLE wireless sniffer captures encrypted payload broadcast from MAC D4:8A:3F:11:C9:82 matching Pi Zero in Vance's drawer.\n"
                        "- 22:42:15: Omnipod pump Serial #OP-9941 receives override command FORCE_BOLUS_MAX(25.0U).\n"
                        "- 22:41:00: Git commit pushed under Marcus Vance's name executed by an automated cron shell script.\n"
                        "- 22:20 - 23:10: Devon Park verified in 2nd floor hardware staging lab.\n"
                        "- Filtered Noise: Cleanroom cooling manifold temperature alert and AWS support ticket dismissed as distractions."
                    )
            elif is_gallery:
                if tier == "weak":
                    return (
                        "Surface Observations (Extraction Incomplete):\n"
                        "- Beaux-Arts gala had 150 guests.\n"
                        "- Henri Delacroix collapsed in vault.\n"
                        "- Loud jazz music was playing.\n"
                        "[EXTRACTION INCOMPLETE: Chemical swabs, DNA matches, and alibis were omitted because user prompt lacked specific extraction directives.]"
                    )
                elif tier == "moderate":
                    return (
                        "Extracted Evidence (Partial):\n"
                        "- 20:30: Opening gala begins in Grand Rotunda.\n"
                        "- 21:40: Henri Delacroix found dead in vault display room.\n"
                        "- Vitrine latch tested positive for tetrodotoxin.\n"
                        "- Black nitrile gloves recovered in restroom bin."
                    )
                else:
                    return (
                        "Verified Clues & Factual Evidence Extracted:\n"
                        "- 21:40: Henri Delacroix discovered dead in private vault beside empty display vitrine.\n"
                        "- Toxicology: Cause of death was acute transdermal absorption of tetrodotoxin.\n"
                        "- Forensic Swab: Vitrine latch #V-02 coated with lethal transdermal tetrodotoxin.\n"
                        "- 21:30 - 21:40: Jean-Luc Fontaine verified resetting basement circuit breaker panel.\n"
                        "- 22:45: Black nitrile gloves in restroom bin test positive for tetrodotoxin on exterior and Julian Thorne DNA inside.\n"
                        "- Stolen Item Recovery: Julian Thorne's coat-check briefcase contained velvet pouch with Caesarean Emerald Intaglio.\n"
                        "- Filtered Noise: Broken champagne flutes and main salon catering dispute dismissed as peripheral noise."
                    )
            else:
                if tier == "weak":
                    return (
                        "Surface Observations:\n"
                        "- Heavy rain fell on the manor.\n"
                        "- Lord Reginald was found dead in the library.\n"
                        "- A mutton dinner was burned in the kitchen.\n"
                        "[EXTRACTION INCOMPLETE: Timestamps, forensic clues, and suspect alibis were omitted because the user prompt lacked specific extraction directives.]"
                    )
                elif tier == "moderate":
                    return "Extracted Evidence:\n- Earl Grey tea served with Demerara sugar cubes at 8:00 PM.\n- Tray left unattended on drawing room sideboard for 10 minutes.\n- Muddy boots in cloakroom.\n- Lord Reginald died in locked library."
                else:
                    return (
                        "Verified Clues & Forensic Facts Extracted:\n"
                        "- 8:00 PM: Butler Higgins serves Earl Grey tea with Demerara sugar cubes.\n"
                        "- 8:05 - 8:15 PM: Tea tray unattended on drawing room sideboard during cellar disturbance.\n"
                        "- Toxicology: Potassium cyanide detected on Demerara sugar cubes and silver sugar tongs.\n"
                        "- Footprint Corroboration: Wet red peat mud from greenhouse path found on Dr. Bell's boots in cloakroom.\n"
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


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """Initialize and return the configured ChatModel."""
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

        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=chosen_model or "gemini-3.8-flash",
            google_api_key=api_key,
            temperature=temp,
            timeout=timeout,
        )

    elif chosen_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=chosen_model or "gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=temp,
            timeout=timeout,
        )

    elif chosen_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=chosen_model or "claude-3-5-haiku-20241022",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temp,
            timeout=timeout,
        )

    elif chosen_provider == "ollama":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=settings.OLLAMA_BASE_URL,
            api_key="ollama",
            model=chosen_model or "qwen3:4b",
            temperature=temp,
            timeout=timeout,
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
