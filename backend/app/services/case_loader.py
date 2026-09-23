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
