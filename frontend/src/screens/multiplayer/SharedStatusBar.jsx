import React, { useState } from "react";
import { Users, Wifi, Copy, Check, ShieldCheck, Sparkles } from "lucide-react";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";
import { copyToClipboard } from "../../utils/clipboard";

export function SharedStatusBar() {
  const {
    roomCode,
    teamName,
    myRole,
    myPlayerName,
    room,
    wsConnected,
    isLockedIn,
    peerTyping,
    getJoinUrl,
  } = useMultiplayerStore();

  const [copied, setCopied] = useState(false);

  const handleCopyLink = async () => {
    const url = getJoinUrl();
    const success = await copyToClipboard(url);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const roleLabelMap = {
    player_1: "P1: Extractor",
    player_2: "P2: Reconstructor",
    player_3: "P3: Solver",
  };

  const slot1 = room?.slots?.player_1;
  const slot2 = room?.slots?.player_2;
  const slot3 = room?.slots?.player_3;

  return (
    <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur border-b border-slate-800 shadow-xl px-4 py-2.5">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        {/* Left: Room Badge & Team */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-blue-950/80 border border-blue-500/40 px-2.5 py-1 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-blue-300 font-bold tracking-wider">ROOM:</span>
            <span className="text-white font-extrabold text-sm">{roomCode}</span>
            <button
              onClick={handleCopyLink}
              title="Copy Join Link for Teammates on Wi-Fi"
              className="ml-1 text-blue-400 hover:text-white transition p-0.5 cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-1 text-slate-300">
            <span className="text-slate-500">Team:</span>
            <span className="font-bold text-amber-300">{teamName}</span>
          </div>
        </div>

        {/* Center: Synced Player Readiness Indicators */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Slot 1 */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] transition ${
              slot1?.is_ready
                ? "bg-emerald-950/60 border-emerald-500/50 text-emerald-300 font-bold"
                : slot1?.is_connected
                ? "bg-blue-950/40 border-blue-500/30 text-blue-300"
                : "bg-slate-950 border-slate-800 text-slate-500 opacity-60"
            }`}
          >
            <span>👁️ P1 (Extractor):</span>
            <span>
              {slot1?.is_ready
                ? "Ready ✅"
                : peerTyping.player_1
                ? "Typing ✍️"
                : slot1?.is_connected
                ? slot1.player_name
                : "Empty"}
            </span>
          </div>

          {/* Slot 2 */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] transition ${
              slot2?.is_ready
                ? "bg-emerald-950/60 border-emerald-500/50 text-emerald-300 font-bold"
                : slot2?.is_connected
                ? "bg-purple-950/40 border-purple-500/30 text-purple-300"
                : "bg-slate-950 border-slate-800 text-slate-500 opacity-60"
            }`}
          >
            <span>🕸️ P2 (Reconstructor):</span>
            <span>
              {slot2?.is_ready
                ? "Ready ✅"
                : peerTyping.player_2
                ? "Typing ✍️"
                : slot2?.is_connected
                ? slot2.player_name
                : "Empty"}
            </span>
          </div>

          {/* Slot 3 */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] transition ${
              slot3?.is_ready
                ? "bg-emerald-950/60 border-emerald-500/50 text-emerald-300 font-bold"
                : slot3?.is_connected
                ? "bg-amber-950/40 border-amber-500/30 text-amber-300"
                : "bg-slate-950 border-slate-800 text-slate-500 opacity-60"
            }`}
          >
            <span>⚙️ P3 (Solver):</span>
            <span>
              {slot3?.is_ready
                ? "Ready ✅"
                : peerTyping.player_3
                ? "Typing ✍️"
                : slot3?.is_connected
                ? slot3.player_name
                : "Empty"}
            </span>
          </div>
        </div>

        {/* Right: My Seat Info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200">
            <span className="text-slate-400">Seat:</span>
            <span className="font-bold text-blue-400">{roleLabelMap[myRole]}</span>
            <span
              className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-400" : "bg-rose-500"}`}
              title={wsConnected ? "Wi-Fi Synced" : "Disconnected"}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
