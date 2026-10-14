import logging
import random
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.graph.nodes import (
    node_extractor,
    node_reconstructor,
    node_solver,
    node_evaluator,
)
from backend.app.graph.state import RelayState
from backend.app.models.api_dtos import (
    ActiveSessionRecoveryResponse,
    StartGameRequest,
    StartGameResponse,
    Step1Request,
    Step1Response,
    Step2Request,
    Step2Response,
    Step3Request,
    Step3Response,
)
from backend.app.models.scenario import ScenarioSummary
from backend.app.models.session import TurnStep
from backend.app.services.case_loader import CaseLoader, get_case_loader
from backend.app.services.database import MatchDatabase, get_database
from backend.app.services.scenario_loader import ScenarioLoader, get_scenario_loader
from backend.app.services.session_manager import SessionManager, get_session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/game", tags=["Game"])

# Node hooks for module-level test mocking
agent_1_extractor = node_extractor
agent_2_reconstructor = node_reconstructor
agent_3_detective = node_solver


@router.get("/scenarios", response_model=List[ScenarioSummary])
async def list_scenarios(scenario_loader: ScenarioLoader = Depends(get_scenario_loader)):
    """List available scenarios (both image and text-based) with summary metadata."""
    return scenario_loader.list_summaries()


@router.get("/cases")
async def list_cases(case_loader: CaseLoader = Depends(get_case_loader)):
    """Compatibility alias for list_scenarios returning legacy case format."""
    cases = []
    for c in case_loader.list_cases():
        cases.append({
            "case_id": c.case_id,
            "title": c.title,
            "synopsis": c.synopsis,
            "difficulty": c.difficulty,
            "noisy_case_file": c.noisy_case_file,
        })
    return cases


@router.get("/scenarios/{scenario_id}")
async def get_scenario_details(
    scenario_id: str,
    scenario_loader: ScenarioLoader = Depends(get_scenario_loader),
):
    """Fetch full scenario details (excluding ground truth)."""
    scenario = scenario_loader.get(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found.",
        )
    data = scenario.model_dump()
    data.pop("ground_truth", None)
    return data


@router.post("/start", response_model=StartGameResponse)
async def start_game(
    request: StartGameRequest,
    scenario_loader: ScenarioLoader = Depends(get_scenario_loader),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """Initialize a new game session."""
    target_id = request.scenario_id or request.case_id
    if target_id:
        scenario = scenario_loader.get(target_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario '{target_id}' not found.",
            )
    else:
        all_scenarios = scenario_loader.list_all()
        if not all_scenarios:
            raise HTTPException(status_code=500, detail="No scenarios installed.")
        scenario = random.choice(all_scenarios)

    session = session_manager.create_session(team_name=request.team_name, scenario=scenario)

    SCENARIO_TO_CASE = {
        "scenario_01_airport_crisis": "case_04_airport_crisis",
        "scenario_02_blackwood_manor": "case_01_blackwood_manor",
        "scenario_03_neon_nexus": "case_02_neon_nexus",
        "scenario_04_velvet_vault": "case_03_velvet_vault",
    }
    case_id = request.case_id or SCENARIO_TO_CASE.get(scenario.id, scenario.id)
    theme = "Airport Crisis" if "airport" in str(case_id).lower() or "airport" in str(scenario.id).lower() else scenario.title
    images = [
        item.model_dump() if hasattr(item, "model_dump") else item
        for item in scenario.evidence_items
    ]

    return StartGameResponse(
        session_id=session.session_id,
        team_name=session.team_name,
        current_step=session.current_step,
        scenario=session.scenario,
        case_id=case_id,
        case_title=scenario.title,
        case_file=scenario.dossier_text,
        theme=theme,
        images=images,
        operational_rules=scenario.operational_rules,
    )


@router.get("/session/{session_id}", response_model=ActiveSessionRecoveryResponse)
async def recover_active_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    db: MatchDatabase = Depends(get_database),
):
    """Recover an in-progress or completed match session."""
    session = session_manager.get_session(session_id)
    if not session:
        match = db.get_match(session_id)
        if match:
            return ActiveSessionRecoveryResponse(
                session_id=match["session_id"],
                team_name=match["team_name"],
                scenario=None,
                case_id=match.get("scenario_id"),
                current_step=TurnStep.COMPLETED,
                p1_prompt=match.get("p1_prompt"),
                a1_output=match.get("a1_output"),
                p2_prompt=match.get("p2_prompt"),
                a2_output=match.get("a2_output"),
                p3_prompt=match.get("p3_prompt"),
                final_verdict=match.get("final_verdict"),
                evaluation=match.get("evaluation"),
                total_score=match.get("total_score"),
                grade=match.get("grade"),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or expired.",
        )

    total_score = None
    grade = None
    if session.evaluation:
        total_score = getattr(session.evaluation, "total_score", None) or (
            session.evaluation.get("total_score") if isinstance(session.evaluation, dict) else None
        )
        grade = getattr(session.evaluation, "grade", None) or (
            session.evaluation.get("grade") if isinstance(session.evaluation, dict) else None
        )

    return ActiveSessionRecoveryResponse(
        session_id=session.session_id,
        team_name=session.team_name,
        scenario=session.scenario,
        case_id=session.scenario_id,
        current_step=session.current_step,
        p1_prompt=session.p1_prompt,
        a1_output=session.a1_output,
        p2_prompt=session.p2_prompt,
        a2_output=session.a2_output,
        p3_prompt=session.p3_prompt,
        final_verdict=session.final_verdict,
        evaluation=session.evaluation,
        total_score=total_score,
        grade=grade,
    )


