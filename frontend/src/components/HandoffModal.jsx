import React from "react";
import { ArrowRight, RefreshCw, UserCheck } from "lucide-react";
import { useGameStore } from "../store/useGameStore";

export function HandoffModal() {
  const { currentStep, acknowledgeHandoff1, acknowledgeHandoff2 } = useGameStore();

  if (currentStep !== "handoff1" && currentStep !== "handoff2") {
    return null;
  }

  const isHandoff1 = currentStep === "handoff1";

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
      <div className="max-w-md w-full bg-slate-900 border border-purple-500/30 rounded-2xl p-8 text-center space-y-6 shadow-2xl">
        <div className="w-16 h-16 rounded-full bg-purple-500/10 border border-purple-500/40 mx-auto flex items-center justify-center text-3xl">
          <RefreshCw className="w-8 h-8 text-purple-400 animate-spin-slow" />
        </div>

        <div className="space-y-2">
          <span className="px-2.5 py-1 rounded bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-mono font-bold uppercase">
            {isHandoff1 ? "Step 1 Complete" : "Step 2 Complete"}
          </span>

          <h3 className="text-2xl font-bold text-slate-100 font-serif">
            {isHandoff1 ? "Hand Laptop to Player 2" : "Hand Laptop to Player 3"}
          </h3>

          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            {isHandoff1 ? (
              <>
                Player 1, please step away from the keyboard. Player 2, take the seat.
                You will see <strong>strictly the facts extracted by Agent 1</strong> without
                the original noisy story.
              </>
            ) : (
              <>
                Player 2, please step away. Player 3, take the seat.
                You will receive <strong>strictly Agent 2's chronological timeline</strong> along
                with operational rules to deduce the final decision.
              </>
            )}
          </p>
        </div>

        <button
          onClick={isHandoff1 ? acknowledgeHandoff1 : acknowledgeHandoff2}
          className="w-full py-3.5 px-6 rounded-xl bg-purple-500 hover:bg-purple-400 text-slate-950 font-bold text-sm transition transform active:scale-[0.98] shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2 cursor-pointer"
        >
          <UserCheck className="w-4 h-4" />
          <span>
            {isHandoff1 ? "I am Player 2 — Ready to Prompt" : "I am Player 3 — Ready to Deduce"}
          </span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
