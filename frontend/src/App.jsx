import React, { useEffect } from "react";
import { Header } from "./components/Header";
import { HandoffModal } from "./components/HandoffModal";
import { LeaderboardModal } from "./components/LeaderboardModal";
import { AdminModal } from "./components/AdminModal";
import { LightboxModal } from "./components/LightboxModal";

import { WelcomeScreen } from "./screens/WelcomeScreen";
import { Step1Screen } from "./screens/Step1Screen";
import { Step2Screen } from "./screens/Step2Screen";
import { Step3Screen } from "./screens/Step3Screen";
import { ResultsScreen } from "./screens/ResultsScreen";

import { useGameStore } from "./store/useGameStore";
import { AlertTriangle, X, Loader2 } from "lucide-react";

export function App() {
  const {
    currentStep,
    isLoading,
    loadingText,
    error,
    clearError,
    recoverActiveSession,
  } = useGameStore();

  useEffect(() => {
    recoverActiveSession();
  }, [recoverActiveSession]);

  const renderActiveScreen = () => {
    switch (currentStep) {
      case "welcome":
        return <WelcomeScreen />;
      case "step1":
        return <Step1Screen />;
      case "handoff1":
      case "handoff2":
        // For handoffs, keep the previous step in background and show modal over it
        return (
          <>
            {currentStep === "handoff1" ? <Step1Screen /> : <Step2Screen />}
            <HandoffModal />
          </>
        );
      case "step2":
        return <Step2Screen />;
      case "step3":
        return <Step3Screen />;
      case "completed":
        return <ResultsScreen />;
      default:
        return <WelcomeScreen />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-500/30 selection:text-white">
      {/* Station Header */}
      <Header />

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-950/90 border-b border-rose-800 text-rose-200 px-4 py-3 font-mono text-xs sm:text-sm flex items-center justify-between shadow-xl animate-fade-in z-30">
          <div className="max-w-7xl mx-auto w-full flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={clearError}
              className="p-1 rounded-lg hover:bg-rose-900 text-rose-400 hover:text-rose-100 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main Screen Content */}
      <main className="flex-1 pb-16">
        {renderActiveScreen()}
      </main>

      {/* Modals */}
      <LeaderboardModal />
      <AdminModal />
      <LightboxModal />

      {/* Global High-Tech Loading Spinner Overlay */}
      {isLoading && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-4 animate-fade-in">
          <div className="bg-slate-900/90 border border-blue-500/30 rounded-2xl p-6 sm:p-8 flex flex-col items-center gap-4 shadow-2xl max-w-sm text-center">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
              <Loader2 className="w-6 h-6 text-blue-400 absolute inset-0 m-auto animate-pulse" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-bold text-white font-mono">
                Prompt Relay Engine
              </h3>
              <p className="text-xs font-mono text-blue-300 animate-pulse">
                {loadingText || "Processing agent workflow..."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