@router.post("/step1", response_model=Step1Response)
async def submit_step_1(
    request: Step1Request,
    session_manager: SessionManager = Depends(get_session_manager),
):
    """Turn 1: Player 1 (Evidence Extractor) submission."""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.current_step not in (TurnStep.STEP1, TurnStep.WELCOME):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step progression: current step is {session.current_step.value}, expected Step 1.",
        )

    prompt_text = (request.prompt or request.user_1_prompt or "").strip()
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    state: RelayState = {
        "session_id": session.session_id,
        "team_name": session.team_name,
        "scenario": session.scenario,
        "case_file": session.scenario.dossier_text if session.scenario else "",
        "p1_prompt": prompt_text,
        "user_1_prompt": prompt_text,
    }

    result = agent_1_extractor(state)
    a1_output = result.get("a1_output") or result.get("agent_1_output") or ""

    session.p1_prompt = prompt_text
    session.a1_output = a1_output
    session.current_step = TurnStep.HANDOFF1
    session_manager.update_session(session)

    return Step1Response(
        session_id=session.session_id,
        current_step=session.current_step,
        a1_output=a1_output,
        agent_1_output=a1_output,
    )


@router.post("/step2", response_model=Step2Response)
async def submit_step_2(
    request: Step2Request,
    session_manager: SessionManager = Depends(get_session_manager),
):
    """Turn 2: Player 2 (Timeline Reconstructor) submission."""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.current_step not in (TurnStep.STEP2, TurnStep.HANDOFF1):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step progression: current step is {session.current_step.value}, expected Step 2.",
        )

    prompt_text = (request.prompt or request.user_2_prompt or "").strip()
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    state: RelayState = {
        "session_id": session.session_id,
        "team_name": session.team_name,
        "scenario": session.scenario,
        "p1_prompt": session.p1_prompt or "",
        "a1_output": session.a1_output or "",
        "agent_1_output": session.a1_output or "",
        "p2_prompt": prompt_text,
        "user_2_prompt": prompt_text,
        "leak_keywords": session.scenario.leak_keywords if session.scenario else [],
    }

    result = agent_2_reconstructor(state)
    a2_output = result.get("a2_output") or result.get("agent_2_output") or ""
    leak_detected = result.get("leak_detected", False)
    leak_keywords_found = result.get("leak_keywords_found", [])

    session.p2_prompt = prompt_text
    session.a2_output = a2_output
    session.current_step = TurnStep.HANDOFF2
    session_manager.update_session(session)

    return Step2Response(
        session_id=session.session_id,
        current_step=session.current_step,
        a2_output=a2_output,
        agent_2_output=a2_output,
        leak_detected=leak_detected,
        leak_keywords_found=leak_keywords_found,
    )


