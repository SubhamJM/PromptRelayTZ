import asyncio
from fastapi import APIRouter, HTTPException

from backend.app.api.websocket import manager
from backend.app.models.room import (
    CreateRoomRequest,
    JoinRoomRequest,
    LockInRequest,
    RoomModel,
)
from backend.app.services.relay_runner import execute_multiplayer_relay
from backend.app.services.room_manager import get_local_ip, get_room_manager
from backend.app.services.scenario_loader import get_scenario_loader

router = APIRouter(prefix="/rooms", tags=["Multiplayer Rooms"])


@router.get("/network/server-info")
async def get_network_server_info():
    """Returns Laptop 1's local LAN IP address and join URL template

    for sharing across 3 laptops on the same Wi-Fi.
    """
    ip = get_local_ip()
    port = 8000
    return {
        "local_ip": ip,
        "port": port,
        "base_url": f"http://{ip}:{port}",
        "instructions": (
            f"Teammates on the same Wi-Fi can open: http://{ip}:{port} "
            "and enter the 4-letter Room Code."
        ),
    }


@router.post("/create")
async def create_room(req: CreateRoomRequest):
    room_mgr = get_room_manager()
    scenario_loader = get_scenario_loader()
    scenario = scenario_loader.get(req.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{req.scenario_id}' not found.")

    room = room_mgr.create_room(
        team_name=req.team_name,
        scenario_id=req.scenario_id,
        host_player_name=req.host_player_name,
        host_role=req.host_role,
        round_duration_seconds=req.round_duration_seconds,
    )
    ip = get_local_ip()
    return {
        "room": room.model_dump(),
        "room_code": room.room_code,
        "local_ip": ip,
        "join_url": f"http://{ip}:8000?room={room.room_code}",
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "difficulty": scenario.difficulty,
            "evidence_count": len(scenario.evidence_items),
        },
    }


@router.post("/join")
async def join_room(req: JoinRoomRequest):
    room_mgr = get_room_manager()
    room_code = req.room_code.upper().strip()
    try:
        room = room_mgr.join_slot(room_code, req.role, req.player_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Broadcast update to connected sockets
    await manager.broadcast(
        room_code,
        {
            "type": "ROOM_UPDATED",
            "room": room.model_dump(),
            "event": f"{req.player_name} joined as {req.role}",
        },
    )

    scenario_loader = get_scenario_loader()
    scenario = scenario_loader.get(room.scenario_id)

    return {
        "room": room.model_dump(),
        "role": req.role,
        "player_name": req.player_name,
        "scenario": {
            "id": scenario.id if scenario else room.scenario_id,
            "title": scenario.title if scenario else "Unknown Scenario",
            "evidence_items": scenario.evidence_items if scenario else [],
            "operational_rules": scenario.operational_rules if scenario else [],
        },
    }


@router.get("/{room_code}")
async def get_room_details(room_code: str):
    room_mgr = get_room_manager()
    room = room_mgr.get_room(room_code)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room '{room_code}' not found.")

    scenario_loader = get_scenario_loader()
    scenario = scenario_loader.get(room.scenario_id)

    return {
        "room": room.model_dump(),
        "scenario": {
            "id": scenario.id if scenario else room.scenario_id,
            "title": scenario.title if scenario else "Unknown Scenario",
            "difficulty": scenario.difficulty if scenario else "Hard",
            "evidence_items": scenario.evidence_items if scenario else [],
            "operational_rules": scenario.operational_rules if scenario else [],
        },
    }


@router.post("/{room_code}/start")
async def start_simultaneous_prompting(room_code: str):
    room_mgr = get_room_manager()
    try:
        room = room_mgr.start_prompting(room_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await manager.broadcast(
        room_code,
        {
            "type": "PROMPTING_STARTED",
            "room": room.model_dump(),
        },
    )
    return {"status": "started", "room": room.model_dump()}


@router.post("/{room_code}/lock-in")
async def lock_in_prompt_rest(room_code: str, req: LockInRequest):
    room_mgr = get_room_manager()
    try:
        room = room_mgr.lock_in_prompt(room_code, req.role, req.prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await manager.broadcast(
        room_code,
        {
            "type": "ROOM_UPDATED",
            "room": room.model_dump(),
            "event": f"{req.role} locked in prompt",
        },
    )

    if room_mgr.all_ready(room_code):
        asyncio.create_task(execute_multiplayer_relay(room_code, manager.broadcast))

    return {"status": "locked_in", "room": room.model_dump()}
