import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict

from backend.app.core.llm import get_llm
from backend.app.graph.nodes import (
    node_evaluator,
    node_extractor,
    node_reconstructor,
    node_solver,
)
from backend.app.models.case import CaseModel
from backend.app.services.case_loader import get_case_loader
from backend.app.services.database import get_database
from backend.app.services.room_manager import get_room_manager
from backend.app.services.scenario_loader import get_scenario_loader
from backend.app.services.session_manager import GameSession

logger = logging.getLogger(__name__)


async def execute_multiplayer_relay(
    room_code: str,
    broadcast_fn: Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]],
):
    """Executes the end-to-end 3-agent LangGraph relay for a multiplayer room

    and streams live step updates over WebSocket to all 3 connected laptops.
    """
    room_mgr = get_room_manager()
    room = room_mgr.get_room(room_code)
    if not room:
        logger.error(f"Cannot execute relay: Room '{room_code}' not found.")
        return

    room.status = "executing"
    await broadcast_fn(
        room_code,
        {
            "type": "EXECUTION_STARTED",
            "room_code": room_code,
            "team_name": room.team_name,
        },
    )

    # 1. Resolve Scenario & Case
    scenario_loader = get_scenario_loader()
    scenario = scenario_loader.get(room.scenario_id)
    case_loader = get_case_loader()
    case = case_loader.get_case(scenario.case_id if scenario else "case_04_airport_crisis")

    p1_prompt = room.slots["player_1"].prompt if room.slots.get("player_1") else ""
    p2_prompt = room.slots["player_2"].prompt if room.slots.get("player_2") else ""
    p3_prompt = room.slots["player_3"].prompt if room.slots.get("player_3") else ""

    # Build shared graph state
    state = {
        "scenario": scenario,
        "case_file": (scenario.dossier_text if scenario else (case.noisy_case_file if case else "")),
        "p1_prompt": p1_prompt,
        "p2_prompt": p2_prompt,
        "p3_prompt": p3_prompt,
        "user_1_prompt": p1_prompt,
        "user_2_prompt": p2_prompt,
        "user_3_prompt": p3_prompt,
        "leak_keywords": scenario.spoiler_keywords if scenario else (case.leak_keywords if case else []),
        "ground_truth": (
            scenario.ground_truth.model_dump()
            if scenario and scenario.ground_truth
            else (case.ground_truth.model_dump() if case else {})
        ),
    }

    active_llm = get_llm()

    # --- STEP 1: Agent 1 (Evidence Extractor) ---
    room.current_step = 1
    await broadcast_fn(
        room_code,
        {
            "type": "STEP_STARTED",
            "step": 1,
            "agent_name": "Agent 1: Evidence Extractor",
            "player_name": room.slots["player_1"].player_name if room.slots.get("player_1") else "Player 1",
            "prompt": p1_prompt,
        },
    )
    # Run node_extractor in executor so async event loop stays unblocked
    loop = asyncio.get_running_loop()
    a1_res = await loop.run_in_executor(None, lambda: node_extractor(state, llm=active_llm))
    state.update(a1_res)
    room.a1_output = a1_res.get("agent_1_output", "")

    await broadcast_fn(
        room_code,
        {
            "type": "STEP_DONE",
            "step": 1,
            "output": room.a1_output,
        },
    )
    await asyncio.sleep(0.8)

    # --- STEP 2: Agent 2 (Timeline Reconstructor) ---
    room.current_step = 2
    await broadcast_fn(
        room_code,
        {
            "type": "STEP_STARTED",
            "step": 2,
            "agent_name": "Agent 2: Incident Reconstructor",
            "player_name": room.slots["player_2"].player_name if room.slots.get("player_2") else "Player 2",
            "prompt": p2_prompt,
        },
    )
    state["agent_1_output"] = room.a1_output
    state["a1_output"] = room.a1_output
    a2_res = await loop.run_in_executor(None, lambda: node_reconstructor(state, llm=active_llm))
    state.update(a2_res)
    room.a2_output = a2_res.get("agent_2_output", "")

    await broadcast_fn(
        room_code,
        {
            "type": "STEP_DONE",
            "step": 2,
            "output": room.a2_output,
            "leak_detected": a2_res.get("leak_detected", False),
        },
    )
    await asyncio.sleep(0.8)

    # --- STEP 3: Agent 3 (Logic Solver) ---
    room.current_step = 3
    await broadcast_fn(
        room_code,
        {
            "type": "STEP_STARTED",
            "step": 3,
            "agent_name": "Agent 3: Logic Solver",
            "player_name": room.slots["player_3"].player_name if room.slots.get("player_3") else "Player 3",
            "prompt": p3_prompt,
        },
    )
    state["agent_2_output"] = room.a2_output
    state["a2_output"] = room.a2_output
    a3_res = await loop.run_in_executor(None, lambda: node_solver(state, llm=active_llm))
    state.update(a3_res)
    room.a3_output = a3_res.get("agent_3_output", "")
    room.final_verdict = a3_res.get("final_verdict", {})

    await broadcast_fn(
        room_code,
        {
            "type": "STEP_DONE",
            "step": 3,
            "output": room.a3_output,
            "final_verdict": room.final_verdict,
        },
    )
    await asyncio.sleep(0.8)

    # --- STEP 4: Analytical Evaluator & Score Calculation ---
    room.current_step = 4
    await broadcast_fn(room_code, {"type": "EVALUATION_STARTED"})
    eval_res = await loop.run_in_executor(None, lambda: node_evaluator(state))
    evaluation = eval_res.get("evaluation", {})
    room.evaluation = evaluation
    room.status = "completed"

    # --- Persist match to SQLite Database (Leaderboard & Admin Sync) ---
    try:
        db = get_database()
        session_id = f"multiplayer_{room.room_code}_{int(datetime.now(timezone.utc).timestamp())}"
        mock_game_session = GameSession(
            session_id=session_id,
            team_name=room.team_name,
            case=case or CaseModel(
                case_id=room.scenario_id,
                title=scenario.title if scenario else "Multiplayer Case",
                difficulty="Hard",
                synopsis=scenario.description if scenario else "",
                noisy_case_file="",
                ground_truth=scenario.ground_truth if scenario else None,
                leak_keywords=[],
            ),
            current_step="completed",
            state={
                "session_id": session_id,
                "team_name": room.team_name,
                "case_id": room.scenario_id,
                "user_1_prompt": p1_prompt,
                "agent_1_output": room.a1_output,
                "user_2_prompt": p2_prompt,
                "agent_2_output": room.a2_output,
                "user_3_prompt": p3_prompt,
                "raw_agent_3_output": room.a3_output,
                "final_verdict": room.final_verdict,
                "evaluation": evaluation,
            },
        )
        db.save_match(mock_game_session)
        logger.info(f"Multiplayer match '{session_id}' saved to leaderboard.")
    except Exception as e:
        logger.warning(f"Failed to persist multiplayer match to database: {e}")

    await broadcast_fn(
        room_code,
        {
            "type": "MATCH_COMPLETED",
            "room_code": room_code,
            "evaluation": evaluation,
            "final_verdict": room.final_verdict,
            "room": room.model_dump(),
        },
    )
