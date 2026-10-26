import asyncio
import json
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.services.relay_runner import execute_multiplayer_relay
from backend.app.services.room_manager import get_room_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections for multi-laptop game rooms."""

    def __init__(self):
        # room_code -> list of active WebSockets
        self.active_rooms: Dict[str, List[WebSocket]] = {}
        # room_code -> {role: WebSocket}
        self.role_sockets: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_code: str, role: str, websocket: WebSocket):
        await websocket.accept()
        room_code = room_code.upper().strip()
        if room_code not in self.active_rooms:
            self.active_rooms[room_code] = []
            self.role_sockets[room_code] = {}

        self.active_rooms[room_code].append(websocket)
        self.role_sockets[room_code][role] = websocket
        logger.info(f"WebSocket connected: room={room_code}, role={role}")

    def disconnect(self, room_code: str, role: str, websocket: WebSocket):
        room_code = room_code.upper().strip()
        if room_code in self.active_rooms:
            if websocket in self.active_rooms[room_code]:
                self.active_rooms[room_code].remove(websocket)
            if self.role_sockets.get(room_code, {}).get(role) == websocket:
                del self.role_sockets[room_code][role]

            if not self.active_rooms[room_code]:
                del self.active_rooms[room_code]
                if room_code in self.role_sockets:
                    del self.role_sockets[room_code]

        logger.info(f"WebSocket disconnected: room={room_code}, role={role}")

    async def broadcast(self, room_code: str, message: dict):
        room_code = room_code.upper().strip()
        sockets = self.active_rooms.get(room_code, [])
        dead_sockets = []
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to socket in {room_code}: {e}")
                dead_sockets.append(ws)

        for ws in dead_sockets:
            if ws in sockets:
                sockets.remove(ws)


manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    return manager


@router.websocket("/ws/rooms/{room_code}/{role}")
async def room_websocket_endpoint(websocket: WebSocket, room_code: str, role: str):
    room_mgr = get_room_manager()
    room_code = room_code.upper().strip()
    room = room_mgr.get_room(room_code)

    if not room:
        await websocket.close(code=4004, reason=f"Room '{room_code}' does not exist.")
        return

    await manager.connect(room_code, role, websocket)
    room_mgr.set_connection_status(room_code, role, True)

    # Broadcast updated room state immediately on join
    await manager.broadcast(
        room_code,
        {
            "type": "ROOM_UPDATED",
            "room": room.model_dump(),
            "event": f"{role} connected",
        },
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "").upper()

            if msg_type == "PING":
                await websocket.send_json({"type": "PONG"})

            elif msg_type == "START_PROMPTING":
                # Host initiated start
                room = room_mgr.start_prompting(room_code)
                await manager.broadcast(
                    room_code,
                    {
                        "type": "PROMPTING_STARTED",
                        "room": room.model_dump(),
                    },
                )

            elif msg_type == "LOCK_IN":
                prompt_text = msg.get("prompt", "")
                room = room_mgr.lock_in_prompt(room_code, role, prompt_text)
                await manager.broadcast(
                    room_code,
                    {
                        "type": "ROOM_UPDATED",
                        "room": room.model_dump(),
                        "event": f"{role} locked in prompt",
                    },
                )

                # Check if all 3 players are ready!
                if room_mgr.all_ready(room_code):
                    logger.info(f"All 3 players locked in for room '{room_code}'. Initiating relay execution...")
                    asyncio.create_task(
                        execute_multiplayer_relay(room_code, manager.broadcast)
                    )

            elif msg_type == "UNLOCK":
                room = room_mgr.unlock_prompt(room_code, role)
                await manager.broadcast(
                    room_code,
                    {
                        "type": "ROOM_UPDATED",
                        "room": room.model_dump(),
                        "event": f"{role} unlocked prompt",
                    },
                )

            elif msg_type == "TYPING":
                # Broadcast typing notification to peers
                is_typing = bool(msg.get("is_typing", True))
                await manager.broadcast(
                    room_code,
                    {
                        "type": "PLAYER_TYPING",
                        "role": role,
                        "is_typing": is_typing,
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(room_code, role, websocket)
        room_mgr.set_connection_status(room_code, role, False)
        # Broadcast updated room state
        current_room = room_mgr.get_room(room_code)
        if current_room:
            await manager.broadcast(
                room_code,
                {
                    "type": "ROOM_UPDATED",
                    "room": current_room.model_dump(),
                    "event": f"{role} disconnected",
                },
            )
    except Exception as e:
        logger.error(f"WebSocket error in room {room_code}: {e}")
        manager.disconnect(room_code, role, websocket)
