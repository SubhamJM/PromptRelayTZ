import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.room_manager import get_room_manager

client = TestClient(app)


def test_network_server_info():
    res = client.get("/api/rooms/network/server-info")
    assert res.status_code == 200
    data = res.json()
    assert "local_ip" in data
    assert data["port"] == 8000
    assert "base_url" in data


def test_create_and_join_multiplayer_room():
    # 1. Create room
    create_payload = {
        "team_name": "TrioDetectives",
        "scenario_id": "scenario_01_airport_crisis",
        "host_player_name": "Alice",
        "host_role": "player_1",
        "round_duration_seconds": 300,
    }
    create_res = client.post("/api/rooms/create", json=create_payload)
    assert create_res.status_code == 200
    room_data = create_res.json()
    room_code = room_data["room_code"]
    assert len(room_code) == 4
    assert "local_ip" in room_data

    # Check slot 1 assigned to Alice
    slots = room_data["room"]["slots"]
    assert slots["player_1"]["player_name"] == "Alice"
    assert slots["player_2"] is None
    assert slots["player_3"] is None

    # 2. Join Player 2 (Bob)
    join_p2_res = client.post(
        "/api/rooms/join",
        json={"room_code": room_code, "player_name": "Bob", "role": "player_2"},
    )
    assert join_p2_res.status_code == 200
    p2_data = join_p2_res.json()
    assert p2_data["room"]["slots"]["player_2"]["player_name"] == "Bob"

    # 3. Join Player 3 (Charlie)
    join_p3_res = client.post(
        "/api/rooms/join",
        json={"room_code": room_code, "player_name": "Charlie", "role": "player_3"},
    )
    assert join_p3_res.status_code == 200
    p3_data = join_p3_res.json()
    assert p3_data["room"]["slots"]["player_3"]["player_name"] == "Charlie"

    # 4. Attempt to join an already occupied slot
    conflict_res = client.post(
        "/api/rooms/join",
        json={"room_code": room_code, "player_name": "Imposter", "role": "player_2"},
    )
    assert conflict_res.status_code == 400
    assert "already taken" in conflict_res.json()["detail"].lower()

    # 5. Lock in prompts for P1 and P2
    lock_p1 = client.post(
        f"/api/rooms/{room_code}/lock-in",
        json={"room_code": room_code, "role": "player_1", "prompt": "Extract airport evidence."},
    )
    assert lock_p1.status_code == 200
    assert lock_p1.json()["room"]["slots"]["player_1"]["is_ready"] is True

    lock_p2 = client.post(
        f"/api/rooms/{room_code}/lock-in",
        json={"room_code": room_code, "role": "player_2", "prompt": "Synthesize chronological sequence."},
    )
    assert lock_p2.status_code == 200
    assert lock_p2.json()["room"]["slots"]["player_2"]["is_ready"] is True


def test_websocket_room_lifecycle():
    room_mgr = get_room_manager()
    room = room_mgr.create_room(
        team_name="WebsocketSquad",
        scenario_id="scenario_05_museum_heist",
        host_player_name="LeadHost",
        host_role="player_1",
    )
    code = room.room_code

    with client.websocket_connect(f"/ws/rooms/{code}/player_1") as ws1:
        # Initial message received
        init_data = ws1.receive_json()
        assert init_data["type"] == "ROOM_UPDATED"
        assert init_data["room"]["room_code"] == code

        # Send Ping
        ws1.send_json({"type": "PING"})
        pong = ws1.receive_json()
        assert pong["type"] == "PONG"


