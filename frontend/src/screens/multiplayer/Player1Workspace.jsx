import React, { useState } from "react";
import { Eye, Shield, Lock, CheckCircle2, ChevronRight, AlertCircle } from "lucide-react";
import { EvidenceViewer } from "../../components/EvidenceViewer";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";

export function Player1Workspace() {
  const { myPrompt, setMyPrompt, isLockedIn, lockInPrompt, unlockPrompt, sendTyping } =
    useMultiplayerStore();

  const [charCount, setCharCount] = useState(myPrompt.length);
  const words = myPrompt.trim().split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const MAX_WORDS = 80;
  const MAX_CHARS = 600;

  const handleTextChange = (e) => {
    const val = e.target.value;
    setMyPrompt(val);
    setCharCount(val.length);
    sendTyping(val.length > 0);
  };

  const handleLockIn = (e) => {
    e.preventDefault();
    if (!myPrompt.trim()) {
      alert("Please enter your prompt for Agent 1 before locking in.");
      return;
    }
    if (wordCount > MAX_WORDS) {
      alert(`Prompt exceeds limit of ${MAX_WORDS} words (currently ${wordCount} words).`);
      return;
    }
    if (charCount > MAX_CHARS) {
      alert(`Prompt exceeds limit of ${MAX_CHARS} characters (currently ${charCount} chars).`);
      return;
    }
    lockInPrompt();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Left 7 Columns: Visual Evidence Viewer */}
      <div className="lg:col-span-7 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-blue-400" />
            <h2 className="font-bold text-slate-100 text-base font-serif">
              Visual Evidence & Surveillance Console
            </h2>
          </div>
          <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/30 px-2 py-0.5 rounded">
            Laptop 1 • Player 1
          </span>
        </div>
        <EvidenceViewer />
      </div>

      {/* Right 5 Columns: Prompt Crafting & Directives */}
      <div className="lg:col-span-5 space-y-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-blue-400 font-bold uppercase tracking-wider block">
                Player 1 Directive
              </span>
              <h3 className="font-bold text-slate-100 text-sm">
                Direct Agent 1: Evidence Extractor
              </h3>
            </div>
            <div
              className={`px-2.5 py-1 rounded-full text-[11px] font-mono font-bold border flex items-center gap-1.5 ${
                isLockedIn
                  ? "bg-emerald-950/80 border-emerald-500 text-emerald-300"
                  : "bg-blue-950/40 border-blue-500/30 text-blue-300"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isLockedIn ? "bg-emerald-400" : "bg-blue-400 animate-pulse"
                }`}
              />
              <span>{isLockedIn ? "Locked In ✅" : "Drafting"}</span>
            </div>
          </div>

          {/* Prompt Form */}
          <form onSubmit={handleLockIn} className="space-y-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <label>Your Instruction Prompt for Agent 1:</label>
              <span
                className={`font-semibold ${
                  wordCount > MAX_WORDS ? "text-rose-400 font-bold" : "text-slate-400"
                }`}
              >
                {wordCount} / {MAX_WORDS} words
              </span>
            </div>

            <textarea
              rows={9}
              disabled={isLockedIn}
              value={myPrompt}
              onChange={handleTextChange}
              placeholder="Write your prompt to guide Agent 1 in extracting key facts, IDs, timestamps, and evidence from the dossier..."
              className={`w-full p-3.5 rounded-xl bg-slate-950 border font-mono text-xs text-slate-100 placeholder-slate-600 focus:outline-none transition leading-relaxed ${
                isLockedIn
                  ? "border-emerald-500/40 bg-emerald-950/10 opacity-80"
                  : wordCount > MAX_WORDS
                  ? "border-rose-500 focus:ring-1 focus:ring-rose-500"
                  : "border-slate-700 focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
              }`}
            />

            {isLockedIn ? (
              <div className="space-y-2">
                <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-mono flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Prompt Locked In! Waiting for teammates...</span>
                  </span>
                  <button
                    type="button"
                    onClick={unlockPrompt}
                    className="text-xs underline text-emerald-400 hover:text-white cursor-pointer ml-2"
                  >
                    Unlock & Edit
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="submit"
                disabled={wordCount === 0 || wordCount > MAX_WORDS}
                className="w-full py-3.5 px-4 rounded-xl bg-blue-500 hover:bg-blue-400 disabled:opacity-40 text-slate-950 font-bold text-xs font-mono transition flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-blue-500/20 active:scale-98"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Lock In Extraction Prompt</span>
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
