import React, { useState } from "react";
import {
  FileSearch,
  Sparkles,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Send,
  RotateCcw,
  BookOpen,
} from "lucide-react";
import { useGameStore } from "../store/useGameStore";
import { EvidenceViewer } from "../components/EvidenceViewer";

export function Step1Screen() {
  const { scenario, submitStep1, isLoading } = useGameStore();

  const [prompt, setPrompt] = useState("");
  const [showTips, setShowTips] = useState(true);

  if (!scenario) return null;

  const defaultTemplate = `You are a forensic investigator and data extraction specialist.
Carefully examine all available evidence items (CCTV frames, logs, notes).
Extract every verified factual detail relevant to the case:
1. Timestamps and chronological markers
2. Identified persons, aliases, clothing, and badge numbers
3. Physical items (luggage tags, flight numbers, chemical names, device IDs)
4. Key anomalies, security breaches, or suspicious interactions

Ignore unsupported assumptions and red herrings. Output your findings as a clean, structured bulleted list of verified facts.`;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    submitStep1(prompt.trim());
  };

  const wordCount = prompt.trim() ? prompt.trim().split(/\s+/).length : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-900/40 via-indigo-900/30 to-slate-900/80 border border-blue-500/30 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40">
              TURN 1 OF 3
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
              ROLE: EVIDENCE EXTRACTOR
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-100 flex items-center gap-2">
            <FileSearch className="w-6 h-6 text-blue-400" />
            Player 1: Evidence Extraction Phase
          </h1>
          <p className="text-sm text-slate-400">
            Carefully inspect the case evidence on the left. Prompt Agent 1 to filter out noise and extract critical facts for Player 2.
          </p>
        </div>

        <button
          onClick={() => setShowTips(!showTips)}
          className="self-start md:self-center px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono font-semibold transition border border-slate-700 flex items-center gap-2 cursor-pointer shrink-0"
        >
          <BookOpen className="w-4 h-4 text-blue-400" />
          {showTips ? "Hide Rubric & Tips" : "Show Rubric & Tips"}
        </button>
      </div>

      {/* Main Two-Column Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Evidence Viewer (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <EvidenceViewer isStep1={true} />
        </div>

        {/* Right Column: Prompt Drafting & Tips (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Rubric / Strategy Card */}
          {showTips && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-blue-400 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" /> SCORING RUBRIC (20 PTS)
                </span>
                <span className="text-[11px] font-mono text-slate-400">P1 Weight: 20%</span>
              </div>
              <ul className="text-xs font-mono text-slate-300 space-y-1.5 list-disc list-inside">
                <li><strong className="text-slate-100">Specific Role & Objective:</strong> Clearly define Agent 1's role as a forensic data extractor.</li>
                <li><strong className="text-slate-100">Filtering Noise:</strong> Instruct the agent to ignore distractions/red herrings.</li>
                <li><strong className="text-slate-100">Structured Output:</strong> Request bulleted facts, timestamps, and suspect attributes.</li>
                <li><strong className="text-slate-100">No Premature Logic:</strong> Leave chronological timeline synthesis for Player 2 and final verdicts for Player 3!</li>
              </ul>
            </div>
          )}

          {/* Prompt Form */}
          <form
            onSubmit={handleSubmit}
            className="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-5 shadow-2xl space-y-4"
          >
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <span>Player 1 Prompt for Agent 1</span>
              </label>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPrompt(defaultTemplate)}
                  className="px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-mono transition cursor-pointer flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" /> Template
                </button>
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
                placeholder="Write your prompt to guide Agent 1 in extracting key facts, IDs, timestamps, and evidence from the dossier..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-sm font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition resize-y leading-relaxed disabled:opacity-50"
              />
            </div>

            {/* Bottom Meta & Submit */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-slate-800">
              <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
                <span>{prompt.length} chars</span>
                <span>•</span>
                <span>{wordCount} words</span>
              </div>

              <button
                type="submit"
                disabled={!prompt.trim() || isLoading}
                className="w-full sm:w-auto px-6 py-2.5 rounded-xl font-bold font-mono text-sm bg-blue-600 hover:bg-blue-500 active:scale-95 text-white transition shadow-lg shadow-blue-600/30 disabled:opacity-50 disabled:pointer-events-none cursor-pointer flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Agent 1 is working...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Run Agent 1 & Proceed →</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Hotseat Reminder */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs font-mono text-slate-400 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p>
              Once you submit, Agent 1 will extract the raw facts and hand off the laptop to <strong>Player 2</strong> (Timeline Reconstructor).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
