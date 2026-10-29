import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  Plane,
  Landmark,
  CheckCircle2,
  Users,
  Laptop,
  Wifi,
  Sparkles,
  KeyRound,
  Shield,
} from "lucide-react";
import { api } from "../api/client";
import { useGameStore } from "../store/useGameStore";
import { useMultiplayerStore } from "../store/useMultiplayerStore";

export function WelcomeScreen() {
  const { startGame, isLoading: soloLoading } = useGameStore();
  const {
    createRoom,
    joinRoom,
    fetchServerInfo,
    serverInfo,
    isLoading: mpLoading,
    error: mpError,
    clearError,
  } = useMultiplayerStore();

  const [mode, setMode] = useState("multiplayer"); // "multiplayer" or "solo"
  const [multiplayerTab, setMultiplayerTab] = useState("create"); // "create" or "join"

  // Host state
  const [teamName, setTeamName] = useState("");
  const [hostPlayerName, setHostPlayerName] = useState("Player 1");
  const [hostRole, setHostRole] = useState("player_1");
  const [selectedScenarioId, setSelectedScenarioId] = useState("scenario_01_airport_crisis");

  // Join state
  const [joinRoomCode, setJoinRoomCode] = useState("");
  const [joinPlayerName, setJoinPlayerName] = useState("Player 2");
  const [joinRole, setJoinRole] = useState("player_2");

  const [scenarios, setScenarios] = useState([]);

  useEffect(() => {
    // 1. Load available scenarios
    api
      .getScenarios()
      .then((list) => {
        setScenarios(list);
        const airport = list.find((s) => s.id === "scenario_01_airport_crisis");
        if (airport) setSelectedScenarioId(airport.id);
        else if (list.length > 0) setSelectedScenarioId(list[0].id);
      })
      .catch(console.error);

    // 2. Discover local LAN IP
    fetchServerInfo();

    // 3. Auto-detect ?room=CODE in URL query params
    const urlParams = new URLSearchParams(window.location.search);
    const roomParam = urlParams.get("room");
    if (roomParam) {
      const code = roomParam.toUpperCase();
      setMode("multiplayer");
      setMultiplayerTab("join");
      setJoinRoomCode(code);
      api
        .getRoom(code)
        .then((data) => {
          if (data?.room?.slots) {
            const slots = data.room.slots;
            if (!slots.player_2) setJoinRole("player_2");
            else if (!slots.player_3) setJoinRole("player_3");
            else if (!slots.player_1) setJoinRole("player_1");
          }
        })
        .catch(() => {});
    }
  }, [fetchServerInfo]);

  // Host: Create Room
  const handleCreateRoom = async (e) => {
    e.preventDefault();
    if (!teamName.trim()) {
      alert("Please enter a squad/team name.");
      return;
    }
    try {
      await createRoom({
        teamName,
        scenarioId: selectedScenarioId,
        playerName: hostPlayerName.trim() || "Host",
        role: hostRole,
      });
    } catch (err) {
      alert(err.message);
    }
  };

  // Teammate: Join Room
  const handleJoinRoom = async (e) => {
    e.preventDefault();
    if (!joinRoomCode.trim()) {
      alert("Please enter a 4-letter Room Code.");
      return;
    }
    try {
      await joinRoom({
        roomCode: joinRoomCode.trim(),
        role: joinRole,
        playerName: joinPlayerName.trim() || `Player ${joinRole.slice(-1)}`,
      });
    } catch (err) {
      alert(err.message);
    }
  };

  // Solo Hotseat Start
  const handleSoloStart = (e) => {
    e.preventDefault();
    if (!teamName.trim()) {
      alert("Please enter a team name.");
      return;
    }
    startGame(teamName, selectedScenarioId);
  };

  return (
    <section className="space-y-8 animate-fade-in max-w-4xl mx-auto w-full py-4 px-4">
      {/* Title & Introduction */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono font-semibold tracking-wider uppercase">
          <Sparkles className="w-3.5 h-3.5" />
          <span>3-Agent Prompt Engineering Relay Challenge</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 font-serif tracking-tight">
          Orchestrate 3 Specialized AI Agents in a Relay
        </h2>
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
          Teams of 3 prompt engineers take turns crafting instructions. The output of Agent 1
          feeds Agent 2, whose output feeds Agent 3. Score is evaluated on individual prompt engineering
          quality (60 pts) and final case accuracy (40 pts).
        </p>
      </div>

      {/* Mode Switcher: 3-Laptop Wi-Fi Room vs Single Laptop Hotseat */}
      <div className="flex justify-center">
        <div className="p-1 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-1 text-xs font-mono">
          <button
            type="button"
            onClick={() => setMode("multiplayer")}
            className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
              mode === "multiplayer"
                ? "bg-blue-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Wifi className="w-4 h-4" />
            <span>💻 3-Laptop Team Room (Same Wi-Fi)</span>
          </button>
          <button
            type="button"
            onClick={() => setMode("solo")}
            className={`px-4 py-2 rounded-xl transition flex items-center gap-2 font-bold cursor-pointer ${
              mode === "solo"
                ? "bg-blue-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Laptop className="w-4 h-4" />
            <span>🖥️ Single Laptop (Hotseat Mode)</span>
          </button>
        </div>
      </div>

      {/* Mode A: 3-Laptop Team Room (Same Wi-Fi) */}
      {mode === "multiplayer" && (
        <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
          {/* Sub-tabs: Host a Room vs Join a Room */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setMultiplayerTab("create")}
                className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition cursor-pointer ${
                  multiplayerTab === "create"
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                1. Host / Create Room (Laptop 1)
              </button>
              <button
                type="button"
                onClick={() => setMultiplayerTab("join")}
                className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition cursor-pointer ${
                  multiplayerTab === "join"
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                2. Join Room on Wi-Fi (Laptops 2 & 3)
              </button>
            </div>

            {serverInfo?.local_ip && (
              <span className="hidden sm:inline text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-2.5 py-1 rounded-lg">
                Wi-Fi IP: {serverInfo.local_ip}:8000
              </span>
            )}
          </div>

          {/* Tab 1: Host Form */}
          {multiplayerTab === "create" && (
            <form onSubmit={handleCreateRoom} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
                    Squad / Team Name
                  </label>
                  <input
                    type="text"
                    required
                    value={teamName}
                    onChange={(e) => setTeamName(e.target.value)}
                    placeholder="e.g. Baker Street Trio or SkyWays Response"
                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400 text-sm font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
                    Your Name (Host Laptop)
                  </label>
                  <input
                    type="text"
                    required
                    value={hostPlayerName}
                    onChange={(e) => setHostPlayerName(e.target.value)}
                    placeholder="e.g. Alice"
                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400 text-sm font-mono"
                  />
                </div>
              </div>

              {/* Host Seat Selection */}
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
                  Select Your Seat on This Laptop:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => setHostRole("player_1")}
                    className={`p-3 rounded-xl border text-left font-mono text-xs transition cursor-pointer ${
                      hostRole === "player_1"
                        ? "bg-blue-950/40 border-blue-400 text-blue-200"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span className="font-bold block text-slate-200">Seat 1: Player 1</span>
                    <span className="text-[11px] text-slate-400">Evidence Extractor</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setHostRole("player_2")}
                    className={`p-3 rounded-xl border text-left font-mono text-xs transition cursor-pointer ${
                      hostRole === "player_2"
                        ? "bg-purple-950/40 border-purple-400 text-purple-200"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span className="font-bold block text-slate-200">Seat 2: Player 2</span>
                    <span className="text-[11px] text-slate-400">Timeline Reconstructor</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setHostRole("player_3")}
                    className={`p-3 rounded-xl border text-left font-mono text-xs transition cursor-pointer ${
                      hostRole === "player_3"
                        ? "bg-emerald-950/40 border-emerald-400 text-emerald-200"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span className="font-bold block text-slate-200">Seat 3: Player 3</span>
                    <span className="text-[11px] text-slate-400">Logic Solver</span>
                  </button>
                </div>
              </div>

              {/* Case Selection Cards */}
              <div className="space-y-2">
                <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider">
                  Select Visual Case Investigation:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Airport Crisis */}
                  <div
                    onClick={() => setSelectedScenarioId("scenario_01_airport_crisis")}
                    className={`cursor-pointer rounded-2xl p-4 transition space-y-2 border ${
                      selectedScenarioId === "scenario_01_airport_crisis"
                        ? "border-2 border-blue-500 bg-blue-950/30 shadow-md shadow-blue-500/15"
                        : "border-slate-800 bg-slate-950/70 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[10px] font-bold">
                        CASE 01 • AIRPORT CRISIS
                      </span>
                      <Plane className="w-4 h-4 text-blue-400" />
                    </div>
                    <h4 className="font-bold text-slate-100 text-sm">
                      Flight SW 472: The Diamond Baggage Swap
                    </h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Terminal CCTV feeds, baggage scales, apron cargo diversion, and duplicate tag audits.
                    </p>
                  </div>

                  {/* Museum Heist */}
                  <div
                    onClick={() => setSelectedScenarioId("scenario_05_museum_heist")}
                    className={`cursor-pointer rounded-2xl p-4 transition space-y-2 border ${
                      selectedScenarioId === "scenario_05_museum_heist"
                        ? "border-2 border-amber-500 bg-amber-950/30 shadow-md shadow-amber-500/15"
                        : "border-slate-800 bg-slate-950/70 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                        CASE 02 • MUSEUM HEIST
                      </span>
                      <Landmark className="w-4 h-4 text-amber-400" />
                    </div>
                    <h4 className="font-bold text-slate-100 text-sm">
                      The Celestial Madonna: Museum Heist
                    </h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Gallery & basement CCTV, SCADA power grid telemetry, and conservation spectrometry.
                    </p>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={mpLoading}
                className="w-full py-4 px-6 rounded-xl bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold text-sm transition transform active:scale-98 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <span>Create Wi-Fi Team Room</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Tab 2: Join Form */}
          {multiplayerTab === "join" && (
            <form onSubmit={handleJoinRoom} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
                    Enter 4-Letter Room Code
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={joinRoomCode}
                    onChange={(e) => setJoinRoomCode(e.target.value.toUpperCase())}
                    placeholder="e.g. SW47"
                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 font-mono text-lg font-bold tracking-widest focus:outline-none focus:border-blue-400 uppercase"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
                    Your Name
                  </label>
                  <input
                    type="text"
                    required
                    value={joinPlayerName}
                    onChange={(e) => setJoinPlayerName(e.target.value)}
                    placeholder="e.g. Bob"
                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400 text-sm font-mono"
                  />
                </div>
              </div>

              {/* Join Seat Selection */}
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
                  Claim Your Role / Seat for This Laptop:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => setJoinRole("player_1")}
                    className={`p-3 rounded-xl border text-left font-mono text-xs transition cursor-pointer ${
                      joinRole === "player_1"
                        ? "bg-blue-950/40 border-blue-400 text-blue-200"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span className="font-bold block text-slate-200">Seat 1: Player 1</span>
                    <span className="text-[11px] text-slate-400">Evidence Extractor</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setJoinRole("player_2")}
                    className={`p-3 rounded-xl border text-left font-mono text-xs transition cursor-pointer ${
                      joinRole === "player_2"
                        ? "bg-purple-950/40 border-purple-400 text-purple-200"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span className="font-bold block text-slate-200">Seat 2: Player 2</span>
                    <span className="text-[11px] text-slate-400">Timeline Reconstructor</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setJoinRole("player_3")}
                    className={`p-3 rounded-xl border text-left font-mono text-xs transition cursor-pointer ${
                      joinRole === "player_3"
                        ? "bg-emerald-950/40 border-emerald-400 text-emerald-200"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <span className="font-bold block text-slate-200">Seat 3: Player 3</span>
                    <span className="text-[11px] text-slate-400">Logic Solver</span>
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={mpLoading || !joinRoomCode.trim()}
                className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 text-slate-950 font-extrabold text-sm transition transform active:scale-98 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <span>Connect to Wi-Fi Room</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}
        </div>
      )}

      {/* Mode B: Single Laptop Hotseat Mode */}
      {mode === "solo" && (
        <form
          onSubmit={handleSoloStart}
          className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6"
        >
          <div>
            <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
              Team Name (3-Person Prompt Squad)
            </label>
            <input
              type="text"
              required
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              placeholder="e.g. Flight 472 Response Unit"
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400 text-sm font-mono"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider">
              Select Visual Investigation Case:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div
                onClick={() => setSelectedScenarioId("scenario_01_airport_crisis")}
                className={`cursor-pointer rounded-2xl p-4 transition space-y-2 border ${
                  selectedScenarioId === "scenario_01_airport_crisis"
                    ? "border-2 border-blue-500 bg-blue-950/30"
                    : "border-slate-800 bg-slate-950/70"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-[10px] font-bold">
                    CASE 01 • AIRPORT CRISIS
                  </span>
                  <Plane className="w-4 h-4 text-blue-400" />
                </div>
                <h4 className="font-bold text-slate-100 text-sm">
                  Flight SW 472: The Diamond Baggage Swap
                </h4>
              </div>

              <div
                onClick={() => setSelectedScenarioId("scenario_05_museum_heist")}
                className={`cursor-pointer rounded-2xl p-4 transition space-y-2 border ${
                  selectedScenarioId === "scenario_05_museum_heist"
                    ? "border-2 border-amber-500 bg-amber-950/30"
                    : "border-slate-800 bg-slate-950/70"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
                    CASE 02 • MUSEUM HEIST
                  </span>
                  <Landmark className="w-4 h-4 text-amber-400" />
                </div>
                <h4 className="font-bold text-slate-100 text-sm">
                  The Celestial Madonna: Museum Heist
                </h4>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={soloLoading}
            className="w-full py-4 px-6 rounded-xl bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold text-sm transition transform active:scale-98 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <span>Launch Solo Hotseat Operation</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      )}
    </section>
  );
}
