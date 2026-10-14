import json
import logging
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

from backend.app.core.config import get_settings
from backend.app.models.case import CaseModel

logger = logging.getLogger(__name__)


BUILTIN_CASE_IDS = {
    "case_01_blackwood_manor",
    "case_02_neon_nexus",
    "case_03_velvet_vault",
    "case_04_airport_crisis",
}


class CaseLoader:
    """Service to load, cache, and serve murder mystery cases, and detect leaks."""

    def __init__(self, cases_dir: Optional[Path] = None):
        self.cases_dir = cases_dir or get_settings().CASES_DIR
        self._cases: Dict[str, CaseModel] = {}
        self.load_all_cases()

    def load_all_cases(self) -> None:
        """Scan the cases directory and validate all JSON case files."""
        self._cases.clear()
        if not self.cases_dir.exists():
            logger.warning(f"Cases directory not found at: {self.cases_dir}")
            return

        for file_path in sorted(self.cases_dir.glob("*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                case = CaseModel.model_validate(data)
                self._cases[case.case_id] = case
                logger.info(f"Loaded case '{case.case_id}': {case.title}")
            except Exception as e:
                logger.error(f"Failed to load case file {file_path.name}: {e}")

    def get_case(self, case_id: str) -> Optional[CaseModel]:
        """Fetch a case by its unique ID."""
        return self._cases.get(case_id)

    def list_cases(self) -> List[CaseModel]:
        """Return all loaded cases."""
        return list(self._cases.values())

    def save_case(self, case: CaseModel) -> Path:
        """Save a new or updated case to disk and register it."""
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        clean_id = case.case_id.replace(" ", "_").lower()
        if not clean_id.endswith(".json"):
            filename = f"{clean_id}.json"
        else:
            filename = clean_id
        file_path = self.cases_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(case.model_dump_json(indent=2))
        self._cases[case.case_id] = case
        logger.info(f"Saved custom case '{case.case_id}' to {file_path}")
        return file_path

    def delete_case(self, case_id: str) -> bool:
        """Delete a custom case file from disk. Built-in cases cannot be deleted."""
        if case_id in BUILTIN_CASE_IDS:
            raise ValueError(f"Cannot delete built-in case '{case_id}'.")

        clean_id = case_id.replace(" ", "_").lower()
        if not clean_id.endswith(".json"):
            filename = f"{clean_id}.json"
        else:
            filename = clean_id
        file_path = self.cases_dir / filename
        deleted = False
        if file_path.exists():
            file_path.unlink()
            deleted = True

        if case_id in self._cases:
            del self._cases[case_id]
            deleted = True
            logger.info(f"Deleted custom case '{case_id}'")
        return deleted

    def get_random_case(self, exclude_ids: Optional[List[str]] = None) -> CaseModel:
        """Select a random case, optionally excluding specific case IDs."""
        if not self._cases:
            raise RuntimeError(f"No cases available in {self.cases_dir}")

        exclude_set = set(exclude_ids or [])
        available = [c for c in self._cases.values() if c.case_id not in exclude_set]
        
        # If all cases have been excluded, fall back to all cases
        candidates = available if available else list(self._cases.values())
        return random.choice(candidates)

    def check_leak(self, case: CaseModel, text: str) -> Tuple[bool, List[str]]:
        """
        Inspect text to see if it triggers the leak trap by prematurely mentioning
        the murderer's name or any explicit leak keywords.
        Returns:
            Tuple of (is_leaked: bool, matched_keywords: List[str])
        """
        if not text:
            return False, []

        normalized_text = text.lower()
        matched = []

        # Always check the ground truth culprit full name
        culprit_normalized = case.ground_truth.culprit.lower()
        if culprit_normalized and culprit_normalized in normalized_text:
            matched.append(case.ground_truth.culprit)

        # Check configured leak keywords
        for keyword in case.leak_keywords:
            kw_clean = keyword.strip().lower()
            if kw_clean and kw_clean in normalized_text:
                if keyword not in matched:
                    matched.append(keyword)

        return len(matched) > 0, matched


@lru_cache
def get_case_loader() -> CaseLoader:
    """Return singleton instance of CaseLoader."""
    return CaseLoader()
