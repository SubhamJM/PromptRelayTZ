import { create } from "zustand";
import { api } from "../api/client";

const STORAGE_KEY = "prompt_relay_session_id";

export const useGameStore = create((set, get) => ({
  // Active Match State
  sessionId: localStorage.getItem(STORAGE_KEY) || null,
  teamName: "",
  scenario: null,
  currentStep: "welcome", // welcome, step1, handoff1, step2, handoff2, step3, completed

  p1Prompt: "",
  a1Output: "",
  p2Prompt: "",
  a2Output: "",
  p3Prompt: "",
  finalVerdict: null,
  evaluation: null,

  // UI Transient State
  isLoading: false,
  loadingText: "Running Agent...",
  error: null,
  activeEvidenceIndex: 0,
  evidenceFilter: "all",
  isLightboxOpen: false,
  isLeaderboardOpen: false,
  isAdminOpen: false,

  // Setters
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  setLoading: (isLoading, loadingText = "Running Agent...") =>
    set({ isLoading, loadingText }),
  setActiveEvidenceIndex: (activeEvidenceIndex) => set({ activeEvidenceIndex }),
  setEvidenceFilter: (evidenceFilter) => set({ evidenceFilter }),
  setIsLightboxOpen: (isLightboxOpen) => set({ isLightboxOpen }),
  setIsLeaderboardOpen: (isLeaderboardOpen) => set({ isLeaderboardOpen }),
  setIsAdminOpen: (isAdminOpen) => set({ isAdminOpen }),

  // Match Actions
  startGame: async (teamName, scenarioId) => {
    set({ isLoading: true, loadingText: "Initializing Scenario...", error: null });
    try {
      const data = await api.startGame(teamName, scenarioId);
      localStorage.setItem(STORAGE_KEY, data.session_id);
      set({
        sessionId: data.session_id,
        teamName: data.team_name,
        scenario: data.scenario,
        currentStep: "step1",
        p1Prompt: "",
        a1Output: "",
        p2Prompt: "",
        a2Output: "",
        p3Prompt: "",
        finalVerdict: null,
        evaluation: null,
        activeEvidenceIndex: 0,
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  submitStep1: async (prompt) => {
    const { sessionId } = get();
    set({ isLoading: true, loadingText: "Agent 1 is filtering evidence...", error: null });
    try {
      const data = await api.submitStep1(sessionId, prompt);
      set({
        p1Prompt: prompt,
        a1Output: data.a1_output,
        currentStep: "handoff1",
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  acknowledgeHandoff1: () => {
    set({ currentStep: "step2", activeEvidenceIndex: 0 });
  },

  submitStep2: async (prompt) => {
    const { sessionId } = get();
    set({ isLoading: true, loadingText: "Agent 2 is reconstructing timeline...", error: null });
    try {
      const data = await api.submitStep2(sessionId, prompt);
      set({
        p2Prompt: prompt,
        a2Output: data.a2_output,
        currentStep: "handoff2",
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  acknowledgeHandoff2: () => {
    set({ currentStep: "step3", activeEvidenceIndex: 0 });
  },

  submitStep3: async (prompt) => {
    const { sessionId } = get();
    set({ isLoading: true, loadingText: "Agent 3 is solving & evaluating match...", error: null });
    try {
      const data = await api.submitStep3(sessionId, prompt);
      set({
        p1Prompt: data.p1_prompt || get().p1Prompt || data.evaluation?.p1_prompt || "",
        a1Output: data.a1_output || get().a1Output || data.evaluation?.a1_output || "",
        p2Prompt: data.p2_prompt || get().p2Prompt || data.evaluation?.p2_prompt || "",
        a2Output: data.a2_output || get().a2Output || data.evaluation?.a2_output || "",
        p3Prompt: data.p3_prompt || prompt || data.evaluation?.p3_prompt || "",
        finalVerdict: data.final_verdict || data.evaluation?.final_verdict || null,
        evaluation: data.evaluation,
        currentStep: "completed",
        isLoading: false,
      });
    } catch (err) {
      set({ error: err.message, isLoading: false });
    }
  },

  recoverActiveSession: async () => {
    const { sessionId } = get();
    if (!sessionId) return;

    set({ isLoading: true, loadingText: "Restoring active session..." });
    try {
      const data = await api.recoverSession(sessionId);
      set({
        sessionId: data.session_id,
        teamName: data.team_name,
        scenario: data.scenario,
        currentStep: data.current_step,
        p1Prompt: data.p1_prompt || data.evaluation?.p1_prompt || "",
        a1Output: data.a1_output || data.evaluation?.a1_output || "",
        p2Prompt: data.p2_prompt || data.evaluation?.p2_prompt || "",
        a2Output: data.a2_output || data.evaluation?.a2_output || "",
        p3Prompt: data.p3_prompt || data.evaluation?.p3_prompt || "",
        finalVerdict: data.final_verdict || data.evaluation?.final_verdict || null,
        evaluation: data.evaluation || null,
        isLoading: false,
      });
    } catch {
      // If session not found or invalid, clear storage
      localStorage.removeItem(STORAGE_KEY);
      set({ sessionId: null, currentStep: "welcome", isLoading: false });
    }
  },

  resetMatch: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({
      sessionId: null,
      teamName: "",
      scenario: null,
      currentStep: "welcome",
      p1Prompt: "",
      a1Output: "",
      p2Prompt: "",
      a2Output: "",
      p3Prompt: "",
      finalVerdict: null,
      evaluation: null,
      error: null,
      activeEvidenceIndex: 0,
    });
  },
}));
