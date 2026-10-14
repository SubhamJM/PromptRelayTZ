import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from backend.app.core.config import BASE_DIR, get_settings
from backend.app.models.session import GameSession

logger = logging.getLogger(__name__)


class MatchDatabase:
    """
    Production-grade SQLite database service operating in WAL mode.
    Handles finished matches leaderboard persistence and in-progress session recovery.
    """

    def __init__(self, db_path: Optional[Path] = None):
        settings = get_settings()
        self.db_path = db_path or (BASE_DIR / settings.DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=20.0,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            # 1. Matches Table (Leaderboard & Match Reports)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    session_id TEXT PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    scenario_title TEXT NOT NULL,
                    scenario_type TEXT NOT NULL,
                    total_score INTEGER NOT NULL,
                    grade TEXT NOT NULL,
                    p1_score INTEGER NOT NULL,
                    p2_score INTEGER NOT NULL,
                    p3_score INTEGER NOT NULL,
                    solution_score INTEGER NOT NULL,
                    final_verdict_json TEXT NOT NULL,
                    evaluation_json TEXT NOT NULL,
                    p1_prompt TEXT,
                    a1_output TEXT,
                    p2_prompt TEXT,
                    a2_output TEXT,
                    p3_prompt TEXT,
                    a3_output TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_matches_leaderboard
                ON matches(total_score DESC, completed_at ASC);
            """)

            # 2. In-Progress Sessions Table (For browser reload & crash recovery)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS active_sessions (
                    session_id TEXT PRIMARY KEY,
                    session_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.commit()

    def save_active_session(self, session: GameSession) -> None:
        """Persist in-progress session to SQLite so browser reload recovers exact step."""
        now = datetime.now(timezone.utc).isoformat()
        session_json = session.model_dump_json()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO active_sessions (session_id, session_json, updated_at)
                VALUES (?, ?, ?);
            """, (session.session_id, session_json, now))
            conn.commit()

    def get_active_session(self, session_id: str) -> Optional[GameSession]:
        """Fetch active session from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT session_json FROM active_sessions WHERE session_id = ?;", (session_id,))
            row = cursor.fetchone()
        if not row:
            return None
        try:
            data = json.loads(row["session_json"])
            return GameSession.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to deserialize active session {session_id}: {e}")
            return None

    def delete_active_session(self, session_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM active_sessions WHERE session_id = ?;", (session_id,))
            conn.commit()

    def save_match(self, session: GameSession, completed_at: Optional[str] = None) -> None:
        """Persist completed match and remove from active sessions."""
        now = completed_at or datetime.now(timezone.utc).isoformat()
        created_at = session.created_at or now

        # Extract values supporting both new objects and legacy test session structures
        eval_report = session.evaluation
        state = getattr(session, "state", None) or {}
        if not eval_report and "evaluation" in state:
            eval_report = state["evaluation"]

        if not eval_report:
            return

        if hasattr(eval_report, "total_score"):
            total_score = eval_report.total_score
            grade = eval_report.grade
            p1_score = eval_report.player_1.score
            p2_score = eval_report.player_2.score
            p3_score = eval_report.player_3.score
            solution_score = eval_report.solution.score
            evaluation_json = eval_report.model_dump_json()
        elif isinstance(eval_report, dict):
            total_score = eval_report.get("total_score", 0)
            grade = eval_report.get("grade", "N/A")
            breakdown = eval_report.get("breakdown", {})
            p1_score = breakdown.get("player_1", {}).get("score", 0)
            p2_score = breakdown.get("player_2", {}).get("score", 0)
            p3_score = breakdown.get("player_3", {}).get("score", 0)
            if "case_accuracy" in breakdown:
                solution_score = breakdown.get("case_accuracy", {}).get("score", 0)
            elif "culprit" in breakdown:
                solution_score = breakdown.get("culprit", {}).get("points", 0)
            else:
                solution_score = breakdown.get("solution", {}).get("score", 0)
            evaluation_json = json.dumps(eval_report)
        else:
            total_score, grade, p1_score, p2_score, p3_score, solution_score = 0, "N/A", 0, 0, 0, 0
            evaluation_json = "{}"

        # Resolve scenario title and id
        scenario = getattr(session, "scenario", None)
        case = getattr(session, "case", None)
        scenario_id = (
            getattr(session, "scenario_id", None)
            or (scenario.id if scenario and hasattr(scenario, "id") else None)
            or getattr(session, "case_id", None)
            or (case.case_id if case and hasattr(case, "case_id") else None)
            or state.get("case_id")
            or "scenario_unknown"
        )
        scenario_title = (
            (scenario.title if scenario and hasattr(scenario, "title") else None)
            or (case.title if case and hasattr(case, "title") else None)
            or scenario_id
        )
        scenario_type = "image" if "airport" in str(scenario_id).lower() else "text"

        final_verdict = session.final_verdict or state.get("final_verdict") or {}
        p1_prompt = session.p1_prompt or state.get("user_1_prompt") or ""
        a1_output = session.a1_output or state.get("agent_1_output") or ""
        p2_prompt = session.p2_prompt or state.get("user_2_prompt") or ""
        a2_output = session.a2_output or state.get("agent_2_output") or ""
        p3_prompt = session.p3_prompt or state.get("user_3_prompt") or ""
        a3_output = session.a3_raw_output or state.get("raw_agent_3_output") or state.get("agent_3_output") or ""

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO matches (
                    session_id, team_name, scenario_id, scenario_title, scenario_type,
                    total_score, grade,
                    p1_score, p2_score, p3_score, solution_score,
                    final_verdict_json, evaluation_json,
                    p1_prompt, a1_output,
                    p2_prompt, a2_output,
                    p3_prompt, a3_output,
                    created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                session.session_id,
                session.team_name,
                scenario_id,
                scenario_title,
                scenario_type,
                total_score,
                grade,
                p1_score,
                p2_score,
                p3_score,
                solution_score,
                json.dumps(final_verdict),
                evaluation_json,
                p1_prompt,
                a1_output,
                p2_prompt,
                a2_output,
                p3_prompt,
                a3_output,
                created_at,
                now,
            ))
            # Remove from active sessions
            conn.execute("DELETE FROM active_sessions WHERE session_id = ?;", (session.session_id,))
            conn.commit()

    def _enrich_match_dict(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Add backward-compatible aliases for tests and inspector."""
        m = dict(row_dict)
        m["final_verdict"] = json.loads(m.pop("final_verdict_json", "{}"))
        eval_dict = json.loads(m.pop("evaluation_json", "{}"))
        m["evaluation"] = eval_dict

        # Aliases
        m["case_id"] = m.get("scenario_id")
        m["case_title"] = m.get("scenario_title")
        m["user_1_prompt"] = m.get("p1_prompt")
        m["agent_1_output"] = m.get("a1_output")
        m["user_2_prompt"] = m.get("p2_prompt")
        m["agent_2_output"] = m.get("a2_output")
        m["user_3_prompt"] = m.get("p3_prompt")
        m["agent_3_output"] = m.get("a3_output")

        # Breakdown scores
        breakdown = eval_dict.get("breakdown", {})
        m["culprit_score"] = breakdown.get("culprit", {}).get("points", 40 if m.get("solution_score", 0) >= 30 else 0)
        m["method_score"] = breakdown.get("method", {}).get("points", 25 if m.get("solution_score", 0) >= 20 else 0)
        m["clue_score"] = breakdown.get("clue", {}).get("points", 20 if m.get("solution_score", 0) >= 10 else 0)
        m["format_score"] = breakdown.get("format", {}).get("points", 15)

        return m

    def get_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return tournament leaderboard ranked by total_score desc, completed_at asc."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    session_id, team_name, scenario_id, scenario_title, scenario_type,
                    total_score, grade, p1_score, p2_score, p3_score, solution_score,
                    completed_at
                FROM matches
                ORDER BY total_score DESC, completed_at ASC
                LIMIT ?;
            """, (limit,))
            rows = cursor.fetchall()

        leaderboard = []
        for idx, row in enumerate(rows, start=1):
            leaderboard.append({
                "rank": idx,
                "session_id": row["session_id"],
                "team_name": row["team_name"],
                "scenario_id": row["scenario_id"],
                "scenario_title": row["scenario_title"],
                "scenario_type": row["scenario_type"],
                "total_score": row["total_score"],
                "grade": row["grade"],
                "p1_score": row["p1_score"],
                "p2_score": row["p2_score"],
                "p3_score": row["p3_score"],
                "solution_score": row["solution_score"],
                "completed_at": row["completed_at"],
                # Backward compatibility
                "case_id": row["scenario_id"],
                "case_title": row["scenario_title"],
            })
        return leaderboard

    def get_match(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM matches WHERE session_id = ?;", (session_id,))
            row = cursor.fetchone()
        if not row:
            return None
        return self._enrich_match_dict(dict(row))

    def get_all_matches(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM matches ORDER BY total_score DESC, completed_at ASC;")
            rows = cursor.fetchall()
        return [self._enrich_match_dict(dict(r)) for r in rows]

    def delete_match(self, session_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM matches WHERE session_id = ?;", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_matches,
                    COALESCE(AVG(total_score), 0.0) as avg_score,
                    COALESCE(MAX(total_score), 0) as max_score,
                    COALESCE(MIN(total_score), 0) as min_score,
                    SUM(CASE WHEN total_score >= 90 THEN 1 ELSE 0 END) as perfect_or_s_count,
                    SUM(CASE WHEN solution_score >= 35 THEN 1 ELSE 0 END) as accurate_solves_count
                FROM matches;
            """)
            stats = dict(cursor.fetchone() or {})

            cursor_top = conn.execute("""
                SELECT scenario_title, COUNT(*) as play_count
                FROM matches
                GROUP BY scenario_id
                ORDER BY play_count DESC
                LIMIT 1;
            """)
            top_row = cursor_top.fetchone()
            top_scenario = top_row["scenario_title"] if top_row else "None"

        total = stats.get("total_matches", 0) or 0
        avg = round(float(stats.get("avg_score", 0.0) or 0.0), 1)
        accurate = stats.get("accurate_solves_count", 0) or 0
        solve_rate = round((accurate / total * 100), 1) if total > 0 else 0.0

        return {
            "total_matches": total,
            "average_score": avg,
            "highest_score": stats.get("max_score", 0) or 0,
            "lowest_score": stats.get("min_score", 0) or 0,
            "perfect_or_s_count": stats.get("perfect_or_s_count", 0) or 0,
            "accurate_solves_count": accurate,
            "solve_rate": solve_rate,
            "most_popular_scenario": top_scenario,
            # Backward compatibility aliases
            "culprit_solved_count": accurate,
            "culprit_solve_rate": solve_rate,
            "most_popular_case": top_scenario,
        }

    def generate_csv(self) -> str:
        import csv
        import io

        leaderboard = self.get_leaderboard(limit=1000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Rank", "Team Name", "Case ID", "Case Title", "Total Score",
            "Grade", "P1 Score", "P2 Score", "P3 Score", "Solution Score", "Completed At"
        ])
        for entry in leaderboard:
            writer.writerow([
                entry["rank"],
                entry["team_name"],
                entry["scenario_id"],
                entry["scenario_title"],
                entry["total_score"],
                entry["grade"],
                entry["p1_score"],
                entry["p2_score"],
                entry["p3_score"],
                entry["solution_score"],
                entry["completed_at"],
            ])
        return output.getvalue()

    def clear_leaderboard(self) -> None:
        self.clear_all()

    def clear(self) -> None:
        self.clear_all()

    def clear_all(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM matches;")
            conn.execute("DELETE FROM active_sessions;")
            conn.commit()


@lru_cache
def get_database() -> MatchDatabase:
    return MatchDatabase()
