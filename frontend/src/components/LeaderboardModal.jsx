import React, { useEffect, useState } from "react";
import { Trophy, X, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import { useGameStore } from "../store/useGameStore";

export function LeaderboardModal() {
  const { isLeaderboardOpen, setIsLeaderboardOpen } = useGameStore();
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStandings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLeaderboard();
      setStandings(data.leaderboard || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isLeaderboardOpen) {
      fetchStandings();
    }
  }, [isLeaderboardOpen]);

  if (!isLeaderboardOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
      <div className="max-w-3xl w-full bg-slate-900 border border-amber-500/30 rounded-2xl p-6 sm:p-8 flex flex-col max-h-[85vh] shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <Trophy className="w-6 h-6 text-amber-400" />
            <div>
              <h3 className="text-xl font-bold font-serif text-slate-100">
                Tournament Leaderboard
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Ranked by calibrated total score (0–100)
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsLeaderboardOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Table Content */}
        <div className="flex-1 overflow-y-auto pr-1">
          {loading ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
              <span>Loading standings...</span>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-red-400 font-mono text-xs">
              {error}
            </div>
          ) : standings.length === 0 ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs">
              No completed matches recorded yet. Play a match to set the high score!
            </div>
          ) : (
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-slate-400 border-b border-slate-800 sticky top-0 bg-slate-900">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Team</th>
                  <th className="py-2.5 px-3">Scenario</th>
                  <th className="py-2.5 px-3">Score</th>
                  <th className="py-2.5 px-3">Grade</th>
                  <th className="py-2.5 px-3">Completed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {standings.map((entry) => {
                  let rankBadge = `#${entry.rank}`;
                  if (entry.rank === 1) rankBadge = "🥇 1";
                  else if (entry.rank === 2) rankBadge = "🥈 2";
                  else if (entry.rank === 3) rankBadge = "🥉 3";

                  let gradeClass = "bg-slate-800 text-slate-300";
                  if (entry.total_score >= 90)
                    gradeClass = "bg-amber-500/20 text-amber-300 border border-amber-500/30";
                  else if (entry.total_score >= 75)
                    gradeClass = "bg-blue-500/20 text-blue-300 border border-blue-500/30";
                  else if (entry.total_score >= 60)
                    gradeClass = "bg-purple-500/20 text-purple-300 border border-purple-500/30";

                  let dateStr = "";
                  try {
                    const d = new Date(entry.completed_at);
                    dateStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                  } catch {
                    dateStr = entry.completed_at;
                  }

                  return (
                    <tr key={entry.session_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-3 font-bold text-amber-400">{rankBadge}</td>
                      <td className="py-3 px-3 font-semibold text-slate-100 font-sans">
                        {entry.team_name}
                      </td>
                      <td className="py-3 px-3 text-slate-400 truncate max-w-[160px]">
                        {entry.scenario_title}
                      </td>
                      <td className="py-3 px-3 font-bold text-slate-100">
                        {entry.total_score}{" "}
                        <span className="text-slate-500 font-normal text-[10px]">/ 100</span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${gradeClass}`}>
                          {entry.grade.split(" ")[0]}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-500 text-[11px]">{dateStr}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex justify-between items-center">
          <button
            onClick={fetchStandings}
            className="text-xs font-mono text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={() => setIsLeaderboardOpen(false)}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-bold transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
