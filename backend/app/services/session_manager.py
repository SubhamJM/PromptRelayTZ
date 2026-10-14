import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Dict, List, Optional

from backend.app.models.scenario import Scenario
from backend.app.models.session import GameSession, TurnStep
from backend.app.services.database import MatchDatabase, get_database


class SessionManager:
    """Session management with dual in-memory cache and SQLite persistence for recovery."""

    def __init__(self, db: Optional[MatchDatabase] = None):
        self.db = db or get_database()
        self._cache: Dict[str, GameSession] = {}

    def create_session(self, team_name: str, scenario: Scenario) -> GameSession:
        session_id = f"relay_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        session = GameSession(
            session_id=session_id,
            team_name=team_name.strip(),
            scenario_id=scenario.id,
            scenario=scenario,
            current_step=TurnStep.STEP1,
            created_at=now,
            updated_at=now,
        )

        self._cache[session_id] = session
        self.db.save_active_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[GameSession]:
        if session_id in self._cache:
            return self._cache[session_id]

        # Check SQLite persistence (e.g. if server restarted or session was unloaded)
        session = self.db.get_active_session(session_id)
        if session:
            self._cache[session_id] = session
            return session
        return None

    def save_session(self, session: GameSession) -> None:
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._cache[session.session_id] = session
        self.db.save_active_session(session)

    def complete_session(self, session: GameSession) -> None:
        session.current_step = TurnStep.COMPLETED
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._cache[session.session_id] = session
        self.db.save_match(session)

    def update_session(self, session: GameSession) -> None:
        self.save_session(session)

    def clear(self) -> None:
        self._cache.clear()
        self.db.clear_all()

    def delete_session(self, session_id: str) -> None:
        if session_id in self._cache:
            del self._cache[session_id]
        self.db.delete_active_session(session_id)


@lru_cache
def get_session_manager() -> SessionManager:
    return SessionManager()
