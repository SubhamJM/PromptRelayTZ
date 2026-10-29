import React, { useState } from "react";
import { Cpu, ShieldCheck, Lock, CheckCircle2, BookOpen, Code2, AlertCircle, Eye } from "lucide-react";
import { EvidenceViewer } from "../../components/EvidenceViewer";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";

export function Player3Workspace() {
  const { scenario, myPrompt, setMyPrompt, isLockedIn, lockInPrompt, unlockPrompt, sendTyping } =
    useMultiplayerStore();

  const isMuseum = scenario?.id === "scenario_05_museum_heist";
  const [activeTab, setActiveTab] = useState("evidence"); // "evidence" | "rules"
  const [charCount, setCharCount] = useState(myPrompt.length);
  const words = myPrompt.trim().split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const MAX_WORDS = 60;

  const handleTextChange = (e) => {
    const val = e.target.value;
    setMyPrompt(val);
    setCharCount(val.length);
    sendTyping(val.length > 0);
  };

  const handleLockIn = (e) => {
    e.preventDefault();
    if (!myPrompt.trim()) {
      alert("Please enter your prompt for Agent 3 before locking in.");
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
      {/* Left 7 Columns: Visual Evidence & Operational Rulebook Console */}
      <div className="lg:col-span-7 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {activeTab === "evidence" ? (
              <Eye className="w-5 h-5 text-emerald-400" />
            ) : (
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            )}
            <h2 className="font-bold text-slate-100 text-base font-serif">
              {activeTab === "evidence"
                ? "Visual Evidence & Surveillance Console"
                : "Governing Operational Protocols & Resolution Assistant"}
            </h2>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
            Laptop 3 • Player 3
          </span>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            type="button"
            onClick={() => setActiveTab("evidence")}
            className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === "evidence"
                ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20"
                : "bg-slate-900/90 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Surveillance Feeds</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded font-extrabold ${
                activeTab === "evidence"
                  ? "bg-slate-950/20 text-slate-950"
                  : "bg-emerald-950/60 text-emerald-300"
              }`}
            >
              {evidenceCount} Feeds
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("rules")}
            className={`px-3 py-1.5 rounded-xl font-mono text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === "rules"
                ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20"
                : "bg-slate-900/90 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Operational Rules & Resolution Checklist</span>
          </button>
        </div>

        {activeTab === "evidence" ? (
          <EvidenceViewer isStep3={true} />
        ) : (
          <div className="space-y-4">
            {/* Operational Rules Cards */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-2.5">
                <BookOpen className="w-4 h-4 text-emerald-400" />
                <h3 className="font-bold text-slate-200 text-xs font-mono uppercase tracking-wider">
                  Mandatory Operational Regulations
                </h3>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                {isMuseum ? (
                  <>
                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                      <span className="font-bold text-emerald-300">
                        Rule SEC-401 (Auxiliary Power Blackout Lockdown Protocol)
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        Upon intentional tripping of primary breaker circuits (Breaker B-04), all perimeter access points, emergency egress corridors, and loading docks undergo immediate automated lockdown.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                      <span className="font-bold text-emerald-300">
                        Rule ART-302 (Masterpiece Forgery & Physical Chain of Custody)
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        When an exhibited masterwork exhibits synthetic binders or pigment discrepancies indicating an in-situ forgery swap, all conservation staff possessing departmental keycards must surrender access tokens and undergo immediate detainment.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                      <span className="font-bold text-emerald-300">
                        Rule CLR-505 (Art Crime Evidence Recovery & Containment)
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        Security units must execute a targeted search of secondary drop points (Locker 14) and seal private vault/cloakroom depositories (Unit C-408).
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                      <span className="font-bold text-emerald-300">
                        Rule SEC-101 (Sterile Zone Unattended Baggage Protocol)
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        Any unattended baggage in passenger boarding gates must be immediately cordoned off and inspected by a certified K9 explosive detection unit.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                      <span className="font-bold text-emerald-300">
                        Rule BAGG-204 (Baggage Chain-of-Custody & Tag Duplicate Protocol)
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        Manual tag reprinting requires multi-factor supervisor authorization; any weight discrepancy over 1.0 kg between check-in and gate intercepts flags immediate chain-of-custody fraud.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                      <span className="font-bold text-emerald-300">
                        Rule OPS-204 (Pre-Departure Security Hold Protocol)
                      </span>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        No flight at a gate under an active security investigation, unattended baggage incident, or ramp cargo diversion may depart or board passengers.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Case Resolution Checklist */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-mono font-bold text-slate-200">
                    Final Case Resolution Checklist
                  </span>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded">
                  Plain English Supported
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-0.5">
                  <span className="text-emerald-400 font-bold">1. Culprit / Action:</span>
                  <p className="text-slate-400 text-[10px]">
                    {isMuseum ? "Identify Dr. Julian Vance & Marcus Thorne" : "Identify Tariq Malik (Senior Ramp Supervisor)"}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-0.5">
                  <span className="text-emerald-400 font-bold">2. Method & Mechanism:</span>
                  <p className="text-slate-400 text-[10px]">
                    {isMuseum ? "Breaker B-04 blackout synthetic forgery swap" : "Duplicate tag reprint, ballast decoy drop & Cart #MC-08 diversion"}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-0.5">
                  <span className="text-emerald-400 font-bold">3. Violated Rule:</span>
                  <p className="text-slate-400 text-[10px]">
                    {isMuseum ? "Rule SEC-401, Rule ART-302, Rule CLR-505" : "Rule SEC-101, Rule BAGG-204, Rule OPS-204"}
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 space-y-0.5">
                  <span className="text-emerald-400 font-bold">4. Key Evidence:</span>
                  <p className="text-slate-400 text-[10px]">
                    {isMuseum ? "Locker 14 token C-408, CONSV-408 badge, lab spectrometry" : "REPRINT-MGR-02 watermark, 6.3kg discrepancy, CAM 12 boots"}
                  </p>
                </div>
              </div>
              <p className="text-[10px] text-slate-500 font-mono">
                💡 Tip: Agent 3 handles all structured formatting automatically—just instruct in clear, natural English!
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Right 5 Columns: Prompt Crafting & Directives */}
      <div className="lg:col-span-5 space-y-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase tracking-wider block">
                Player 3 Directive
              </span>
              <h3 className="font-bold text-slate-100 text-sm">
                Direct Agent 3: Logic Decision Solver
              </h3>
            </div>
            <div
              className={`px-2.5 py-1 rounded-full text-[11px] font-mono font-bold border flex items-center gap-1.5 ${
                isLockedIn
                  ? "bg-emerald-950/80 border-emerald-500 text-emerald-300"
                  : "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isLockedIn ? "bg-emerald-400" : "bg-emerald-400 animate-pulse"
                }`}
              />
              <span>{isLockedIn ? "Locked In ✅" : "Drafting"}</span>
            </div>
          </div>

          {/* Strategy Tips */}
          <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/20 text-xs text-slate-300 space-y-1.5 font-sans leading-relaxed">
            <span className="font-bold text-emerald-300 font-mono text-[11px] block">
              💡 Key Objectives for Player 3:
            </span>
            <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
              <li>Define role: <em>Logic Decision Solver and Operational Authority</em></li>
              <li>Evaluate timeline against governing rules ({isMuseum ? "SEC-401, ART-302, CLR-505" : "SEC-101, OPS-204"})</li>
              <li>Deduce authorized dispatch action / conspirators and decisive evidence keys</li>
              <li><strong>Plain English:</strong> Write naturally without technical data formatting requirements</li>
            </ul>
          </div>

          {/* Form */}
          <form onSubmit={handleLockIn} className="space-y-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <label>Your Instruction Prompt for Agent 3:</label>
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
                  ? "e.g. Role: Logic Decision Solver. Evaluate the reconstructed timeline against Rule SEC-401, Rule ART-302, and Rule CLR-505. Deduce the conspirators Dr. Julian Vance and Marcus Thorne. Explain the Breaker B-04 90-second blackout forgery swap method. Cite key evidence (card CONSV-408, token C-408, acrylic spectrometry)."
                  : "e.g. Role: Logic Decision Solver. Evaluate the reconstructed timeline against Rule SEC-101, Rule BAGG-204, and Rule OPS-204. Deduce the culprit Tariq Malik, the luggage swap method using the duplicate tag and Maintenance Cart #MC-08, and cite the decisive clues (REPRINT-MGR-02 watermark, 6.3kg discrepancy, Door B-Staff-03 log)."
              }
              className={`w-full p-3.5 rounded-xl bg-slate-950 border font-mono text-xs text-slate-100 placeholder-slate-600 focus:outline-none transition leading-relaxed ${
                isLockedIn
                  ? "border-emerald-500/40 bg-emerald-950/10 opacity-80"
                  : wordCount > MAX_WORDS
                  ? "border-rose-500 focus:ring-1 focus:ring-rose-500"
                  : "border-slate-700 focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400"
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
                className="w-full py-3.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-slate-950 font-bold text-xs font-mono transition flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-emerald-500/20 active:scale-98"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Lock In Decision Prompt</span>
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
