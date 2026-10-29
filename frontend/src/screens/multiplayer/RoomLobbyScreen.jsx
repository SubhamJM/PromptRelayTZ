import React, { useEffect, useState } from "react";
import {
  Users,
  Wifi,
  Copy,
  Check,
  Play,
  ArrowLeft,
  Shield,
  Eye,
  Network,
  Cpu,
  FileText,
  Sparkles,
} from "lucide-react";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";
import { useGameStore } from "../../store/useGameStore";
import { copyToClipboard } from "../../utils/clipboard";

export function RoomLobbyScreen() {
  const {
    roomCode,
    teamName,
    myRole,
    myPlayerName,
    room,
    scenario,
    serverInfo,
    fetchServerInfo,
    getJoinUrl,
    openPartyCreatedModal,
    joinRoom,
    startPrompting,
    disconnect,
  } = useMultiplayerStore();

  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchServerInfo();
  }, [fetchServerInfo]);

  const joinUrl = getJoinUrl();

  const handleCopyLink = async () => {
    const success = await copyToClipboard(joinUrl);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleClaimSlot = async (targetRole) => {
    if (myRole === targetRole) return;
    try {
      await joinRoom({
        roomCode,
        role: targetRole,
        playerName: myPlayerName || `Player ${targetRole.slice(-1)}`,
      });
    } catch (err) {
      alert(err.message);
    }
  };

  const handleStartRound = () => {
    startPrompting();
  };

  const slots = room?.slots || {};
  const isHost = myRole === "player_1"; // Host typically holds slot 1

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-8 animate-fade-in">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <button
          onClick={disconnect}
          className="flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-white transition cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Exit Lobby</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-mono text-slate-300">
            {window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
              ? "Online Relay Room Active"
              : "Wi-Fi Local Network Lobby Active"}
          </span>
        </div>
      </div>

      {/* Hero: Room Code & Wi-Fi Sharing Box */}
      <div className="bg-gradient-to-br from-blue-950/40 via-slate-900 to-slate-950 border border-blue-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl text-center space-y-4">
        <div className="inline-block px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs font-mono uppercase tracking-wider">
          Multi-Laptop Relay Room
        </div>

        <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 font-serif">
          {teamName}
        </h2>

        {/* Room Code Big Display */}
        <div className="flex flex-col items-center justify-center gap-2 py-2">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
            Room Join PIN
          </span>
          <div className="flex items-center justify-center gap-3">
            <span className="text-4xl sm:text-5xl font-mono font-black tracking-widest px-6 py-2 rounded-2xl bg-slate-950 border-2 border-blue-500/50 text-blue-300 shadow-lg shadow-blue-500/20">
              {roomCode}
            </span>
            <button
              onClick={handleCopyLink}
              className="p-3 rounded-2xl bg-blue-500 hover:bg-blue-400 text-slate-950 font-bold transition flex items-center justify-center cursor-pointer shadow-md"
              title="Copy Join Link"
            >
              {copied ? <Check className="w-5 h-5 text-slate-950" /> : <Copy className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Wi-Fi Direct Join Link for Teammates */}
        <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 max-w-xl mx-auto space-y-3 text-xs font-mono">
          <div className="flex items-center justify-between text-slate-300">
            <div className="flex items-center gap-2">
              <Wifi className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-slate-400">
                {window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
                  ? "Direct Party Share Link:"
                  : "Same Wi-Fi Join Link:"}
              </span>
            </div>
            <button
              onClick={openPartyCreatedModal}
              className="text-[11px] text-blue-400 hover:text-blue-300 underline cursor-pointer"
            >
              View Instructions
            </button>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-left text-slate-100 font-bold select-all truncate text-xs text-blue-300">
            {joinUrl || `http://<laptop-1-ip>:8000?room=${roomCode}`}
          </div>

          <button
            onClick={handleCopyLink}
            className={`w-full py-3 px-4 rounded-xl font-bold font-mono text-xs transition flex items-center justify-center gap-2 cursor-pointer shadow-md ${
              copied
                ? "bg-emerald-500 text-slate-950 ring-2 ring-emerald-400/50"
                : "bg-blue-500 hover:bg-blue-400 text-slate-950 active:scale-98"
            }`}
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-slate-950 stroke-[2.5]" />
                <span>Link Copied! Share with Player 2 & 3</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 text-slate-950 stroke-[2.5]" />
                <span>Copy Party Link for Teammates</span>
              </>
            )}
          </button>
        </div>
        <p className="text-[11px] text-slate-400 font-mono">
          Teammates on laptops 2 & 3: Connect to the same Wi-Fi, open this link, and select your seat below.
        </p>
      </div>

      {/* 3 Seat Allocation Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-mono uppercase tracking-wider text-slate-300 font-bold">
            Assigned Player Seats (3 Laptops)
          </h3>
          <span className="text-xs font-mono text-blue-400">
            Click an open seat to switch laptops
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Seat 1: Player 1 (Extractor) */}
          <div
            onClick={() => handleClaimSlot("player_1")}
            className={`rounded-2xl p-5 border transition flex flex-col justify-between space-y-4 cursor-pointer ${
              myRole === "player_1"
                ? "bg-blue-950/40 border-2 border-blue-400 shadow-xl shadow-blue-500/10 ring-2 ring-blue-500/30"
                : slots.player_1
                ? "bg-slate-900/90 border-slate-700"
                : "bg-slate-950/60 border-dashed border-slate-800 hover:border-blue-500/50"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-blue-400 font-mono font-bold text-xs">
                  1
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                    myRole === "player_1"
                      ? "bg-blue-500 text-slate-950 border-blue-400"
                      : slots.player_1
                      ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                      : "bg-slate-900 text-slate-400 border-slate-800"
                  }`}
                >
                  {myRole === "player_1"
                    ? "Your Laptop (Active)"
                    : slots.player_1
                    ? `Occupied: ${slots.player_1.player_name}`
                    : "Seat Available"}
                </span>
              </div>
              <h4 className="font-bold text-slate-100 text-sm flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-blue-400" />
                <span>Player 1: Evidence Extractor</span>
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Directs Agent 1 to mine CCTV feeds, OCR text, and timestamps while filtering peripheral noise.
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
              {slots.player_1 ? `Player: ${slots.player_1.player_name}` : "Click to sit here"}
            </div>
          </div>

          {/* Seat 2: Player 2 (Reconstructor) */}
          <div
            onClick={() => handleClaimSlot("player_2")}
            className={`rounded-2xl p-5 border transition flex flex-col justify-between space-y-4 cursor-pointer ${
              myRole === "player_2"
                ? "bg-purple-950/40 border-2 border-purple-400 shadow-xl shadow-purple-500/10 ring-2 ring-purple-500/30"
                : slots.player_2
                ? "bg-slate-900/90 border-slate-700"
                : "bg-slate-950/60 border-dashed border-slate-800 hover:border-purple-500/50"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="w-7 h-7 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400 font-mono font-bold text-xs">
                  2
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                    myRole === "player_2"
                      ? "bg-purple-500 text-slate-950 border-purple-400"
                      : slots.player_2
                      ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                      : "bg-slate-900 text-slate-400 border-slate-800"
                  }`}
                >
                  {myRole === "player_2"
                    ? "Your Laptop (Active)"
                    : slots.player_2
                    ? `Occupied: ${slots.player_2.player_name}`
                    : "Seat Available"}
                </span>
              </div>
              <h4 className="font-bold text-slate-100 text-sm flex items-center gap-1.5">
                <Network className="w-4 h-4 text-purple-400" />
                <span>Player 2: Reconstructor</span>
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Directs Agent 2 to assemble the strict chronological sequence (First, Next, Last) and causal dependencies.
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
              {slots.player_2 ? `Player: ${slots.player_2.player_name}` : "Click to sit here"}
            </div>
          </div>

          {/* Seat 3: Player 3 (Solver) */}
          <div
            onClick={() => handleClaimSlot("player_3")}
            className={`rounded-2xl p-5 border transition flex flex-col justify-between space-y-4 cursor-pointer ${
              myRole === "player_3"
                ? "bg-emerald-950/40 border-2 border-emerald-400 shadow-xl shadow-emerald-500/10 ring-2 ring-emerald-500/30"
                : slots.player_3
                ? "bg-slate-900/90 border-slate-700"
                : "bg-slate-950/60 border-dashed border-slate-800 hover:border-emerald-500/50"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-mono font-bold text-xs">
                  3
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                    myRole === "player_3"
                      ? "bg-emerald-500 text-slate-950 border-emerald-400"
                      : slots.player_3
                      ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                      : "bg-slate-900 text-slate-400 border-slate-800"
                  }`}
                >
                  {myRole === "player_3"
                    ? "Your Laptop (Active)"
                    : slots.player_3
                    ? `Occupied: ${slots.player_3.player_name}`
                    : "Seat Available"}
                </span>
              </div>
              <h4 className="font-bold text-slate-100 text-sm flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-emerald-400" />
                <span>Player 3: Logic Solver</span>
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Directs Agent 3 to evaluate governing rules and deduce the definitive operational resolution.
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
              {slots.player_3 ? `Player: ${slots.player_3.player_name}` : "Click to sit here"}
            </div>
          </div>
        </div>
      </div>

      {/* Start Round CTA */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 text-center space-y-4">
        <div className="space-y-1">
          <h4 className="font-bold text-slate-100 text-base">
            Ready to Begin the Simultaneous Relay Challenge?
          </h4>
          <p className="text-xs text-slate-400">
            Once started, all 3 laptops will begin writing their prompts simultaneously while coordinating verbally.
          </p>
        </div>

        <button
          onClick={handleStartRound}
          className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-400 hover:to-indigo-500 text-slate-950 font-extrabold text-sm transition transform active:scale-95 shadow-xl shadow-blue-500/20 flex items-center justify-center gap-2 mx-auto cursor-pointer"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>Launch Simultaneous Prompting Phase</span>
        </button>
      </div>
    </div>
  );
}