@pytest.mark.asyncio
async def test_full_multiplayer_relay_execution():
    from backend.app.services.relay_runner import execute_multiplayer_relay

    room_mgr = get_room_manager()
    room = room_mgr.create_room(
        team_name="SimultaneousSquad",
        scenario_id="scenario_01_airport_crisis",
        host_player_name="PlayerOne",
        host_role="player_1",
    )
    code = room.room_code

    # Join P2 and P3
    room_mgr.join_slot(code, "player_2", "PlayerTwo")
    room_mgr.join_slot(code, "player_3", "PlayerThree")

    # Lock in all 3 prompts
    p1 = "Role: Evidence Extractor. Identify key people Daniel Kim, times 08:14, locations Gate B07, and blue luggage."
    p2 = "Role: Incident Reconstructor. Chronologically sequence events first, next, and last. Trace the unattended bag."
    p3 = "Role: Logic Decision Solver. Evaluate rules Rule SEC-101 and Rule OPS-204 to hold Flight SW 472. Output JSON."

    room_mgr.lock_in_prompt(code, "player_1", p1)
    room_mgr.lock_in_prompt(code, "player_2", p2)
    room_mgr.lock_in_prompt(code, "player_3", p3)

    # Verify all ready was reached
    assert room_mgr.all_ready(code) is True

    broadcast_events = []

    async def mock_broadcast(r_code, event):
        broadcast_events.append(event)

    await execute_multiplayer_relay(code, mock_broadcast)

    assert room.status == "completed"
    assert room.a1_output != ""
    assert room.a2_output != ""
    assert room.a3_output != ""
    assert room.evaluation is not None
    event_types = [e["type"] for e in broadcast_events]
    assert "EXECUTION_STARTED" in event_types
    assert "MATCH_COMPLETED" in event_types


def test_invalid_room_and_unlock_flow():
    # Attempt to join non-existent room
    bad_join = client.post(
        "/api/rooms/join",
        json={"room_code": "ZZZZ", "player_name": "Ghost", "role": "player_1"},
    )
    assert bad_join.status_code == 400
    assert "does not exist" in bad_join.json()["detail"].lower()

    # Create room and test start prompting endpoint
    create_res = client.post(
        "/api/rooms/create",
        json={
            "team_name": "UnlockSquad",
            "scenario_id": "scenario_01_airport_crisis",
            "host_player_name": "HostP1",
            "host_role": "player_1",
        },
    )
    code = create_res.json()["room_code"]

    # Start prompting
    start_res = client.post(f"/api/rooms/{code}/start")
    assert start_res.status_code == 200
    assert start_res.json()["room"]["status"] == "prompting"

    # Lock in then unlock
    lock_res = client.post(
        f"/api/rooms/{code}/lock-in",
        json={"room_code": code, "role": "player_1", "prompt": "Drafting my prompt..."},
    )
    assert lock_res.status_code == 200
    assert lock_res.json()["room"]["slots"]["player_1"]["is_ready"] is True

    # Test unlock via room manager
    room_mgr = get_room_manager()
    unlocked_room = room_mgr.unlock_prompt(code, "player_1")
    assert unlocked_room.slots["player_1"].is_ready is False


def test_websocket_typing_and_unlock():
    room_mgr = get_room_manager()
    room = room_mgr.create_room(
        team_name="TypingSquad",
        scenario_id="scenario_05_museum_heist",
        host_player_name="P1Host",
        host_role="player_1",
    )
    code = room.room_code
    room_mgr.join_slot(code, "player_2", "P2Player")

    with client.websocket_connect(f"/ws/rooms/{code}/player_1") as ws1:
        # Read init message
        ws1.receive_json()

        with client.websocket_connect(f"/ws/rooms/{code}/player_2") as ws2:
            # P1 receives P2 join update
            p2_join_msg = ws1.receive_json()
            assert p2_join_msg["type"] == "ROOM_UPDATED"

            # P2 receives initial state
            ws2.receive_json()

            # P1 sends typing event
            ws1.send_json({"type": "TYPING", "is_typing": True})

            # P2 receives TYPING event
            typing_msg = ws2.receive_json()
            assert typing_msg["type"] == "PLAYER_TYPING"
            assert typing_msg["role"] == "player_1"
            assert typing_msg["is_typing"] is True

