import React from "react";
import { Trophy, Settings, ShieldAlert } from "lucide-react";
import { useGameStore } from "../store/useGameStore";

export function Header() {
  const {
    teamName,
    scenario,
    currentStep,
    setIsLeaderboardOpen,
    setIsAdminOpen,
  } = useGameStore();

  const isMatchActive = currentStep !== "welcome" && teamName;

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 py-3.5 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-bold text-lg">
          ⚡
        </div>
        <div>
          <h1 className="text-base sm:text-lg font-bold text-slate-100 font-serif tracking-wide leading-tight">
            PROMPT RELAY
          </h1>
          <p className="text-[11px] text-slate-400 font-mono">
            3-Agent Sequential Prompt Engineering Challenge
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {isMatchActive && (
          <div className="hidden sm:flex items-center gap-2.5 text-xs font-mono">
            <div className="bg-slate-800/80 border border-slate-700/60 px-3 py-1 rounded-full flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-400">Team:</span>
              <span className="text-amber-300 font-bold">{teamName}</span>
            </div>
            {scenario && (
              <div className="bg-slate-800/80 border border-slate-700/60 px-3 py-1 rounded-full text-slate-300 font-medium truncate max-w-[200px]">
                {scenario.title}
              </div>
            )}
          </div>
        )}

        <button
          onClick={() => setIsLeaderboardOpen(true)}
          className="px-3.5 py-1.5 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/70 text-xs font-mono font-semibold text-amber-400 flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
        >
          <Trophy className="w-3.5 h-3.5" />
          <span>Leaderboard</span>
        </button>

        <button
          onClick={() => setIsAdminOpen(true)}
          className="px-3.5 py-1.5 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/70 text-xs font-mono font-semibold text-slate-300 hover:text-slate-100 flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
        >
          <Settings className="w-3.5 h-3.5" />
          <span>Organizer</span>
        </button>
      </div>
    </header>
  );
}
