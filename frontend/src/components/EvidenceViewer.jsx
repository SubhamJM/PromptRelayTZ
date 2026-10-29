import React from "react";
import { ChevronLeft, ChevronRight, ZoomIn } from "lucide-react";
import { useGameStore } from "../store/useGameStore";
import { useMultiplayerStore } from "../store/useMultiplayerStore";

export function EvidenceViewer({ isStep1 = false, isStep2 = false, isStep3 = false }) {
  const {
    scenario: gameScenario,
    activeEvidenceIndex,
    setActiveEvidenceIndex,
    evidenceFilter,
    setEvidenceFilter,
    setIsLightboxOpen,
  } = useGameStore();

  const multiScenario = useMultiplayerStore((s) => s.scenario);
  const scenario = gameScenario || multiScenario;

  if (!scenario) return null;

  const items = scenario.evidence_items || [];

  // Dynamic theme colors based on role
  const theme = isStep3
    ? {
        border: "border-emerald-500/40",
        feedBadge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
        badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
        zoomBtn: "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border-emerald-500/40",
        hintBox: "from-emerald-950/60 to-slate-900 border-emerald-500/30",
        hintLabel: "text-emerald-300",
        activeFilter: "bg-emerald-500 text-slate-950 shadow-sm",
        activeThumb: "border-2 border-emerald-400 ring-2 ring-emerald-500/40 bg-slate-900 shadow-md",
        thumbHover: "hover:border-emerald-500/50",
      }
    : isStep2
    ? {
        border: "border-purple-500/40",
        feedBadge: "bg-purple-500/20 text-purple-300 border-purple-500/30",
        badge: "bg-purple-500/20 text-purple-300 border-purple-500/40",
        zoomBtn: "bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border-purple-500/40",
        hintBox: "from-purple-950/60 to-slate-900 border-purple-500/30",
        hintLabel: "text-purple-300",
        activeFilter: "bg-purple-500 text-slate-950 shadow-sm",
        activeThumb: "border-2 border-purple-400 ring-2 ring-purple-500/40 bg-slate-900 shadow-md",
        thumbHover: "hover:border-purple-500/50",
      }
    : {
        border: "border-blue-500/40",
        feedBadge: "bg-blue-500/20 text-blue-300 border-blue-500/30",
        badge: "bg-blue-500/20 text-blue-300 border-blue-500/40",
        zoomBtn: "bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border-blue-500/40",
        hintBox: "from-blue-950/60 to-slate-900 border-blue-500/30",
        hintLabel: "text-blue-300",
        activeFilter: "bg-blue-500 text-slate-950 shadow-sm",
        activeThumb: "border-2 border-blue-400 ring-2 ring-blue-500/40 bg-slate-900 shadow-md",
        thumbHover: "hover:border-blue-500/50",
      };

  // Dynamic categories for evidence items
  const dynamicCategories = [
    "all",
    ...Array.from(new Set(items.map((item) => item.category).filter(Boolean))),
  ];

  // Filter items
  const filteredItems = items.filter((item) => {
    if (evidenceFilter === "all") return true;
    return item.category === evidenceFilter;
  });

  const activeItem = items[activeEvidenceIndex] || items[0] || {};

  const handlePrev = (e) => {
    e?.stopPropagation();
    setActiveEvidenceIndex((activeEvidenceIndex - 1 + items.length) % items.length);
  };

  const handleNext = (e) => {
    e?.stopPropagation();
    setActiveEvidenceIndex((activeEvidenceIndex + 1) % items.length);
  };

  return (
    <div className="space-y-4">
      <div className={`rounded-2xl border ${theme.border} bg-slate-900/90 shadow-2xl overflow-hidden`}>
        {/* Header Bar */}
        <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <span className={`px-2 py-0.5 rounded ${theme.feedBadge} font-mono text-xs font-bold border`}>
              Feed {activeEvidenceIndex + 1} of {items.length}
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${theme.badge} border truncate`}>
              {activeItem.badge}
            </span>
            <h3 className="text-xs sm:text-sm font-bold text-slate-100 font-mono truncate">
              {activeItem.title}
            </h3>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={handlePrev}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-bold transition flex items-center gap-1 cursor-pointer"
              title="Previous Feed"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Prev</span>
            </button>
            <button
              onClick={handleNext}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-bold transition flex items-center gap-1 cursor-pointer"
              title="Next Feed"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setIsLightboxOpen(true)}
              className={`px-2.5 py-1 rounded-lg ${theme.zoomBtn} text-xs font-mono font-bold transition cursor-pointer flex items-center gap-1`}
              title="Click to Zoom Fullscreen"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Main Image Container */}
        <div
          onClick={() => setIsLightboxOpen(true)}
          className="relative w-full aspect-[2/1] overflow-hidden bg-slate-950 flex items-center justify-center p-1 group cursor-pointer"
          title="Click image to zoom fullscreen"
        >
          <button
            onClick={handlePrev}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-slate-900/85 hover:bg-blue-600 text-white border border-slate-700 flex items-center justify-center transition shadow-xl font-bold cursor-pointer hover:scale-105 active:scale-95"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <img
            src={activeItem.src}
            alt={activeItem.title}
            className="w-full h-full object-contain rounded transition duration-200"
            onError={(e) => {
              if (!e.target.src.includes("..")) {
                e.target.src = "../" + activeItem.src.replace(/^\//, "");
              }
            }}
          />

          <button
            onClick={handleNext}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-slate-900/85 hover:bg-blue-600 text-white border border-slate-700 flex items-center justify-center transition shadow-xl font-bold cursor-pointer hover:scale-105 active:scale-95"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-slate-950/80 text-[10px] font-mono text-slate-300 border border-slate-700/60 opacity-80 group-hover:opacity-100 transition flex items-center gap-1">
            <ZoomIn className="w-3 h-3" /> Click to zoom
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
        {dynamicCategories.map((filter) => (
          <button
            key={filter}
            onClick={() => setEvidenceFilter(filter)}
            className={`px-2.5 py-1 rounded-lg transition font-bold cursor-pointer ${
              evidenceFilter === filter
                ? theme.activeFilter
                : "bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
            }`}
          >
            {filter === "all" ? `All (${items.length})` : filter}
          </button>
        ))}
      </div>

      {/* Thumbnail Strip */}
      <div className="grid grid-cols-5 sm:grid-cols-5 gap-2 max-h-48 overflow-y-auto pr-1">
        {filteredItems.map((item) => {
          const itemIdx = items.findIndex((i) => i.id === item.id);
          return (
            <button
              key={item.id}
              onClick={() => setActiveEvidenceIndex(itemIdx)}
              className={`group relative cursor-pointer overflow-hidden rounded-xl p-1.5 space-y-1 transition text-left ${
                activeEvidenceIndex === itemIdx
                  ? theme.activeThumb
                  : `border border-slate-800 bg-slate-950/80 ${theme.thumbHover} opacity-75 hover:opacity-100`
              }`}
            >
              <div className="aspect-[2/1] w-full overflow-hidden rounded bg-slate-950 flex items-center justify-center">
                <img
                  src={item.src}
                  alt={item.title}
                  className="h-full w-full object-cover group-hover:scale-105 transition"
                />
              </div>
              <div className="truncate text-[10px] font-mono text-slate-300 font-semibold leading-tight">
                {itemIdx + 1}. {item.badge}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
