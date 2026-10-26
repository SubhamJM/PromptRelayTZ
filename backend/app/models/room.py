from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

PlayerRole = Literal["player_1", "player_2", "player_3"]
RoomStatus = Literal["lobby", "prompting", "executing", "completed"]


class PlayerSlot(BaseModel):
    role: PlayerRole
    player_name: str
    is_connected: bool = True
    prompt: str = ""
    is_ready: bool = False  # Locked in
    ready_at: Optional[str] = None


class RoomModel(BaseModel):
    room_code: str
    team_name: str
    scenario_id: str
    status: RoomStatus = "lobby"
    round_duration_seconds: int = 420  # 7-minute collaborative timer
    started_prompting_at: Optional[str] = None
    slots: Dict[str, Optional[PlayerSlot]] = Field(
        default_factory=lambda: {
            "player_1": None,
            "player_2": None,
            "player_3": None,
        }
    )
    current_step: int = 0  # 0=idle, 1=Agent 1, 2=Agent 2, 3=Agent 3, 4=Evaluated
    a1_output: Optional[str] = None
    a2_output: Optional[str] = None
    a3_output: Optional[str] = None
    final_verdict: Optional[dict] = None
    evaluation: Optional[dict] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CreateRoomRequest(BaseModel):
    team_name: str
    scenario_id: str
    host_player_name: str = "Host"
    host_role: PlayerRole = "player_1"
    round_duration_seconds: int = 420


class JoinRoomRequest(BaseModel):
    room_code: str
    player_name: str
    role: PlayerRole


class LockInRequest(BaseModel):
    room_code: str
    role: PlayerRole
    prompt: str
