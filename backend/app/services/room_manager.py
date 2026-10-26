import random
import socket
import string
from datetime import datetime, timezone
from typing import Dict, Optional

from backend.app.models.room import PlayerRole, PlayerSlot, RoomModel


def get_local_ip() -> str:
    """Discovers the local Wi-Fi / LAN IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an arbitrary public/broadcast IP without sending packets
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class RoomManager:
    """In-memory room registry for multiplayer simultaneous relay matches."""

    def __init__(self):
        self._rooms: Dict[str, RoomModel] = {}

    def generate_room_code(self) -> str:
        """Generates a memorable 4-letter uppercase code."""
        chars = string.ascii_uppercase + "23456789"
        while True:
            code = "".join(random.choices(chars, k=4))
            if code not in self._rooms:
                return code

    def create_room(
        self,
        team_name: str,
        scenario_id: str,
        host_player_name: str = "Player 1",
        host_role: PlayerRole = "player_1",
        round_duration_seconds: int = 420,
    ) -> RoomModel:
        room_code = self.generate_room_code()
        room = RoomModel(
            room_code=room_code,
            team_name=team_name.strip() or "Squad 472",
            scenario_id=scenario_id,
            round_duration_seconds=round_duration_seconds,
            status="lobby",
        )
        # Assign host to their chosen role
        room.slots[host_role] = PlayerSlot(
            role=host_role,
            player_name=host_player_name.strip() or "Host",
            is_connected=True,
            is_ready=False,
        )
        self._rooms[room_code] = room
        return room

    def get_room(self, room_code: str) -> Optional[RoomModel]:
        return self._rooms.get(room_code.upper().strip())

    def join_slot(
        self,
        room_code: str,
        role: PlayerRole,
        player_name: str,
    ) -> RoomModel:
        room = self.get_room(room_code)
        if not room:
            raise ValueError(f"Room '{room_code}' does not exist.")

        slot = room.slots.get(role)
        # If slot already taken by another active player
        if slot and slot.is_connected and slot.player_name.lower() != player_name.lower():
            raise ValueError(f"Slot '{role}' is already taken by {slot.player_name}.")

        room.slots[role] = PlayerSlot(
            role=role,
            player_name=player_name.strip() or f"Player {role[-1]}",
            is_connected=True,
            is_ready=False,
            prompt=slot.prompt if slot else "",
        )
        return room

    def set_connection_status(self, room_code: str, role: PlayerRole, is_connected: bool):
        room = self.get_room(room_code)
        if room and room.slots.get(role):
            room.slots[role].is_connected = is_connected

    def start_prompting(self, room_code: str) -> RoomModel:
        room = self.get_room(room_code)
        if not room:
            raise ValueError(f"Room '{room_code}' not found.")
        room.status = "prompting"
        room.started_prompting_at = datetime.now(timezone.utc).isoformat()
        return room

    def lock_in_prompt(self, room_code: str, role: PlayerRole, prompt: str) -> RoomModel:
        room = self.get_room(room_code)
        if not room:
            raise ValueError(f"Room '{room_code}' not found.")
        slot = room.slots.get(role)
        if not slot:
            raise ValueError(f"Slot '{role}' has not joined room '{room_code}'.")

        slot.prompt = prompt.strip()
        slot.is_ready = True
        slot.ready_at = datetime.now(timezone.utc).isoformat()
        return room

    def unlock_prompt(self, room_code: str, role: PlayerRole) -> RoomModel:
        room = self.get_room(room_code)
        if not room:
            raise ValueError(f"Room '{room_code}' not found.")
        slot = room.slots.get(role)
        if slot:
            slot.is_ready = False
        return room

    def all_ready(self, room_code: str) -> bool:
        room = self.get_room(room_code)
        if not room:
            return False
        # All 3 slots must be occupied and marked ready
        for role in ["player_1", "player_2", "player_3"]:
            slot = room.slots.get(role)
            if not slot or not slot.is_ready:
                return False
        return True


# Global RoomManager instance
_room_manager = RoomManager()


def get_room_manager() -> RoomManager:
    return _room_manager
