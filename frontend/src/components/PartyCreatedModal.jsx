import React, { useState } from "react";
import {
  Sparkles,
  Check,
  Copy,
  Wifi,
  Users,
  X,
  ArrowRight,
  Shield,
  Laptop,
} from "lucide-react";
import { useMultiplayerStore } from "../store/useMultiplayerStore";
import { copyToClipboard } from "../utils/clipboard";

export function PartyCreatedModal() {
  const {
    showPartyCreatedModal,
    closePartyCreatedModal,
    teamName,
    roomCode,
    getJoinUrl,
    room,
  } = useMultiplayerStore();

  const [copied, setCopied] = useState(false);

  if (!showPartyCreatedModal || !roomCode) return null;

  const joinUrl = getJoinUrl();

  const handleCopy = async () => {
    const success = await copyToClipboard(joinUrl);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-blue-500/40 rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl relative space-y-6 text-center">
        {/* Close Button */}
        <button
          onClick={closePartyCreatedModal}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Badge & Title */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Party Created Successfully</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-100 font-serif">
            {teamName}
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Your Wi-Fi multiplayer room is live and ready for teammates.
          </p>
        </div>

        {/* 4-Letter Room Code */}
        <div className="py-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest block mb-1">
            4-Letter Room Code
          </span>
          <div className="inline-block text-3xl sm:text-4xl font-mono font-black tracking-widest px-6 py-2 rounded-2xl bg-slate-950 border-2 border-blue-500/40 text-blue-300 shadow-inner">
            {roomCode}
          </div>
        </div>

        {/* Same Wi-Fi Share Link Box */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4 text-left space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300">
            <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <Wifi className="w-4 h-4" />
              <span>Same Wi-Fi Share Link</span>
            </span>
            <span className="text-[10px] text-slate-500">Auto-joins this party</span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-700/80 font-mono text-xs text-blue-300 break-all select-all flex items-center justify-between gap-2">
            <span className="truncate">{joinUrl}</span>
          </div>

          {/* Big Prominent Copy Link Button */}
          <button
            onClick={handleCopy}
            className={`w-full py-3.5 px-4 rounded-xl font-mono font-bold text-sm transition flex items-center justify-center gap-2 cursor-pointer shadow-lg ${
              copied
                ? "bg-emerald-500 text-slate-950 shadow-emerald-500/25 ring-2 ring-emerald-400/50"
                : "bg-blue-500 hover:bg-blue-400 text-slate-950 shadow-blue-500/20 active:scale-98"
            }`}
          >
            {copied ? (
              <>
                <Check className="w-5 h-5 text-slate-950 stroke-[2.5]" />
                <span>Party Link Copied to Clipboard!</span>
              </>
            ) : (
              <>
                <Copy className="w-5 h-5 text-slate-950 stroke-[2.5]" />
                <span>Copy Party Link for Teammates</span>
              </>
            )}
          </button>
        </div>

        {/* Instructions */}
        <div className="text-left text-xs text-slate-400 font-mono space-y-1.5 bg-blue-950/20 border border-blue-500/20 rounded-xl p-3">
          <div className="flex items-start gap-2">
            <span className="text-blue-400 font-bold shrink-0">1.</span>
            <span>Send this link to Player 2 & 3 on laptops connected to the same Wi-Fi.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-blue-400 font-bold shrink-0">2.</span>
            <span>They open the link, enter their names, and claim Player 2 / Player 3 seats.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-blue-400 font-bold shrink-0">3.</span>
            <span>Once all 3 seats are filled, click "Begin Synchronized Mission" in the lobby!</span>
          </div>
        </div>

        {/* Enter Lobby Action */}
        <button
          onClick={closePartyCreatedModal}
          className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold transition flex items-center justify-center gap-2 cursor-pointer"
        >
          <span>Continue to Team Lobby</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
