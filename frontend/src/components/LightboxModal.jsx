import React, { useEffect } from "react";
import { X, ChevronLeft, ChevronRight, Maximize2, Tag, Info } from "lucide-react";
import { useGameStore } from "../store/useGameStore";
import { useMultiplayerStore } from "../store/useMultiplayerStore";

export function LightboxModal() {
  const {
    scenario: gameScenario,
    activeEvidenceIndex,
    setActiveEvidenceIndex,
    isLightboxOpen,
    setIsLightboxOpen,
  } = useGameStore();

  const multiScenario = useMultiplayerStore((s) => s.scenario);
  const scenario = gameScenario || multiScenario;

  const items = scenario?.evidence_items || [];
  const currentItem = items[activeEvidenceIndex] || items[0];

  useEffect(() => {
    if (!isLightboxOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setIsLightboxOpen(false);
      } else if (e.key === "ArrowLeft") {
        setActiveEvidenceIndex((activeEvidenceIndex - 1 + items.length) % items.length);
      } else if (e.key === "ArrowRight") {
        setActiveEvidenceIndex((activeEvidenceIndex + 1) % items.length);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isLightboxOpen, activeEvidenceIndex, items.length, setActiveEvidenceIndex, setIsLightboxOpen]);

  if (!isLightboxOpen || !currentItem) return null;

  const handlePrev = (e) => {
    e.stopPropagation();
    setActiveEvidenceIndex((activeEvidenceIndex - 1 + items.length) % items.length);
  };

  const handleNext = (e) => {
    e.stopPropagation();
    setActiveEvidenceIndex((activeEvidenceIndex + 1) % items.length);
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-md flex flex-col items-center justify-between p-4 sm:p-6 animate-fade-in"
      onClick={() => setIsLightboxOpen(false)}
    >
      {/* Top Header */}
      <div
        className="w-full max-w-6xl flex items-center justify-between pb-3 border-b border-slate-800"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 rounded-lg bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/30">
            Feed {activeEvidenceIndex + 1} of {items.length}
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700 font-semibold">
            {currentItem.badge}
          </span>
          <h2 className="text-base sm:text-lg font-bold text-slate-100 font-mono truncate max-w-md">
            {currentItem.title}
          </h2>
        </div>

        <button
          onClick={() => setIsLightboxOpen(false)}
          className="p-2 rounded-xl bg-slate-800/80 hover:bg-rose-500 text-slate-300 hover:text-white transition cursor-pointer border border-slate-700/80"
          title="Close (Esc)"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Image Display with Navigation */}
      <div
        className="relative w-full max-w-6xl flex-1 my-4 flex items-center justify-center overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handlePrev}
          className="absolute left-2 sm:left-4 z-20 w-12 h-12 rounded-full bg-slate-900/80 hover:bg-blue-600 text-white border border-slate-700 flex items-center justify-center transition shadow-2xl hover:scale-105 active:scale-95 cursor-pointer"
          title="Previous Evidence (Left Arrow)"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>

        <div className="w-full h-full flex items-center justify-center p-2">
          <img
            src={currentItem.src}
            alt={currentItem.title}
            className="max-w-full max-h-[72vh] object-contain rounded-xl shadow-2xl border border-slate-800"
            onError={(e) => {
              if (!e.target.src.includes("..")) {
                e.target.src = "../" + currentItem.src.replace(/^\//, "");
              }
            }}
          />
        </div>

        <button
          onClick={handleNext}
          className="absolute right-2 sm:right-4 z-20 w-12 h-12 rounded-full bg-slate-900/80 hover:bg-blue-600 text-white border border-slate-700 flex items-center justify-center transition shadow-2xl hover:scale-105 active:scale-95 cursor-pointer"
          title="Next Evidence (Right Arrow)"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>

      {/* Footer Info Box */}
      <div
        className="w-full max-w-6xl bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row gap-4 items-start justify-between"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-1 space-y-1.5">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Tag className="w-3.5 h-3.5 text-blue-400" />
            <span>Category: <span className="text-slate-200 font-semibold">{currentItem.category}</span></span>
            {currentItem.timestamp && (
              <span className="ml-2 text-blue-400">• Time: {currentItem.timestamp}</span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-300 font-mono leading-relaxed">
            {currentItem.description}
          </p>
        </div>

        {currentItem.ocr_ledger && (
          <div className="w-full md:w-80 shrink-0 bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-xs text-slate-400">
            <div className="text-[11px] text-blue-400 font-bold mb-1 flex items-center gap-1">
              <Info className="w-3.5 h-3.5" /> High-Fidelity OCR Ledger
            </div>
            <div className="line-clamp-3 hover:line-clamp-none transition text-[11px] text-slate-300">
              {currentItem.ocr_ledger}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
