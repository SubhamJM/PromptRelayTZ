import React, { useState } from "react";
import { Network, MapPin, Lock, CheckCircle2, Route, Clock, GitMerge, AlertTriangle, Eye } from "lucide-react";
import { EvidenceViewer } from "../../components/EvidenceViewer";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";

export function Player2Workspace() {
  const { scenario, myPrompt, setMyPrompt, isLockedIn, lockInPrompt, unlockPrompt, sendTyping } =
    useMultiplayerStore();

  const isMuseum = scenario?.id === "scenario_05_museum_heist";
  const [activeTab, setActiveTab] = useState("evidence"); // "evidence" | "layout"
  const [charCount, setCharCount] = useState(myPrompt.length);
  const words = myPrompt.trim().split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const MAX_WORDS = 40;

  const handleTextChange = (e) => {
    const val = e.target.value;
    setMyPrompt(val);
    setCharCount(val.length);
    sendTyping(val.length > 0);
  };

  const handleLockIn = (e) => {
    e.preventDefault();
    if (!myPrompt.trim()) {
      alert("Please enter your prompt for Agent 2 before locking in.");
      return;
    }
    if (wordCount > MAX_WORDS) {
      alert(`Prompt exceeds limit of ${MAX_WORDS} words (currently ${wordCount} words).`);
      return;
    }
    lockInPrompt();
  };

  const evidenceCount = scenario?.evidence_items?.length || 10;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      {/* Left 7 Columns: Evidence Feeds & Layout Canvas */}
      <div className="lg:col-span-7 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {activeTab === "evidence" ? (
              <Eye className="w-5 h-5 text-purple-400" />
            ) : (
              <Network className="w-5 h-5 text-purple-400" />
            )}
            <h2 className="font-bold text-slate-100 text-base font-serif">
              {activeTab === "evidence"
                ? "Visual Evidence & Surveillance Console"
                : "Facility Layout & Chronological Staging Canvas"}
            </h2>
          </div>
          <span className="text-[11px] font-mono text-purple-400 bg-purple-500/10 border border-purple-500/30 px-2 py-0.5 rounded">
            Laptop 2 • Player 2
          </span>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            type="button"
            onClick={() => setActiveTab("evidence")}
            className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === "evidence"
                ? "bg-purple-500 text-slate-950 shadow-lg shadow-purple-500/20"
                : "bg-slate-900/90 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Surveillance Feeds</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded font-extrabold ${
                activeTab === "evidence"
                  ? "bg-slate-950/20 text-slate-950"
                  : "bg-purple-950/60 text-purple-300"
              }`}
            >
              {evidenceCount} Feeds
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("layout")}
            className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === "layout"
                ? "bg-purple-500 text-slate-950 shadow-lg shadow-purple-500/20"
                : "bg-slate-900/90 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Facility Blueprint & Staging</span>
          </button>
        </div>

        {activeTab === "evidence" ? (
          <EvidenceViewer isStep2={true} />
        ) : (
          /* Spatial Diagram / Blueprint Card */
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-purple-400" />
                <h3 className="font-bold text-slate-200 text-xs font-mono uppercase tracking-wider">
                  {isMuseum ? "Wing C & Basement Blueprint Layout" : "Terminal 1 Concourse B Spatial Map"}
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                Reference Blueprint
              </span>
            </div>

            {/* Blueprint Image Preview */}
            <div className="rounded-xl overflow-hidden border border-purple-500/30 bg-slate-950 flex items-center justify-center p-2">
              <img
                src={
                  isMuseum
                    ? "/images_for_museum/6.png"
                    : "/image_data/7.png"
                }
                alt="Floor Plan"
                className="max-h-64 object-contain rounded"
              />
            </div>

            {/* Chronological Transit Vector Guide */}
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1">
                <span className="text-purple-300 font-bold block text-[10px]">1. FIRST (Origin)</span>
                <p className="text-slate-300 text-[11px]">
                  {isMuseum
                    ? "21:15 Gala Reception at Gallery 4 with authentic framed Madonna."
                    : "08:14 Check-in at Island A; blue suitcase tagged & dispatched."}
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1">
                <span className="text-purple-300 font-bold block text-[10px]">2. NEXT (Transit)</span>
                <p className="text-slate-300 text-[11px]">
                  {isMuseum
                    ? "23:40:42 Breaker B-04 trip ➔ 90s blackout ➔ canvas tube moved down Stairwell C1."
                    : "08:16:05 Supervisor duplicate tag reprint ➔ 08:46 decoy bag drop at B07 ➔ 08:47:45 Door B-Staff-03 badge swipe."}
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-purple-950/20 border border-purple-500/30 space-y-1">
                <span className="text-purple-300 font-bold block text-[10px]">3. LAST (Drop Point & Diversion)</span>
                <p className="text-slate-300 text-[11px]">
                  {isMuseum
                    ? "23:48 Basement Locker 14 search yields card CONSV-408 and token C-408."
                    : "08:49 Officer R. Nair logs 12.1 kg ballast decoy at B07; 09:02 genuine 18.4 kg diamond bag diverted to Cart #MC-08."}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right 5 Columns: Prompt Crafting & Directives */}
      <div className="lg:col-span-5 space-y-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-purple-400 font-bold uppercase tracking-wider block">
                Player 2 Directive
              </span>
              <h3 className="font-bold text-slate-100 text-sm">
                Direct Agent 2: Incident Reconstructor
              </h3>
            </div>
            <div
              className={`px-2.5 py-1 rounded-full text-[11px] font-mono font-bold border flex items-center gap-1.5 ${
                isLockedIn
                  ? "bg-emerald-950/80 border-emerald-500 text-emerald-300"
                  : "bg-purple-950/40 border-purple-500/30 text-purple-300"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isLockedIn ? "bg-emerald-400" : "bg-purple-400 animate-pulse"
                }`}
              />
              <span>{isLockedIn ? "Locked In ✅" : "Drafting"}</span>
            </div>
          </div>

          {/* Strategy Tips */}
          <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/20 text-xs text-slate-300 space-y-1.5 font-sans leading-relaxed">
            <span className="font-bold text-purple-300 font-mono text-[11px] block">
              💡 Key Objectives for Player 2:
            </span>
            <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
              <li>Define role: <em>Timeline & Incident Reconstructor</em></li>
              <li>Order events chronologically: what happened <strong>first</strong>, <strong>next</strong>, and <strong>last</strong></li>
              <li>Trace suspect & object transit vectors and connect causal dependencies</li>
              <li>Keep uncertain sightings separate; <strong>maintain strict neutrality</strong></li>
            </ul>
          </div>

          {/* Form */}
          <form onSubmit={handleLockIn} className="space-y-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <label>Your Instruction Prompt for Agent 2:</label>
              <span
                className={`font-semibold ${
                  wordCount > MAX_WORDS ? "text-rose-400 font-bold" : "text-slate-400"
                }`}
              >
                {wordCount} / {MAX_WORDS} words
              </span>
            </div>

            <textarea
              rows={8}
              disabled={isLockedIn}
              value={myPrompt}
              onChange={handleTextChange}
              placeholder={
                isMuseum
                  ? "e.g. Role: Timeline & Incident Reconstructor. Order all facts chronologically from 21:15 to 23:48. Trace suspect movements, connect Breaker B-04 blackout to Locker 14, and highlight alibi gaps. Maintain neutrality without naming culprits."
                  : "e.g. Role: Timeline & Incident Reconstructor. Reconstruct events chronologically from 08:14 to 09:02. Trace Daniel Kim's 18.4 kg checked bag, the duplicate tag reprint, Gate B07 decoy, and Cart #MC-08 diversion. Maintain neutrality."
              }
              className={`w-full p-3.5 rounded-xl bg-slate-950 border font-mono text-xs text-slate-100 placeholder-slate-600 focus:outline-none transition leading-relaxed ${
                isLockedIn
                  ? "border-emerald-500/40 bg-emerald-950/10 opacity-80"
                  : wordCount > MAX_WORDS
                  ? "border-rose-500 focus:ring-1 focus:ring-rose-500"
                  : "border-slate-700 focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
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
                className="w-full py-3.5 px-4 rounded-xl bg-purple-500 hover:bg-purple-400 disabled:opacity-40 text-slate-950 font-bold text-xs font-mono transition flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-purple-500/20 active:scale-98"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Lock In Reconstruction Prompt</span>
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
