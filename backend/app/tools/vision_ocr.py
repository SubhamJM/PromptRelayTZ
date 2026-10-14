import re
from typing import Any, Dict, List, Optional


class VisionOCREvidenceTool:
    """
    Agent 1 Specialized Tool: OCR & Visual Evidence Extractor.
    Extracts text, metadata, timestamps, bounding descriptions, and confidence levels
    from multimodal visual evidence (CCTV feeds, gate monitors, badge scans, passenger texts, maps).
    """

    def __init__(self):
        self.name = "ocr_vision_tool"
        self.description = "Extracts text, objects, people, timestamps, and locations from visual evidence."

    def extract_evidence(
        self,
        visual_evidence_text: str,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Processes visual evidence text and optional image attachments,
        separating confirmed visual sightings, uncertain observations, and noise.
        """
        lines = [line.strip() for line in visual_evidence_text.split("\n") if line.strip()]
        
        people: List[str] = []
        timestamps: List[str] = []
        locations: List[str] = []
        objects: List[str] = []
        confirmed_facts: List[str] = []
        uncertain_facts: List[str] = []
        noise_filtered: List[str] = []
        image_attachments: List[Dict[str, Any]] = []

        # Process structured image attachments if provided
        if images:
            for img in images:
                title = img.get("title", "")
                fn = img.get("filename", "")
                ts = img.get("timestamp", "")
                src = img.get("src", "")
                if ts and ts != "--:--:--" and ts not in timestamps:
                    timestamps.append(ts)
                
                # Check for locations in title
                for lk in ["gate", "check-in", "baggage", "terminal", "corridor", "departure"]:
                    if lk in title.lower():
                        if title not in locations:
                            locations.append(title)

                desc = img.get("description", "")
                cat = img.get("category", "")
                badge = img.get("badge", "")

                image_attachments.append({
                    "filename": fn,
                    "title": title,
                    "category": cat,
                    "badge": badge,
                    "timestamp": ts,
                    "description": desc,
                    "src": src,
                })
                obs_detail = f"{desc}" if desc else f"captured at {ts}"
                confirmed_facts.append(
                    f"Visual Attachment ({fn} - {title}): {obs_detail}"
                )

        # Patterns
        time_pattern = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\b", re.IGNORECASE)
        location_keywords = [
            "gate", "terminal", "concourse", "ramp", "cargo", "checkpoint",
            "baggage", "runway", "lounge", "pod", "room", "corridor", "hall"
        ]
        noise_keywords = [
            "coffee", "muffin", "latte", "sunglasses", "weather", "rain",
            "cat", "dog", "music", "catering", "pizza", "boba", "snack", "wifi"
        ]
        uncertain_keywords = [
            "unclear", "blurry", "possible", "alleged", "claimed", "unverified",
            "unconfirmed", "obscured", "partial", "glitch", "maybe"
        ]

        for line in lines:
            # Check timestamps
            found_times = time_pattern.findall(line)
            for t in found_times:
                if t not in timestamps:
                    timestamps.append(t)

            lower = line.lower()

            # Check noise
            if any(nw in lower for nw in noise_keywords) and not any(crit in lower for crit in ["breach", "alarm", "security", "unauthorized", "prohibited", "bomb", "chemical", "poison", "tongs", "mud"]):
                noise_filtered.append(line)
                continue

            # Check locations
            for lk in location_keywords:
                if lk in lower:
                    # Extract nearby words or line snippet
                    match = re.search(rf"\b([A-Za-z0-9\-\s]{{2,20}}{lk}[A-Za-z0-9\-\s]{{0,15}})\b", line, re.IGNORECASE)
                    if match:
                        loc_clean = match.group(1).strip()
                        if loc_clean not in locations and len(loc_clean) < 30:
                            locations.append(loc_clean)

            # Categorize confirmed vs uncertain
            if any(uw in lower for uw in uncertain_keywords):
                uncertain_facts.append(line)
            else:
                confirmed_facts.append(line)

        return {
            "status": "success",
            "tool_name": self.name,
            "timestamps_detected": timestamps,
            "locations_detected": locations[:10],
            "confirmed_evidence_count": len(confirmed_facts),
            "uncertain_evidence_count": len(uncertain_facts),
            "noise_filtered_count": len(noise_filtered),
            "confirmed_facts": confirmed_facts,
            "uncertain_facts": uncertain_facts,
            "irrelevant_noise": noise_filtered,
            "image_attachments": image_attachments,
        }

    def run(
        self,
        visual_evidence_text: str,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Run the tool and format the extraction as a structured summary."""
        result = self.extract_evidence(visual_evidence_text, images=images)
        output_lines = [
            "=== OCR & VISION TOOL EXTRACTION REPORT ===",
            f"Timestamps Detected: {', '.join(result['timestamps_detected']) if result['timestamps_detected'] else 'None'}",
            f"Key Locations: {', '.join(result['locations_detected']) if result['locations_detected'] else 'None'}",
        ]
        if result.get("image_attachments"):
            output_lines.append(f"Visual Image Files Processed ({len(result['image_attachments'])}):")
            for img in result["image_attachments"][:5]:
                output_lines.append(f"  [IMAGE FEED] {img['filename']} - {img['title']} ({img['timestamp']})")
        output_lines.append(f"Confirmed Observations ({result['confirmed_evidence_count']}):")
        for f in result['confirmed_facts'][:8]:
            output_lines.append(f"  [CONFIRMED] {f}")
        if result['uncertain_facts']:
            output_lines.append(f"Uncertain / Low-Confidence Sightings ({result['uncertain_evidence_count']}):")
            for uf in result['uncertain_facts'][:5]:
                output_lines.append(f"  [UNCERTAIN] {uf}")
        if result['irrelevant_noise']:
            output_lines.append(f"Filtered Peripheral Noise ({result['noise_filtered_count']}):")
            for nf in result['irrelevant_noise'][:3]:
                output_lines.append(f"  [NOISE FILTERED] {nf}")
        output_lines.append("=== END VISION OCR REPORT ===")
        return "\n".join(output_lines)
