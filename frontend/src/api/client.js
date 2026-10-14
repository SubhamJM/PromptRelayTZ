const API_BASE = "/api";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `Server error (${response.status})`;
    try {
      const errJson = await response.json();
      errorMsg = errJson.detail || errorMsg;
    } catch {
      const text = await response.text();
      if (text) errorMsg = text;
    }
    throw new Error(errorMsg);
  }

  return response.json();
}

export const api = {
  // Scenarios
  getScenarios: () => request("/game/scenarios"),
  getScenario: (id) => request(`/game/scenarios/${id}`),

  // Game Lifecycle
  startGame: (teamName, scenarioId) =>
    request("/game/start", {
      method: "POST",
      body: JSON.stringify({ team_name: teamName, scenario_id: scenarioId }),
    }),

  recoverSession: (sessionId) => request(`/game/session/${sessionId}`),

  submitStep1: (sessionId, prompt) =>
    request("/game/step1", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, prompt }),
    }),

  submitStep2: (sessionId, prompt) =>
    request("/game/step2", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, prompt }),
    }),

  submitStep3: (sessionId, prompt) =>
    request("/game/step3", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, prompt }),
    }),

  getLeaderboard: () => request("/game/leaderboard"),

  // Organizer Admin
  getAdminStats: () => request("/admin/stats"),
  getAdminMatches: () => request("/admin/matches"),
  getAdminMatch: (sessionId) => request(`/admin/matches/${sessionId}`),
  deleteAdminMatch: (sessionId) =>
    request(`/admin/matches/${sessionId}`, { method: "DELETE" }),
  getLLMStatus: () => request("/admin/llm/status"),
  configureLLM: (config) =>
    request("/admin/llm/configure", {
      method: "POST",
      body: JSON.stringify(config),
    }),
  resetTournament: () => request("/admin/reset", { method: "POST" }),
};
