import React, { useEffect, useState } from "react";
import { ArrowRight, Plane, Landmark, CheckCircle2 } from "lucide-react";
import { api } from "../api/client";
import { useGameStore } from "../store/useGameStore";

export function WelcomeScreen() {
  const { startGame, isLoading } = useGameStore();
  const [teamName, setTeamName] = useState("");
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("scenario_01_airport_crisis");

  useEffect(() => {
    api
      .getScenarios()
      .then((list) => {
        setScenarios(list);
        // Default to airport crisis if present, else first scenario
        const airport = list.find((s) => s.id === "scenario_01_airport_crisis");
        if (airport) {
          setSelectedScenarioId(airport.id);
        } else if (list.length > 0) {
          setSelectedScenarioId(list[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const handleStart = (e) => {
    e.preventDefault();
    if (!teamName.trim()) {
      alert("Please enter a team name.");
      return;
    }
    startGame(teamName, selectedScenarioId);
  };

  const activeScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0] || {};

  return (
    <section className="space-y-8 animate-fade-in max-w-4xl mx-auto w-full py-4">
      {/* Title & Introduction */}
      <div className="text-center space-y-3">
        <div className="inline-block px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono font-semibold tracking-wider uppercase">
          3-Agent Prompt Engineering Relay Challenge
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 font-serif tracking-tight">
          Orchestrate 3 Specialized AI Agents in a Relay
        </h2>
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
          Teams of 3 prompt engineers take turns crafting instructions. The output of Agent 1
          feeds Agent 2, whose output feeds Agent 3. Score is evaluated on individual prompt engineering
          quality (60 pts) and final case accuracy (40 pts).
        </p>
      </div>

      {/* Rules Preview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between mb-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 font-mono text-sm font-bold">
              1
            </div>
            <span className="px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/30 text-[10px] font-mono text-blue-300 font-semibold">
              👁️ Vision / OCR Ledger
            </span>
          </div>
          <h3 className="font-bold text-slate-200 text-sm mb-1">Player 1: Evidence Extractor</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Directs Agent 1 to extract facts, times, locations, and movements while separating confirmed
            from uncertain items without making premature inferences.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between mb-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 font-mono text-sm font-bold">
              2
            </div>
            <span className="px-2 py-0.5 rounded bg-purple-500/15 border border-purple-500/30 text-[10px] font-mono text-purple-300 font-semibold">
              🕸️ Chronological Graph
            </span>
          </div>
          <h3 className="font-bold text-slate-200 text-sm mb-1">Player 2: Reconstructor</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Sees <strong>only</strong> Agent 1's facts and prompts Agent 2 to reconstruct chronological
            sequences and causal dependencies, keeping uncertainties separate.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between mb-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-mono text-sm font-bold">
              3
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-[10px] font-mono text-emerald-300 font-semibold">
              ⚙️ Logic Constraint Solver
            </span>
          </div>
          <h3 className="font-bold text-slate-200 text-sm mb-1">Player 3: Logic Solver</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Sees <strong>only</strong> Agent 2's timeline and prompts Agent 3 to evaluate rules and
            deduce valid operational actions and blocking conditions in strict JSON.
          </p>
        </div>
      </div>

      {/* Registration & Scenario Selection Form */}
      <form
        onSubmit={handleStart}
        className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6"
      >
        <div>
          <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider mb-2">
            Team Name (3-Person Prompt Squad)
          </label>
          <input
            type="text"
            required
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            placeholder="e.g. Flight 472 Response Unit or Baker Street Trio"
            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition text-sm font-mono"
          />
        </div>

        {/* Challenge Scenario Selector */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-xs font-mono text-slate-300 uppercase tracking-wider">
              Select Visual Investigation Case
            </label>
            <span className="text-[11px] font-mono text-blue-400 font-semibold">
              2 Visual Cases Available
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Story 1: Airport Crisis */}
            <div
              onClick={() => setSelectedScenarioId("scenario_01_airport_crisis")}
              className={`cursor-pointer rounded-2xl p-5 transition flex flex-col justify-between space-y-3 ${
                selectedScenarioId === "scenario_01_airport_crisis"
                  ? "border-2 border-blue-500 bg-blue-950/30 shadow-lg shadow-blue-500/15 ring-1 ring-blue-500/30"
                  : "border border-slate-800 bg-slate-950/70 hover:bg-slate-850 hover:border-slate-700"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2.5 py-1 rounded bg-blue-500/20 text-blue-300 font-mono text-[10px] font-bold border border-blue-500/30 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                    CASE 01 • AIRPORT CRISIS
                  </span>
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center ${
                      selectedScenarioId === "scenario_01_airport_crisis"
                        ? "bg-blue-400 ring-4 ring-blue-500/30"
                        : "bg-slate-700"
                    }`}
                  >
                    {selectedScenarioId === "scenario_01_airport_crisis" && (
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />
                    )}
                  </span>
                </div>
                <h4 className="font-bold text-slate-100 text-base flex items-center gap-2">
                  <Plane className="w-4 h-4 text-blue-400 shrink-0" />
                  <span>Flight SW 472: Baggage Contraband</span>
                </h4>
                <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
                  Surveillance CCTV feeds, digital boarding monitors, passenger WhatsApp chats,
                  security logs, and physical luggage tags at Gate B07.
                </p>
              </div>

              {/* Photo Previews */}
              <div className="pt-3 border-t border-blue-500/20 flex items-center gap-2 overflow-hidden">
                <img
                  src="/image_data/01_cctv_checkin.png"
                  alt="CCTV"
                  className="w-14 h-8 object-cover rounded border border-blue-500/40 shrink-0"
                />
                <img
                  src="/image_data/04_flight_display.png"
                  alt="FIDS"
                  className="w-14 h-8 object-cover rounded border border-blue-500/40 shrink-0"
                />
                <img
                  src="/image_data/05_passenger_messages.png"
                  alt="Chat"
                  className="w-14 h-8 object-cover rounded border border-blue-500/40 shrink-0"
                />
                <img
                  src="/image_data/09_baggage_tag.png"
                  alt="Tag"
                  className="w-14 h-8 object-cover rounded border border-blue-500/40 shrink-0"
                />
                <span className="text-[10px] font-mono text-blue-300 font-bold ml-1">+6 more</span>
              </div>
            </div>

            {/* Story 2: Museum Heist */}
            <div
              onClick={() => setSelectedScenarioId("scenario_05_museum_heist")}
              className={`cursor-pointer rounded-2xl p-5 transition flex flex-col justify-between space-y-3 ${
                selectedScenarioId === "scenario_05_museum_heist"
                  ? "border-2 border-amber-500 bg-amber-950/30 shadow-lg shadow-amber-500/15 ring-1 ring-amber-500/30"
                  : "border border-slate-800 bg-slate-950/70 hover:bg-slate-850 hover:border-slate-700"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold border border-amber-500/30 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                    CASE 02 • MUSEUM HEIST
                  </span>
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center ${
                      selectedScenarioId === "scenario_05_museum_heist"
                        ? "bg-amber-400 ring-4 ring-amber-500/30"
                        : "bg-slate-700"
                    }`}
                  >
                    {selectedScenarioId === "scenario_05_museum_heist" && (
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />
                    )}
                  </span>
                </div>
                <h4 className="font-bold text-slate-100 text-base flex items-center gap-2">
                  <Landmark className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>The Celestial Madonna: Museum Heist</span>
                </h4>
                <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
                  CCTV Wing C & basement feeds, SCADA power telemetry, lab spectrometry,
                  architectural blueprints, and evidence locker tokens.
                </p>
              </div>

              {/* Photo Previews */}
              <div className="pt-3 border-t border-amber-500/20 flex items-center gap-2 overflow-hidden">
                <img
                  src="/images_for_museum/01_cctv_gallery.png"
                  alt="CAM-04"
                  className="w-14 h-8 object-cover rounded border border-amber-500/40 shrink-0"
                />
                <img
                  src="/images_for_museum/02_scada_console.png"
                  alt="SCADA"
                  className="w-14 h-8 object-cover rounded border border-amber-500/40 shrink-0"
                />
                <img
                  src="/images_for_museum/04_conservation_lab.png"
                  alt="Lab"
                  className="w-14 h-8 object-cover rounded border border-amber-500/40 shrink-0"
                />
                <img
                  src="/images_for_museum/09_evidence_locker14.png"
                  alt="Locker 14"
                  className="w-14 h-8 object-cover rounded border border-amber-500/40 shrink-0"
                />
                <span className="text-[10px] font-mono text-amber-300 font-bold ml-1">+6 more</span>
              </div>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-4 px-6 rounded-xl bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold text-sm transition transform active:scale-[0.98] shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
        >
          <span>
            Launch {selectedScenarioId === "scenario_05_museum_heist" ? "Museum Heist Investigation" : "Flight 472 Operation"}
          </span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </section>
  );
}
