import React, { useState } from "react";
import {
  Brain,
  AlertCircle,
  FileText,
  ShieldCheck,
  Code,
  Send,
  RotateCcw,
  Scale,
} from "lucide-react";
import { useGameStore } from "../store/useGameStore";

export function Step3Screen() {
  const { scenario, a2Output, submitStep3, isLoading } = useGameStore();

  const [prompt, setPrompt] = useState("");
  const [activeTab, setActiveTab] = useState("timeline"); // timeline, rules, schema

  if (!scenario) return null;

  const MAX_WORDS = 120;
  const MAX_CHARS = 900;

  const wordCount = prompt.trim() ? prompt.trim().split(/\s+/).length : 0;
  const charCount = prompt.length;
  const isOverWordLimit = wordCount > MAX_WORDS;
  const isOverCharLimit = charCount > MAX_CHARS;
  const isOverLimit = isOverWordLimit || isOverCharLimit;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim() || isOverLimit || isLoading) return;
    submitStep3(prompt.trim());
  };
  const rules = scenario.rules || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-900/40 via-teal-900/30 to-slate-900/80 border border-emerald-500/30 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              TURN 3 OF 3 • FINAL PHASE
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
              ROLE: LOGIC SOLVER
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Brain className="w-6 h-6 text-emerald-400" />
            Player 3: Logic Deduction & Final Verdict
          </h1>
          <p className="text-sm text-slate-400">
            Apply deductive reasoning across Agent 2's timeline and the operational rules. Prompt Agent 3 in plain English to deduce the final resolution.
          </p>
        </div>
      </div>

      {/* Main Two-Column Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Data Feeds & Rules (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900/90 border border-emerald-500/30 rounded-2xl shadow-xl overflow-hidden">
            {/* Tabs */}
            <div className="px-4 py-2 bg-slate-950/80 border-b border-slate-800 flex items-center gap-2 overflow-x-auto text-xs font-mono">
              <button
                onClick={() => setActiveTab("timeline")}
                className={`px-3 py-1.5 rounded-lg transition shrink-0 cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "timeline"
                    ? "bg-emerald-500 text-slate-950 font-bold"
                    : "bg-slate-900 text-slate-400 hover:text-slate-200"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Agent 2 Timeline</span>
              </button>
              <button
                onClick={() => setActiveTab("rules")}
                className={`px-3 py-1.5 rounded-lg transition shrink-0 cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "rules"
                    ? "bg-emerald-500 text-slate-950 font-bold"
                    : "bg-slate-900 text-slate-400 hover:text-slate-200"
                }`}
              >
                <Scale className="w-3.5 h-3.5" />
                <span>Rules & Policies ({rules.length})</span>
              </button>
              <button
                onClick={() => setActiveTab("schema")}
                className={`px-3 py-1.5 rounded-lg transition shrink-0 cursor-pointer flex items-center gap-1.5 ${
                  activeTab === "schema"
                    ? "bg-emerald-500 text-slate-950 font-bold"
                    : "bg-slate-900 text-slate-400 hover:text-slate-200"
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Resolution Checklist</span>
              </button>
            </div>

            {/* Tab Contents */}
            <div className="p-4 max-h-[520px] overflow-y-auto text-xs sm:text-sm font-mono text-slate-300 leading-relaxed whitespace-pre-wrap selection:bg-emerald-500/30">
              {activeTab === "timeline" && (
                a2Output || (
                  <div className="text-slate-500 italic py-8 text-center">
                    No timeline received from Agent 2.
                  </div>
                )
              )}

              {activeTab === "rules" && (
                <div className="space-y-3 whitespace-normal">
                  {rules.length === 0 ? (
                    <p className="text-slate-500 italic">No explicit operational rules defined.</p>
                  ) : (
                    rules.map((rule, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1"
                      >
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            {rule.id}
                          </span>
                          <span className="font-bold text-slate-200">{rule.name}</span>
                        </div>
                        <p className="text-xs text-slate-400 pl-1">{rule.description}</p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "schema" && (
                <div className="space-y-3 whitespace-normal">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono space-y-3">
                    <p className="text-emerald-400 font-bold flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4" /> Final Case Resolution Checklist:
                    </p>
                    <p className="text-slate-300 leading-relaxed">
                      Instruct Agent 3 to resolve the case by addressing these 4 core questions:
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1 text-slate-300">
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-emerald-400 font-bold block">1. Culprit / Operational Action</span>
                        <p className="text-slate-400 text-[11px] leading-relaxed">Who is the perpetrator, or what emergency action must be executed immediately?</p>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-emerald-400 font-bold block">2. Method & Mechanism</span>
                        <p className="text-slate-400 text-[11px] leading-relaxed">How was the breach carried out, or what security protocol explains the situation?</p>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-emerald-400 font-bold block">3. Violated Rule</span>
                        <p className="text-slate-400 text-[11px] leading-relaxed">Which specific operational rule or safety protocol applies (e.g. SEC-101, BAGG-204, ART-302)?</p>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-emerald-400 font-bold block">4. Decisive Evidence & Clues</span>
                        <p className="text-slate-400 text-[11px] leading-relaxed">What decisive physical clues, barcodes, or sensor logs prove the case?</p>
                      </div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-[11px] leading-relaxed">
                      💡 Tip: Write naturally in plain English! Agent 3 handles the technical data formatting automatically behind the scenes.
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Scenario Context */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 text-xs font-mono text-slate-400 space-y-1">
            <div className="text-slate-200 font-bold flex items-center gap-1.5">
              <span>Case: {scenario.title}</span>
            </div>
            <p className="text-slate-400">{scenario.objective}</p>
          </div>
        </div>

        {/* Right Column: Prompt Drafting (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Prompt Form */}
          <form
            onSubmit={handleSubmit}
            className="bg-slate-900/90 border border-emerald-500/30 rounded-2xl p-5 shadow-2xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <span>Player 3 Prompt for Agent 3</span>
              </label>

              <div className="flex items-center gap-2">
                {prompt && (
                  <button
                    type="button"
                    onClick={() => setPrompt("")}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-rose-950 text-slate-400 hover:text-rose-300 border border-slate-700 text-xs font-mono transition cursor-pointer flex items-center gap-1"
                  >
                    <RotateCcw className="w-3 h-3" /> Clear
                  </button>
                )}
              </div>
            </div>

            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={12}
                disabled={isLoading}
                placeholder="Write your prompt in plain English to instruct Agent 3 to deduce the culprit or action, method, motive, and violated rule..."
                className={`w-full bg-slate-950 border rounded-xl p-3.5 text-sm font-mono text-slate-200 placeholder-slate-600 focus:outline-none transition resize-y leading-relaxed disabled:opacity-50 ${
                  isOverLimit ? "border-rose-500 focus:border-rose-500" : "border-slate-800 focus:border-emerald-500"
                }`}
              />
            </div>

            {/* Bottom Meta & Submit */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-slate-800">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className={isOverWordLimit ? "text-rose-400 font-bold" : "text-slate-400"}>
                    {wordCount} / {MAX_WORDS} words
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className={isOverCharLimit ? "text-rose-400 font-bold" : "text-slate-400"}>
                    {charCount} / {MAX_CHARS} chars
                  </span>
                </div>
                {isOverLimit && (
                  <span className="text-xs font-mono text-rose-400 font-bold flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {isOverWordLimit
                      ? `Exceeds limit by ${wordCount - MAX_WORDS} words!`
                      : `Exceeds limit by ${charCount - MAX_CHARS} chars!`}
                  </span>
                )}
              </div>

              <button
                type="submit"
                disabled={!prompt.trim() || isOverLimit || isLoading}
                className="w-full sm:w-auto px-6 py-2.5 rounded-xl font-bold font-mono text-sm bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white transition shadow-lg shadow-emerald-600/30 disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Agent 3 is solving & scoring...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Solve & Finalize Verdict →</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Grand Finale Indicator */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-emerald-500/30 text-xs font-mono text-slate-400 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <p>
              Submitting triggers <strong>Agent 3</strong> to solve the mystery and immediately launches the <strong>Calibrated Relay Evaluator</strong> to calculate your team's final score!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
