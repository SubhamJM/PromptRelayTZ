import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from backend.app.core.llm import get_runtime_config, test_llm_connection
from backend.app.models.case import CaseModel
from backend.app.services.case_loader import BUILTIN_CASE_IDS, CaseLoader, get_case_loader
from backend.app.services.database import MatchDatabase, get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


class ConfigureLLMRequest(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    timeout_seconds: Optional[int] = None
    fallback_to_offline: Optional[bool] = None


@router.get("/stats")
async def get_tournament_stats(db: MatchDatabase = Depends(get_database)):
    return db.get_stats()


@router.get("/matches")
async def list_matches(db: MatchDatabase = Depends(get_database)):
    return db.get_all_matches()


@router.get("/matches/{session_id}")
async def get_match_detail(session_id: str, db: MatchDatabase = Depends(get_database)):
    match = db.get_match(session_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match record not found.")
    return match


@router.delete("/matches/{session_id}")
async def delete_match(session_id: str, db: MatchDatabase = Depends(get_database)):
    deleted = db.delete_match(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Match not found.")
    return {"message": f"Match '{session_id}' deleted successfully."}


@router.get("/cases")
async def admin_list_cases(case_loader: CaseLoader = Depends(get_case_loader)):
    return [c.model_dump() for c in case_loader.list_cases()]


@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def admin_create_case(case_data: CaseModel, case_loader: CaseLoader = Depends(get_case_loader)):
    case_loader.save_case(case_data)
    return case_data.model_dump()


@router.delete("/cases/{case_id}")
async def admin_delete_case(case_id: str, case_loader: CaseLoader = Depends(get_case_loader)):
    if case_id in BUILTIN_CASE_IDS:
        raise HTTPException(status_code=400, detail="Cannot delete built-in cases.")
    deleted = case_loader.delete_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Case not found.")
    return {"message": f"Case '{case_id}' deleted successfully."}


@router.get("/export/csv")
async def export_csv(db: MatchDatabase = Depends(get_database)):
    csv_data = db.generate_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prompt_relay_leaderboard.csv"'},
    )


@router.get("/export/json")
async def export_json(db: MatchDatabase = Depends(get_database)):
    matches = db.get_all_matches()
    return Response(
        content=json.dumps(matches, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="prompt_relay_tournament_archive.json"'},
    )


@router.get("/llm/status")
async def get_llm_status():
    config = get_runtime_config()
    test_result = test_llm_connection()
    return {
        **config.to_dict(),
        "status": test_result["status"],
        "latency_ms": test_result.get("latency_ms"),
        "message": test_result.get("message"),
    }


@router.post("/llm/configure")
async def configure_llm(request: ConfigureLLMRequest):
    config = get_runtime_config()
    config.update(
        provider=request.provider,
        model_name=request.model_name,
        temperature=request.temperature,
        timeout_seconds=request.timeout_seconds,
        fallback_to_offline=request.fallback_to_offline,
    )
    test_result = test_llm_connection()
    return {
        **config.to_dict(),
        "status": test_result["status"],
        "latency_ms": test_result.get("latency_ms"),
        "message": test_result.get("message"),
    }


@router.post("/reset")
async def reset_tournament(db: MatchDatabase = Depends(get_database)):
    db.clear_all()
    return {"message": "Tournament history reset successfully."}
