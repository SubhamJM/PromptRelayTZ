import React, { useState } from "react";
import {
  Trophy,
  Award,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  BarChart3,
  FileText,
  UserCheck,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { useGameStore } from "../store/useGameStore";
import { useMultiplayerStore } from "../store/useMultiplayerStore";

export function ResultsScreen() {
  const {
    teamName,
    scenario,
    evaluation,
    finalVerdict,
    p1Prompt,
    a1Output,
    p2Prompt,
    a2Output,
    p3Prompt,
    resetMatch,
    setIsLeaderboardOpen,
  } = useGameStore();

  const [expandedSection, setExpandedSection] = useState("scorecards"); // scorecards, chain, truth

  const handleExitMatch = () => {
    useMultiplayerStore.getState().disconnect();
    resetMatch();
  };

  if (!evaluation) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <Trophy className="w-12 h-12 text-amber-400 mx-auto animate-bounce" />
        <h2 className="text-xl font-bold text-slate-100">Match Completed</h2>
        <p className="text-slate-400 font-mono text-sm">
          Awaiting evaluation payload or session completed.
        </p>
        <button
          onClick={handleExitMatch}
          className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 font-mono font-bold text-white transition"
        >
          Return to Lobby
        </button>
      </div>
    );
  }

  const totalScore = evaluation?.total_score ?? evaluation?.score ?? 0;
  const gradeStr = evaluation?.grade || "Evaluated";
  const summaryNarrative =
    evaluation?.summary_narrative ||
    evaluation?.summary ||
    "Team match evaluation completed.";

  // Safe resolution of player scorecards with dual fallback (p1_scorecard, player_1, or breakdown.player_1)
  const p1Card =
    evaluation?.p1_scorecard ||
    evaluation?.player_1 ||
    evaluation?.breakdown?.player_1 ||
    {};
  const p2Card =
    evaluation?.p2_scorecard ||
    evaluation?.player_2 ||
    evaluation?.breakdown?.player_2 ||
    {};
  const p3Card =
    evaluation?.p3_scorecard ||
    evaluation?.player_3 ||
    evaluation?.breakdown?.player_3 ||
    {};

  // Safe resolution of solution scorecard
  const solutionCard =
    evaluation?.solution_scorecard ||
    evaluation?.solution ||
    evaluation?.breakdown?.case_accuracy ||
    evaluation?.breakdown?.solution ||
    {};

  const culpritData = evaluation?.breakdown?.culprit || {};
  const methodData = evaluation?.breakdown?.method || {};
  const clueData = evaluation?.breakdown?.clue || {};

  const culpritPts =
    solutionCard?.action_or_culprit_pts ??
    culpritData.points ??
    (solutionCard?.culprit_correct ? 15 : 0);
  const culpritMax = culpritData.max_points ?? 15;
  const isCulpritCorrect =
    solutionCard?.culprit_correct ??
    (culpritData.status === "correct") ??
    (culpritPts >= 12);

  const methodPts =
    solutionCard?.rules_or_method_pts ??
    solutionCard?.method_score ??
    methodData.points ??
    0;
  const methodMax = methodData.max_points ?? 15;

  const cluePts =
    solutionCard?.proof_or_clue_pts ??
    solutionCard?.rule_score ??
    clueData.points ??
    0;
  const clueMax = clueData.max_points ?? 10;

  const solutionScore =
    solutionCard?.score ??
    evaluation?.breakdown?.case_accuracy?.score ??
    culpritPts + methodPts + cluePts;
  const solutionMaxScore = solutionCard?.max_score ?? 40;

  // Grade color helper
  const getGradeColor = (g) => {
    if (!g) return "text-blue-400 border-blue-500/40 bg-blue-500/10";
    if (g.startsWith("S")) return "text-amber-400 border-amber-500/40 bg-amber-500/10";
    if (g.startsWith("A")) return "text-emerald-400 border-emerald-500/40 bg-emerald-500/10";
    if (g.startsWith("B")) return "text-blue-400 border-blue-500/40 bg-blue-500/10";
    if (g.startsWith("C")) return "text-purple-400 border-purple-500/40 bg-purple-500/10";
    return "text-rose-400 border-rose-500/40 bg-rose-500/10";
  };

  const pScores = [
    { title: "Player 1 (Extractor)", card: p1Card, color: "blue" },
    { title: "Player 2 (Reconstructor)", card: p2Card, color: "purple" },
    { title: "Player 3 (Logic Solver)", card: p3Card, color: "emerald" },
  ];

  // Relay Chain prompts & outputs
  const resolvedP1Prompt =
    p1Prompt ||
    evaluation?.p1_prompt ||
    evaluation?.breakdown?.player_1?.prompt ||
    "";
  const resolvedA1Output =
    a1Output ||
    evaluation?.a1_output ||
    evaluation?.breakdown?.player_1?.agent_output ||
    "";
  const resolvedP2Prompt =
    p2Prompt ||
    evaluation?.p2_prompt ||
    evaluation?.breakdown?.player_2?.prompt ||
    "";
  const resolvedA2Output =
    a2Output ||
    evaluation?.a2_output ||
    evaluation?.breakdown?.player_2?.agent_output ||
    "";
  const resolvedP3Prompt =
    p3Prompt ||
    evaluation?.p3_prompt ||
    evaluation?.breakdown?.player_3?.prompt ||
    "";
  const resolvedA3Output =
    evaluation?.a3_output ||
    (typeof finalVerdict === "object"
      ? JSON.stringify(finalVerdict, null, 2)
      : finalVerdict) ||
    "";

  // Ground Truth and Verdict
  const expectedCulprit =
    solutionCard?.ground_truth?.culprit ||
    scenario?.ground_truth?.culprit ||
    scenario?.ground_truth?.action ||
    evaluation?.expected_verdict?.culprit ||
    evaluation?.breakdown?.culprit?.expected ||
    "N/A";
  const expectedMethod =
    solutionCard?.ground_truth?.method ||
    scenario?.ground_truth?.method ||
    scenario?.ground_truth?.rules ||
    evaluation?.expected_verdict?.method ||
    evaluation?.breakdown?.method?.expected ||
    "N/A";
  const expectedMotive =
    solutionCard?.ground_truth?.motive ||
    scenario?.ground_truth?.motive ||
    (Array.isArray(scenario?.operational_rules) ? scenario.operational_rules[0] : null) ||
    "N/A";
  const expectedRule =
    solutionCard?.ground_truth?.rule_broken ||
    solutionCard?.ground_truth?.clue ||
    scenario?.ground_truth?.proof ||
    scenario?.ground_truth?.clue ||
    evaluation?.expected_verdict?.rule_broken ||
    evaluation?.breakdown?.clue?.expected ||
    "N/A";

  const teamParsed =
    solutionCard?.parsed_verdict ||
    finalVerdict ||
    evaluation?.actual_verdict ||
    evaluation?.final_verdict ||
    {};
  const teamCulprit =
    teamParsed?.culprit ||
    teamParsed?.action ||
    evaluation?.breakdown?.culprit?.actual ||
    "N/A";
  const teamMethod =
    teamParsed?.method ||
    teamParsed?.rules ||
    evaluation?.breakdown?.method?.actual ||
    "N/A";
  const teamMotive =
    teamParsed?.motive ||
    teamParsed?.reason ||
    "N/A";
  const teamRule =
    teamParsed?.rule_broken ||
    teamParsed?.clue ||
    teamParsed?.proof ||
    evaluation?.breakdown?.clue?.actual ||
    "N/A";

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Hero Victory Card */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 p-6 sm:p-10 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8 text-center md:text-left">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono font-bold text-slate-300">
              <Trophy className="w-3.5 h-3.5 text-amber-400" />
              <span>OFFICIAL MATCH EVALUATION</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Team: <span className="text-blue-400">{teamName}</span>
            </h1>

            <p className="text-slate-400 font-mono text-sm max-w-xl">
              Scenario: <span className="text-slate-200 font-bold">{scenario?.title}</span> • Difficulty: {scenario?.difficulty}
            </p>

            <p className="text-slate-300 font-mono text-xs sm:text-sm max-w-2xl leading-relaxed pt-2">
              {summaryNarrative}
            </p>
          </div>

          {/* Big Score Callout */}
          <div className="flex flex-col items-center shrink-0">
            <div className="w-40 h-40 rounded-3xl bg-slate-950/90 border-2 border-blue-500/30 flex flex-col items-center justify-center shadow-2xl relative">
              <span className="text-5xl font-black font-mono tracking-tight text-white">
                {totalScore}
              </span>
              <span className="text-xs font-mono text-slate-400 mt-1">OUT OF 100 PTS</span>

              <div
                className={`absolute -bottom-3.5 px-3 py-0.5 rounded-full border text-xs font-mono font-extrabold shadow-lg ${getGradeColor(
                  gradeStr
                )}`}
              >
                {gradeStr}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="relative z-10 flex flex-wrap items-center justify-center md:justify-start gap-3 pt-8 mt-6 border-t border-slate-800">
          <button
            onClick={() => setIsLeaderboardOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-mono font-bold text-xs sm:text-sm transition flex items-center gap-2 border border-slate-700 cursor-pointer shadow-lg"
          >
            <BarChart3 className="w-4 h-4 text-amber-400" />
            <span>View Global Leaderboard</span>
          </button>

          <button
            onClick={handleExitMatch}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-mono font-bold text-xs sm:text-sm transition flex items-center gap-2 shadow-lg shadow-blue-600/30 cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Play Next Scenario</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs for Details */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-mono">
        <button
          onClick={() => setExpandedSection("scorecards")}
          className={`px-4 py-2 rounded-xl transition cursor-pointer font-bold ${
            expandedSection === "scorecards"
              ? "bg-blue-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          Player Scorecards (60 pts) & Verdict (40 pts)
        </button>
        <button
          onClick={() => setExpandedSection("chain")}
          className={`px-4 py-2 rounded-xl transition cursor-pointer font-bold ${
            expandedSection === "chain"
              ? "bg-blue-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          Relay Chain Inspection (Prompts & Outputs)
        </button>
        <button
          onClick={() => setExpandedSection("truth")}
          className={`px-4 py-2 rounded-xl transition cursor-pointer font-bold ${
            expandedSection === "truth"
              ? "bg-blue-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          Ground Truth Comparison
        </button>
      </div>

      {/* TAB 1: SCORECARDS & VERDICT */}
      {expandedSection === "scorecards" && (
        <div className="space-y-6">
          {/* Individual Player Scorecards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {pScores.map(({ title, card, color }, idx) => (
              <div
                key={idx}
                className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-slate-300 block">{title}</span>
                      <span className="text-[11px] font-mono text-slate-500">
                        Prompt: {card?.prompt_score ?? card?.criteria?.prompt_score ?? 0}/12 • Execution: {card?.agent_score ?? card?.criteria?.agent_score ?? 0}/8
                      </span>
                    </div>
                    <span className="px-2.5 py-1 rounded-full font-mono text-xs font-extrabold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                      {card?.score ?? 0} / {card?.max_score ?? 20} pts
                    </span>
                  </div>

                  <p className="text-xs font-mono text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                    {card?.itemized_feedback ||
                      card?.feedback ||
                      (card?.score !== undefined
                        ? `Scored ${card.score}/20 pts. Prompt engineering and agent execution evaluated.`
                        : "No feedback recorded.")}
                  </p>
                </div>

                <div className="space-y-2 pt-2 border-t border-slate-800 text-[11px] font-mono">
                  {card?.strengths && card.strengths.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-emerald-400 font-bold flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Strengths:
                      </span>
                      <ul className="text-slate-400 space-y-0.5 pl-4 list-disc">
                        {card.strengths.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {card?.weaknesses && card.weaknesses.length > 0 && (
                    <div className="space-y-1 pt-1">
                      <span className="text-rose-400 font-bold flex items-center gap-1">
                        <XCircle className="w-3 h-3" /> Improvements:
                      </span>
                      <ul className="text-slate-400 space-y-0.5 pl-4 list-disc">
                        {card.weaknesses.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Solution Accuracy Scorecard (40 pts) */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Award className="w-5 h-5 text-emerald-400" />
                  Final Solution Accuracy & Logic Deduction
                </h3>
                <p className="text-xs font-mono text-slate-400">
                  Judged against official scenario ground truth.
                </p>
              </div>

              <span className="px-3 py-1 rounded-full font-mono text-sm font-extrabold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                {solutionScore} / {solutionMaxScore} pts
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center font-mono">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-xs text-slate-500 block">Culprit / Action ID</span>
                <span
                  className={`text-sm font-bold block mt-1 ${
                    isCulpritCorrect
                      ? "text-emerald-400"
                      : culpritPts > 0
                      ? "text-amber-400"
                      : "text-rose-400"
                  }`}
                >
                  {isCulpritCorrect
                    ? `CORRECT (+${culpritPts})`
                    : culpritPts > 0
                    ? `PARTIAL (+${culpritPts})`
                    : "INCORRECT (0)"}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  {culpritPts} / {culpritMax} pts
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-xs text-slate-500 block">Method / Rules</span>
                <span
                  className={`text-sm font-bold block mt-1 ${
                    methodPts > 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {methodPts} / {methodMax} pts
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  {methodData.status ? methodData.status.toUpperCase() : "EVALUATED"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-xs text-slate-500 block">Key Clue / Proof</span>
                <span
                  className={`text-sm font-bold block mt-1 ${
                    cluePts > 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {cluePts} / {clueMax} pts
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  {clueData.status ? clueData.status.toUpperCase() : "EVALUATED"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-xs text-slate-500 block">Verdict Format</span>
                <span className="text-sm font-bold block mt-1 text-emerald-400">
                  {evaluation?.breakdown?.format?.status === "failed" ? "INVALID" : "COMPLIANT"}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Structured JSON
                </span>
              </div>
            </div>

            {(solutionCard?.reasoning || summaryNarrative) && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed">
                <strong className="text-emerald-400">Evaluator Synthesis: </strong>
                {solutionCard?.reasoning || summaryNarrative}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: RELAY CHAIN BREAKDOWN */}
      {expandedSection === "chain" && (
        <div className="space-y-6 font-mono text-xs">
          {/* Step 1 */}
          <div className="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-blue-400 text-sm">Step 1: Evidence Extractor</span>
              <span className="text-slate-500">P1 Prompt ➔ Agent 1 Output</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 font-bold block">Player 1 Prompt:</span>
                <p className="text-slate-300 whitespace-pre-wrap">{resolvedP1Prompt || "No prompt recorded."}</p>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 max-h-60 overflow-y-auto">
                <span className="text-slate-400 font-bold block">Agent 1 Extracted Facts:</span>
                <p className="text-slate-300 whitespace-pre-wrap">{resolvedA1Output || "No output recorded."}</p>
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-slate-900/90 border border-purple-500/30 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-purple-400 text-sm">Step 2: Timeline Reconstructor</span>
              <span className="text-slate-500">P2 Prompt ➔ Agent 2 Output</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 font-bold block">Player 2 Prompt:</span>
                <p className="text-slate-300 whitespace-pre-wrap">{resolvedP2Prompt || "No prompt recorded."}</p>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 max-h-60 overflow-y-auto">
                <span className="text-slate-400 font-bold block">Agent 2 Reconstructed Timeline:</span>
                <p className="text-slate-300 whitespace-pre-wrap">{resolvedA2Output || "No output recorded."}</p>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="bg-slate-900/90 border border-emerald-500/30 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-bold text-emerald-400 text-sm">Step 3: Logic Solver</span>
              <span className="text-slate-500">P3 Prompt ➔ Agent 3 Output</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <span className="text-slate-400 font-bold block">Player 3 Prompt:</span>
                <p className="text-slate-300 whitespace-pre-wrap">{resolvedP3Prompt || "No prompt recorded."}</p>
              </div>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1 max-h-60 overflow-y-auto">
                <span className="text-slate-400 font-bold block">Agent 3 Final Verdict:</span>
                <pre className="text-slate-300 whitespace-pre-wrap">
                  {resolvedA3Output || "No output recorded."}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: GROUND TRUTH */}
      {expandedSection === "truth" && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 font-mono text-xs">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            Official Scenario Solution vs Team Verdict
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <span className="text-emerald-400 font-bold text-xs uppercase block">
                Ground Truth (Expected Solution)
              </span>
              <div className="space-y-2 text-slate-300">
                <div>
                  <span className="text-slate-500">Culprit / Action:</span>{" "}
                  <strong>{expectedCulprit}</strong>
                </div>
                <div>
                  <span className="text-slate-500">Method / Rules:</span>{" "}
                  <span>{expectedMethod}</span>
                </div>
                <div>
                  <span className="text-slate-500">Motive / Objective:</span>{" "}
                  <span>{expectedMotive}</span>
                </div>
                <div>
                  <span className="text-slate-500">Rule Violated / Proof Clue:</span>{" "}
                  <span>{expectedRule}</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <span className="text-blue-400 font-bold text-xs uppercase block">
                Team Verdict (Parsed Solution)
              </span>
              <div className="space-y-2 text-slate-300">
                <div>
                  <span className="text-slate-500">Culprit / Action:</span>{" "}
                  <strong>{teamCulprit}</strong>
                </div>
                <div>
                  <span className="text-slate-500">Method / Rules:</span>{" "}
                  <span>{teamMethod}</span>
                </div>
                <div>
                  <span className="text-slate-500">Motive / Objective:</span>{" "}
                  <span>{teamMotive}</span>
                </div>
                <div>
                  <span className="text-slate-500">Rule Violated / Proof Clue:</span>{" "}
                  <span>{teamRule}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
