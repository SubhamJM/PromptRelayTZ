const API_BASE = "/api";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 40000);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
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
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out. The server took longer than 40s to respond. Please try again.");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
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

  // 3-Laptop Multiplayer Room Endpoints
  getServerInfo: () => request("/rooms/network/server-info"),
  createRoom: (payload) =>
    request("/rooms/create", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  joinRoom: (payload) =>
    request("/rooms/join", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getRoom: (roomCode) => request(`/rooms/${roomCode}`),
  startRoomPrompting: (roomCode) =>
    request(`/rooms/${roomCode}/start`, { method: "POST" }),
  lockInPrompt: (roomCode, role, prompt) =>
    request(`/rooms/${roomCode}/lock-in`, {
      method: "POST",
      body: JSON.stringify({ room_code: roomCode, role, prompt }),
    }),
};
