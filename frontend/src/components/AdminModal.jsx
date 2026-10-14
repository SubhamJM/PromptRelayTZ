import React, { useEffect, useState } from "react";
import { Settings, X, Download, Trash2, RefreshCw, Zap, AlertTriangle, Eye } from "lucide-react";
import { api } from "../api/client";
import { useGameStore } from "../store/useGameStore";

export function AdminModal() {
  const { isAdminOpen, setIsAdminOpen } = useGameStore();
  const [activeTab, setActiveTab] = useState("matches"); // matches, llm
  const [stats, setStats] = useState(null);
  const [matches, setMatches] = useState([]);
  const [llmStatus, setLlmStatus] = useState(null);
  const [inspectedMatch, setInspectedMatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pingLoading, setPingLoading] = useState(false);

  // Form state
  const [provider, setProvider] = useState("gemini");
  const [modelName, setModelName] = useState("gemini-3.8-flash");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sData, mData, lData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminMatches(),
        api.getLLMStatus(),
      ]);
      setStats(sData);
      setMatches(mData);
      setLlmStatus(lData);
      setProvider(lData.provider);
      setModelName(lData.model_name);
    } catch (err) {
      console.error("Failed to load admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdminOpen) {
      fetchData();
    }
  }, [isAdminOpen]);

  const handleTestPing = async () => {
    setPingLoading(true);
    try {
      const res = await api.getLLMStatus();
      setLlmStatus(res);
    } catch (err) {
      alert("Ping error: " + err.message);
    } finally {
      setPingLoading(false);
    }
  };

  const handleSaveLLM = async () => {
    setLoading(true);
    try {
      const res = await api.configureLLM({
        provider,
        model_name: modelName,
      });
      setLlmStatus(res);
      alert("LLM settings applied successfully!");
    } catch (err) {
      alert("Config error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMatch = async (sessionId) => {
    if (!confirm("Are you sure you want to delete this match record?")) return;
    try {
      await api.deleteAdminMatch(sessionId);
      fetchData();
      if (inspectedMatch?.session_id === sessionId) {
        setInspectedMatch(null);
      }
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  };

  const handleReset = async () => {
    if (!confirm("⚠️ DANGER: Reset all tournament matches and history? This cannot be undone!"))
      return;
    try {
      await api.resetTournament();
      fetchData();
      setInspectedMatch(null);
      alert("Tournament history reset successfully.");
    } catch (err) {
      alert("Reset error: " + err.message);
    }
  };

  if (!isAdminOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
      <div className="max-w-4xl w-full bg-slate-900 border border-slate-700 rounded-2xl p-6 sm:p-8 flex flex-col max-h-[90vh] shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-slate-300" />
            <div>
              <h3 className="text-xl font-bold font-serif text-slate-100">
                Organizer Control Center
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Tournament telemetry, match inspector, and model engine
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsAdminOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Buttons */}
        <div className="flex border-b border-slate-800 gap-4 text-xs font-mono">
          <button
            onClick={() => setActiveTab("matches")}
            className={`pb-2 border-b-2 font-bold transition cursor-pointer ${
              activeTab === "matches"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            📊 Standings & Matches
          </button>
          <button
            onClick={() => setActiveTab("llm")}
            className={`pb-2 border-b-2 font-bold transition cursor-pointer ${
              activeTab === "llm"
                ? "border-amber-400 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            ⚡ LLM Engine & Connectivity
          </button>
        </div>

        {/* TAB 1: MATCHES & STATS */}
        {activeTab === "matches" && (
          <div className="space-y-4 flex-1 flex flex-col min-h-0 overflow-y-auto pr-1">
            {stats && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xl font-bold text-amber-400">{stats.total_matches}</div>
                  <div className="text-[11px] text-slate-400">Total Matches</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xl font-bold text-slate-100">{stats.average_score}</div>
                  <div className="text-[11px] text-slate-400">Average Score</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xl font-bold text-emerald-400">{stats.highest_score}</div>
                  <div className="text-[11px] text-slate-400">Highest Score</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-xl font-bold text-cyan-400">{stats.solve_rate}%</div>
                  <div className="text-[11px] text-slate-400">Accurate Solves</div>
                </div>
              </div>
            )}

            {/* Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
              <div className="flex items-center gap-2">
                <a
                  href="/api/admin/export/csv"
                  download
                  className="px-3 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-500/40 text-emerald-300 font-semibold flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" /> Export CSV
                </a>
                <a
                  href="/api/admin/export/json"
                  download
                  className="px-3 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-500/40 text-cyan-300 font-semibold flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" /> Export JSON
                </a>
                <button
                  onClick={fetchData}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1 transition cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Refresh
                </button>
              </div>

              <button
                onClick={handleReset}
                className="px-3 py-1.5 rounded-lg bg-red-950/50 hover:bg-red-900/50 border border-red-500/40 text-red-300 font-semibold flex items-center gap-1.5 transition cursor-pointer"
              >
                <AlertTriangle className="w-3.5 h-3.5" /> Reset Tournament
              </button>
            </div>

            {/* Matches List */}
            <div className="border border-slate-800 rounded-xl bg-slate-950 max-h-52 overflow-y-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="text-slate-400 border-b border-slate-800 sticky top-0 bg-slate-950">
                  <tr>
                    <th className="py-2.5 px-3">Team</th>
                    <th className="py-2.5 px-3">Scenario</th>
                    <th className="py-2.5 px-3">Score</th>
                    <th className="py-2.5 px-3">Grade</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {matches.map((m) => (
                    <tr key={m.session_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 font-semibold text-slate-100">{m.team_name}</td>
                      <td className="py-2.5 px-3 text-slate-400 truncate max-w-[140px]">
                        {m.scenario_title}
                      </td>
                      <td className="py-2.5 px-3 font-bold">{m.total_score}</td>
                      <td className="py-2.5 px-3 text-amber-300">{m.grade.split(" ")[0]}</td>
                      <td className="py-2.5 px-3 text-right flex items-center justify-end gap-2">
                        <button
                          onClick={() => setInspectedMatch(m)}
                          className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-300 cursor-pointer"
                          title="Inspect match transcript"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteMatch(m.session_id)}
                          className="p-1 rounded bg-slate-800 hover:bg-red-900/50 text-red-300 cursor-pointer"
                          title="Delete match"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {matches.length === 0 && (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-500">
                        No matches recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Match Inspector Drawer */}
            {inspectedMatch && (
              <div className="p-4 rounded-xl bg-slate-950 border border-amber-500/40 space-y-3 font-mono text-xs max-h-56 overflow-y-auto">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-amber-400">
                    Match Transcript: {inspectedMatch.team_name} ({inspectedMatch.scenario_title})
                  </span>
                  <button
                    onClick={() => setInspectedMatch(null)}
                    className="text-slate-400 hover:text-slate-200 cursor-pointer"
                  >
                    ✕
                  </button>
                </div>
                <div className="space-y-2">
                  <div>
                    <span className="text-slate-400 font-semibold">Player 1 Prompt:</span>
                    <p className="text-slate-300 bg-slate-900 p-2 rounded whitespace-pre-wrap">
                      {inspectedMatch.p1_prompt || "(None)"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold">Agent 1 Extracted Facts:</span>
                    <p className="text-slate-300 bg-slate-900 p-2 rounded whitespace-pre-wrap max-h-32 overflow-y-auto">
                      {inspectedMatch.a1_output || "(None)"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold">Player 2 Prompt:</span>
                    <p className="text-slate-300 bg-slate-900 p-2 rounded whitespace-pre-wrap">
                      {inspectedMatch.p2_prompt || "(None)"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold">Agent 2 Timeline:</span>
                    <p className="text-slate-300 bg-slate-900 p-2 rounded whitespace-pre-wrap max-h-32 overflow-y-auto">
                      {inspectedMatch.a2_output || "(None)"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold">Player 3 Prompt:</span>
                    <p className="text-slate-300 bg-slate-900 p-2 rounded whitespace-pre-wrap">
                      {inspectedMatch.p3_prompt || "(None)"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-400 font-semibold">Agent 3 Final Verdict:</span>
                    <pre className="text-slate-300 bg-slate-900 p-2 rounded overflow-x-auto">
                      {JSON.stringify(inspectedMatch.final_verdict, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: LLM ENGINE CONFIG */}
        {activeTab === "llm" && (
          <div className="space-y-4 font-mono text-xs flex-1 overflow-y-auto pr-1">
            {llmStatus && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className={`w-3 h-3 rounded-full ${
                      llmStatus.status === "connected"
                        ? "bg-emerald-400 animate-pulse"
                        : "bg-red-400"
                    }`}
                  />
                  <div>
                    <div className="font-bold text-slate-100 flex items-center gap-2">
                      <span>Provider:</span>
                      <span className="text-amber-400 uppercase">{llmStatus.provider}</span>
                      <span className="text-slate-500">|</span>
                      <span className="text-slate-300">{llmStatus.model_name}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {llmStatus.message || "Engine ready"}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 font-bold">
                    {llmStatus.latency_ms ?? "--"} ms
                  </span>
                  <button
                    onClick={handleTestPing}
                    disabled={pingLoading}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-400 font-semibold transition cursor-pointer flex items-center gap-1"
                  >
                    <Zap className="w-3.5 h-3.5" />
                    <span>{pingLoading ? "Pinging..." : "Test Ping"}</span>
                  </button>
                </div>
              </div>
            )}

            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
              <h4 className="font-bold text-slate-200 text-sm">Configure Model & Provider</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-400 uppercase tracking-wider text-[11px] mb-1">
                    Provider
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-amber-400"
                  >
                    <option value="gemini">Google Gemini (Default)</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic Claude</option>
                    <option value="ollama">Ollama Local</option>
                    <option value="offline">Offline Simulator (Zero Internet)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 uppercase tracking-wider text-[11px] mb-1">
                    Model Identifier
                  </label>
                  <input
                    type="text"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-amber-400"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleSaveLLM}
                  disabled={loading}
                  className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold transition cursor-pointer"
                >
                  Apply Model Settings
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="pt-2 flex justify-end border-t border-slate-800">
          <button
            onClick={() => setIsAdminOpen(false)}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-bold transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
