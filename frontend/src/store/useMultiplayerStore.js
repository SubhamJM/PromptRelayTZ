import { create } from "zustand";
import { api } from "../api/client";
import { useGameStore } from "./useGameStore";

let wsPingTimer = null;
let wsReconnectTimer = null;

export const useMultiplayerStore = create((set, get) => ({
  // Server discovery
  serverInfo: null,

  // Room & Player Identity
  roomCode: "",
  teamName: "",
  myRole: "player_1", // "player_1" | "player_2" | "player_3"
  myPlayerName: "",
  room: null,
  scenario: null,
  joinUrl: "",
  showPartyCreatedModal: false,

  // Prompting Workspace
  myPrompt: "",
  isLockedIn: false,
  peerTyping: {
    player_1: false,
    player_2: false,
    player_3: false,
  },

  // WebSocket Connection
  socket: null,
  wsConnected: false,

  // Live Relay Execution Progress
  executionProgress: {
    currentStep: 0, // 1: Agent 1, 2: Agent 2, 3: Agent 3, 4: Evaluation
    agentName: "",
    step1Output: "",
    step2Output: "",
    step3Output: "",
    finalVerdict: null,
    evaluation: null,
  },

  isLoading: false,
  error: null,

  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  setMyPrompt: (prompt) => set({ myPrompt: prompt }),
  openPartyCreatedModal: () => set({ showPartyCreatedModal: true }),
  closePartyCreatedModal: () => set({ showPartyCreatedModal: false }),

  getJoinUrl: () => {
    const { roomCode, serverInfo } = get();
    if (!roomCode) return "";

    const isLocalhost =
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1";

    // When deployed to Render or any public host, always use the active web origin
    if (!isLocalhost) {
      return `${window.location.origin}?room=${roomCode}`;
    }

    const hostIp = serverInfo?.local_ip;
    const currentPort = window.location.port ? `:${window.location.port}` : "";
    if (hostIp) {
      return `${window.location.protocol}//${hostIp}${currentPort}?room=${roomCode}`;
    }
    return `${window.location.origin}?room=${roomCode}`;
  },

  // 1. Fetch server LAN IP
  fetchServerInfo: async () => {
    try {
      const info = await api.getServerInfo();
      set({ serverInfo: info });
      return info;
    } catch (err) {
      console.warn("Could not fetch server LAN info:", err);
      return null;
    }
  },

  // 2. Create room as Host
  createRoom: async ({ teamName, scenarioId, playerName, role }) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.createRoom({
        team_name: teamName,
        scenario_id: scenarioId,
        host_player_name: playerName,
        host_role: role,
      });

      const room = data.room;
      const hostIp = data.local_ip || get().serverInfo?.local_ip;
      const currentPort = window.location.port ? `:${window.location.port}` : "";
      const isLocalhost =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1";

      let computedJoinUrl = "";
      if (!isLocalhost) {
        computedJoinUrl = `${window.location.origin}?room=${room.room_code}`;
      } else if (data.join_url && !data.join_url.includes("127.0.0.1") && !data.join_url.includes("localhost")) {
        computedJoinUrl = data.join_url;
      } else if (hostIp) {
        computedJoinUrl = `${window.location.protocol}//${hostIp}${currentPort}?room=${room.room_code}`;
      } else {
        computedJoinUrl = `${window.location.origin}?room=${room.room_code}`;
      }

      set({
        roomCode: room.room_code,
        teamName: room.team_name,
        myRole: role,
        myPlayerName: playerName,
        room,
        scenario: data.scenario,
        joinUrl: computedJoinUrl,
        showPartyCreatedModal: true,
        isLoading: false,
        isLockedIn: false,
      });

      // Synchronize scenario into useGameStore for EvidenceViewer & LightboxModal
      if (data.scenario) {
        useGameStore.setState({ scenario: data.scenario });
      }

      // Connect WebSocket
      get().connectWebSocket(room.room_code, role);
      return room;
    } catch (err) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  // 3. Join room as Player
  joinRoom: async ({ roomCode, role, playerName }) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.joinRoom({
        room_code: roomCode,
        role,
        player_name: playerName,
      });

      const room = data.room;
      set({
        roomCode: room.room_code,
        teamName: room.team_name,
        myRole: role,
        myPlayerName: playerName,
        room,
        scenario: data.scenario,
        showPartyCreatedModal: false,
        isLoading: false,
        isLockedIn: false,
      });

      // Synchronize scenario into useGameStore for EvidenceViewer & LightboxModal
      if (data.scenario) {
        useGameStore.setState({ scenario: data.scenario });
      }

      // Connect WebSocket
      get().connectWebSocket(room.room_code, role);
      return room;
    } catch (err) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  // 4. WebSocket Manager
  connectWebSocket: (roomCode, role) => {
    if (wsPingTimer) {
      clearInterval(wsPingTimer);
      wsPingTimer = null;
    }
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = null;
    }

    const existingSocket = get().socket;
    if (existingSocket) {
      existingSocket.close();
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/rooms/${roomCode}/${role}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      set({ wsConnected: true, socket: ws });
      // Start ping heartbeat every 20s to prevent Render 55s proxy timeout
      wsPingTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.send(JSON.stringify({ type: "PING" }));
          } catch {
            // Socket closing
          }
        }
      }, 20000);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { type } = msg;

        if (type === "PONG") {
          // Heartbeat acknowledged by server
          return;
        }

        if (type === "ROOM_UPDATED") {
          const room = msg.room;
          set({ room });

          // Sync lock-in status of current user
          const mySlot = room.slots?.[get().myRole];
          if (mySlot) {
            set({ isLockedIn: mySlot.is_ready });
          }
        } else if (type === "PROMPTING_STARTED") {
          set({ room: msg.room });
        } else if (type === "PLAYER_TYPING") {
          const { role: typingRole, is_typing } = msg;
          set((state) => ({
            peerTyping: {
              ...state.peerTyping,
              [typingRole]: is_typing,
            },
          }));
        } else if (type === "EXECUTION_STARTED") {
          set((state) => ({
            room: state.room ? { ...state.room, status: "executing" } : null,
            executionProgress: {
              currentStep: 1,
              agentName: "Agent 1: Evidence Extractor",
              step1Output: "",
              step2Output: "",
              step3Output: "",
              finalVerdict: null,
              evaluation: null,
            },
          }));
        } else if (type === "STEP_STARTED") {
          set((state) => ({
            executionProgress: {
              ...state.executionProgress,
              currentStep: msg.step,
              agentName: msg.agent_name || `Agent ${msg.step}`,
            },
          }));
        } else if (type === "STEP_DONE") {
          set((state) => {
            const nextProgress = { ...state.executionProgress };
            if (msg.step === 1) nextProgress.step1Output = msg.output;
            if (msg.step === 2) nextProgress.step2Output = msg.output;
            if (msg.step === 3) {
              nextProgress.step3Output = msg.output;
              nextProgress.finalVerdict = msg.final_verdict;
            }
            return { executionProgress: nextProgress };
          });
        } else if (type === "EVALUATION_STARTED") {
          set((state) => ({
            executionProgress: {
              ...state.executionProgress,
              currentStep: 4,
              agentName: "Evaluating Relay Scoring & Rules Compliance...",
            },
          }));
        } else if (type === "MATCH_COMPLETED") {
          const { evaluation, final_verdict, room } = msg;
          set((state) => ({
            room: room || state.room,
            executionProgress: {
              ...state.executionProgress,
              currentStep: 4,
              finalVerdict: final_verdict,
              evaluation,
            },
          }));

          // Also populate GameStore so ResultsScreen can read it if navigated
          useGameStore.setState({
            teamName: get().teamName,
            scenario: get().scenario,
            p1Prompt: room?.slots?.player_1?.prompt || "",
            a1Output: room?.a1_output || "",
            p2Prompt: room?.slots?.player_2?.prompt || "",
            a2Output: room?.a2_output || "",
            p3Prompt: room?.slots?.player_3?.prompt || "",
            finalVerdict: final_verdict,
            evaluation,
          });
        }
      } catch (e) {
        console.error("Error parsing WebSocket message:", e);
      }
    };

    ws.onclose = () => {
      if (wsPingTimer) {
        clearInterval(wsPingTimer);
        wsPingTimer = null;
      }
      set({ wsConnected: false, socket: null });

      // Auto-reconnect if dropped while in an active room
      const state = get();
      if (state.roomCode && state.myRole && state.room?.status !== "completed") {
        wsReconnectTimer = setTimeout(() => {
          const currentState = get();
          if (currentState.roomCode && currentState.myRole && !currentState.wsConnected) {
            currentState.connectWebSocket(currentState.roomCode, currentState.myRole);
          }
        }, 2000);
      }
    };

    ws.onerror = (err) => {
      console.warn("WebSocket error:", err);
      if (wsPingTimer) {
        clearInterval(wsPingTimer);
        wsPingTimer = null;
      }
      set({ wsConnected: false });
    };
  },

  // 5. User Actions
  startPrompting: () => {
    const { socket } = get();
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "START_PROMPTING" }));
    }
  },

  sendTyping: (isTyping) => {
    const { socket } = get();
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "TYPING", is_typing: isTyping }));
    }
  },

  lockInPrompt: () => {
    const { socket, myPrompt } = get();
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "LOCK_IN", prompt: myPrompt }));
      set({ isLockedIn: true });
    }
  },

  unlockPrompt: () => {
    const { socket } = get();
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "UNLOCK" }));
      set({ isLockedIn: false });
    }
  },

  disconnect: () => {
    if (wsPingTimer) {
      clearInterval(wsPingTimer);
      wsPingTimer = null;
    }
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = null;
    }
    const { socket } = get();
    if (socket) {
      socket.close();
    }
    set({
      roomCode: "",
      teamName: "",
      myRole: "",
      myPlayerName: "",
      room: null,
      socket: null,
      wsConnected: false,
      isLockedIn: false,
      myPrompt: "",
      joinUrl: "",
      showPartyCreatedModal: false,
    });
  },
}));