@router.post("/step3", response_model=Step3Response)
async def submit_step_3(
    request: Step3Request,
    session_manager: SessionManager = Depends(get_session_manager),
    db: MatchDatabase = Depends(get_database),
):
    """Turn 3: Player 3 (Logic Solver) submission and full calibrated evaluation."""
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.current_step not in (TurnStep.STEP3, TurnStep.HANDOFF2):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step progression: current step is {session.current_step.value}, expected Step 3.",
        )

    prompt_text = (request.prompt or request.user_3_prompt or "").strip()
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    # 1. Run Solver Node
    solver_state: RelayState = {
        "session_id": session.session_id,
        "team_name": session.team_name,
        "scenario": session.scenario,
        "p1_prompt": session.p1_prompt or "",
        "a1_output": session.a1_output or "",
        "agent_1_output": session.a1_output or "",
        "p2_prompt": session.p2_prompt or "",
        "a2_output": session.a2_output or "",
        "agent_2_output": session.a2_output or "",
        "p3_prompt": prompt_text,
        "user_3_prompt": prompt_text,
    }

    solver_res = agent_3_detective(solver_state)
    final_verdict = solver_res.get("final_verdict", {})
    a3_raw_output = (
        solver_res.get("a3_raw_output")
        or solver_res.get("raw_agent_3_output")
        or solver_res.get("agent_3_output")
        or ""
    )
    was_clean_json = solver_res.get("_was_clean_json", True)

    session.p3_prompt = prompt_text
    session.a3_raw_output = a3_raw_output
    session.final_verdict = final_verdict

    # 2. Run Evaluator Node
    eval_state: RelayState = {
        **solver_state,
        "final_verdict": final_verdict,
        "a3_raw_output": a3_raw_output,
        "raw_agent_3_output": a3_raw_output,
        "_was_clean_json": was_clean_json,
    }
    eval_res = node_evaluator(eval_state)
    report = eval_res["evaluation"]

    session.evaluation = report
    session.current_step = TurnStep.COMPLETED

    # 3. Persist completed match in SQLite leaderboard and session cache
    session_manager.save_session(session)
    db.save_match(session)

    total_score = getattr(report, "total_score", None) or (
        report.get("total_score") if isinstance(report, dict) else 0
    )
    grade = getattr(report, "grade", None) or (
        report.get("grade") if isinstance(report, dict) else "N/A"
    )

    return Step3Response(
        session_id=session.session_id,
        current_step=session.current_step,
        final_verdict=final_verdict,
        evaluation=report,
        agent_3_output=a3_raw_output,
        raw_agent_3_output=a3_raw_output,
        p1_prompt=session.p1_prompt,
        a1_output=session.a1_output,
        p2_prompt=session.p2_prompt,
        a2_output=session.a2_output,
        p3_prompt=session.p3_prompt,
        total_score=total_score,
        grade=grade,
    )


@router.get("/leaderboard")
async def get_leaderboard(db: MatchDatabase = Depends(get_database)):
    """Return top rankings for tournament leaderboard."""
    entries = db.get_leaderboard(limit=50)
    return {
        "total_matches": len(entries),
        "leaderboard": entries,
    }


@router.delete("/leaderboard")
async def delete_leaderboard(db: MatchDatabase = Depends(get_database)):
    """Reset leaderboard entries."""
    db.clear_all()
    return {"message": "Tournament leaderboard reset successfully."}
