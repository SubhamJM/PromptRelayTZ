import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

from backend.app.models.scenario import Scenario, ScenarioSummary

logger = logging.getLogger(__name__)

SCENARIOS_DIR = Path(__file__).resolve().parent.parent.parent / "scenarios"


class ScenarioLoader:
    """Service to load, cache, and serve scenarios (both image and text-based)."""

    def __init__(self, scenarios_dir: Optional[Path] = None):
        self.scenarios_dir = scenarios_dir or SCENARIOS_DIR
        self._scenarios: Dict[str, Scenario] = {}
        self.load_all()

    def load_all(self) -> None:
        """Scan scenarios directory and validate all JSON scenario files."""
        self._scenarios.clear()
        if not self.scenarios_dir.exists():
            logger.warning(f"Scenarios directory not found at: {self.scenarios_dir}")
            return

        for path in sorted(self.scenarios_dir.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                scenario = Scenario.model_validate(data)
                self._scenarios[scenario.id] = scenario
                logger.info(f"Loaded scenario '{scenario.id}': {scenario.title} ({scenario.type})")
            except Exception as e:
                logger.error(f"Failed to load scenario file {path.name}: {e}")

    def get(self, scenario_id: str) -> Optional[Scenario]:
        if scenario_id in self._scenarios:
            return self._scenarios[scenario_id]
        aliases = {
            "case_01_blackwood_manor": "scenario_02_blackwood_manor",
            "case_02_neon_nexus": "scenario_03_neon_nexus",
            "case_03_velvet_vault": "scenario_04_velvet_vault",
            "case_04_airport_crisis": "scenario_01_airport_crisis",
        }
        target = aliases.get(scenario_id)
        if target and target in self._scenarios:
            return self._scenarios[target]
        return None

    def list_all(self) -> List[Scenario]:
        return list(self._scenarios.values())

    def list_summaries(self) -> List[ScenarioSummary]:
        return [
            ScenarioSummary(
                id=s.id,
                type=s.type,
                title=s.title,
                difficulty=s.difficulty,
                synopsis=s.synopsis,
                evidence_count=len(s.evidence_items),
                rule_count=len(s.operational_rules),
                has_images=any(bool(e.src) for e in s.evidence_items),
            )
            for s in self._scenarios.values()
        ]

    def check_leaks(self, scenario: Scenario, text: str) -> Tuple[bool, List[str]]:
        """Check if text prematurely mentions spoilers or target action/culprit."""
        if not text:
            return False, []

        normalized = text.lower()
        matched = []

        # Check target action / culprit name tokens
        target = scenario.ground_truth.target_action_or_culprit.lower()
        if target in normalized:
            matched.append(scenario.ground_truth.target_action_or_culprit)

        for kw in scenario.spoiler_keywords:
            if kw.lower() in normalized and kw not in matched:
                matched.append(kw)

        return len(matched) > 0, matched


@lru_cache
def get_scenario_loader() -> ScenarioLoader:
    return ScenarioLoader()
