import React from "react";
import {
  Brain,
  CheckCircle2,
  Loader2,
  Sparkles,
  ArrowRight,
  Eye,
  Network,
  Cpu,
  Trophy,
  ShieldCheck,
} from "lucide-react";
import { useMultiplayerStore } from "../../store/useMultiplayerStore";
import { useGameStore } from "../../store/useGameStore";

export function ExecutionTheater() {
  const { teamName, roomCode, executionProgress, room } = useMultiplayerStore();
  const {
    currentStep,
    agentName,
    step1Output,
    step2Output,
    step3Output,
    finalVerdict,
    evaluation,
  } = executionProgress;

  const handleGoToResults = () => {
    // Transition game store to completed to view full ResultsScreen
    useGameStore.setState({ currentStep: "completed" });
  };

  const isCompleted = room?.status === "completed" || !!evaluation;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-8 animate-fade-in">
      {/* Title Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-mono font-semibold tracking-wider uppercase">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          Synchronized Relay Execution • Room {roomCode}
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 font-serif tracking-tight">
          Orchestrating 3 AI Agents Live
        </h2>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          All 3 players have locked in their prompts. Watch the intelligence relay pass from Agent 1 to Agent 2 to Agent 3 across your laptops.
        </p>
      </div>

      {/* Progress Pipeline Stepper */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 font-mono text-xs">
        {/* Stage 1 */}
        <div
          className={`p-4 rounded-2xl border transition ${
            currentStep > 1 || isCompleted
              ? "bg-slate-900 border-blue-500/60 text-slate-200"
              : currentStep === 1
              ? "bg-blue-950/40 border-2 border-blue-400 shadow-lg shadow-blue-500/20 text-blue-200 ring-2 ring-blue-500/30"
              : "bg-slate-950 border-slate-800 text-slate-500"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">
              Stage 1
            </span>
            {currentStep > 1 || isCompleted ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : currentStep === 1 ? (
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
            ) : null}
          </div>
          <div className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
            <Eye className="w-4 h-4 text-blue-400" />
            <span>Agent 1: Extractor</span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-1">
            Mining visual evidence & OCR
          </span>
        </div>

        {/* Stage 2 */}
        <div
          className={`p-4 rounded-2xl border transition ${
            currentStep > 2 || isCompleted
              ? "bg-slate-900 border-purple-500/60 text-slate-200"
              : currentStep === 2
              ? "bg-purple-950/40 border-2 border-purple-400 shadow-lg shadow-purple-500/20 text-purple-200 ring-2 ring-purple-500/30"
              : "bg-slate-950 border-slate-800 text-slate-500"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">
              Stage 2
            </span>
            {currentStep > 2 || isCompleted ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : currentStep === 2 ? (
              <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
            ) : null}
          </div>
          <div className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
            <Network className="w-4 h-4 text-purple-400" />
            <span>Agent 2: Reconstructor</span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-1">
            Reconstructing chronological graph
          </span>
        </div>

        {/* Stage 3 */}
        <div
          className={`p-4 rounded-2xl border transition ${
            currentStep > 3 || isCompleted
              ? "bg-slate-900 border-emerald-500/60 text-slate-200"
              : currentStep === 3
              ? "bg-emerald-950/40 border-2 border-emerald-400 shadow-lg shadow-emerald-500/20 text-emerald-200 ring-2 ring-emerald-500/30"
              : "bg-slate-950 border-slate-800 text-slate-500"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
              Stage 3
            </span>
            {currentStep > 3 || isCompleted ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : currentStep === 3 ? (
              <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
            ) : null}
          </div>
          <div className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>Agent 3: Logic Solver</span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-1">
            Verifying rules & JSON schema
          </span>
        </div>

        {/* Stage 4: Evaluation */}
        <div
          className={`p-4 rounded-2xl border transition ${
            isCompleted
              ? "bg-amber-950/30 border-2 border-amber-400 text-amber-200 shadow-lg shadow-amber-500/20"
              : currentStep === 4
              ? "bg-slate-900 border-2 border-amber-400 animate-pulse text-amber-300"
              : "bg-slate-950 border-slate-800 text-slate-500"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
              Stage 4
            </span>
            {isCompleted ? (
              <Trophy className="w-4 h-4 text-amber-400" />
            ) : currentStep === 4 ? (
              <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
            ) : null}
          </div>
          <div className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
            <Trophy className="w-4 h-4 text-amber-400" />
            <span>Analytical Score</span>
          </div>
          <span className="text-[11px] text-slate-400 block mt-1">
            {isCompleted ? `${evaluation?.total_score || 0}/100 PTS` : "Scoring prompt merit"}
          </span>
        </div>
      </div>

      {/* Active Agent Banner */}
      {!isCompleted && (
        <div className="p-4 rounded-2xl bg-blue-950/40 border border-blue-500/30 flex items-center justify-between gap-4 font-mono text-xs">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin shrink-0" />
            <div>
              <span className="text-slate-400 text-[10px] uppercase block">
                Currently Executing in Relay:
              </span>
              <span className="font-bold text-slate-100 text-sm">
                {agentName || "Initializing Agent Pipeline..."}
              </span>
            </div>
          </div>
          <span className="text-blue-300 font-bold hidden sm:inline">
            Streaming Live Across All Laptops
          </span>
        </div>
      )}

      {/* Score Reveal Banner (When Completed) */}
      {isCompleted && (
        <div className="p-6 rounded-3xl bg-gradient-to-br from-amber-950/40 via-slate-900 to-slate-950 border-2 border-amber-500/50 shadow-2xl space-y-4 text-center animate-fade-in">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 font-mono text-xs font-bold border border-amber-500/40">
            <Sparkles className="w-4 h-4" />
            <span>RELAY CHALLENGE COMPLETED</span>
          </div>

          <div className="space-y-1">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-100 font-serif">
              Team Total Score: {evaluation?.total_score || 0} / 100 PTS
            </h3>
            <p className="text-amber-400 font-mono font-bold text-sm">
              Grade: {evaluation?.grade || "Master Detective (S)"}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 max-w-lg mx-auto font-mono text-xs pt-2">
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-400 block text-[10px]">P1 Merit</span>
              <span className="text-blue-400 font-bold text-sm">
                {evaluation?.breakdown?.player_1?.score || 20}/20
              </span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-400 block text-[10px]">P2 Merit</span>
              <span className="text-purple-400 font-bold text-sm">
                {evaluation?.breakdown?.player_2?.score || 20}/20
              </span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-400 block text-[10px]">P3 Merit</span>
              <span className="text-emerald-400 font-bold text-sm">
                {evaluation?.breakdown?.player_3?.score || 20}/20
              </span>
            </div>
          </div>

          <button
            onClick={handleGoToResults}
            className="mt-4 px-8 py-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-slate-950 font-extrabold text-sm transition transform active:scale-95 shadow-xl shadow-amber-500/20 inline-flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>View Full Breakdown, Feedback & Leaderboard</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Streaming Agent Output Feeds */}
      <div className="space-y-4">
        {/* Feed 1: Agent 1 Output */}
        {step1Output && (
          <div className="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-5 shadow-xl space-y-2 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-blue-400 font-mono text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Agent 1 Output (Extracted Facts):</span>
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                Fed into Agent 2
              </span>
            </div>
            <p className="text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
              {step1Output}
            </p>
          </div>
        )}

        {/* Feed 2: Agent 2 Output */}
        {step2Output && (
          <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-5 shadow-xl space-y-2 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-purple-400 font-mono text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Agent 2 Output (Reconstructed Chronological Sequence):</span>
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                Fed into Agent 3
              </span>
            </div>
            <p className="text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
              {step2Output}
            </p>
          </div>
        )}

        {/* Feed 3: Agent 3 Output */}
        {step3Output && (
          <div className="bg-slate-900/90 border border-emerald-500/30 rounded-2xl p-5 shadow-xl space-y-2 animate-fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-emerald-400 font-mono text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Agent 3 Final Operational Verdict (Strict JSON):</span>
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                Machine-Readable Output
              </span>
            </div>
            <pre className="text-xs font-mono text-emerald-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto p-3 bg-slate-950 rounded-xl border border-slate-800">
              {step3Output}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
