# Prompt Relay: Render Deployment & 3-Laptop Multiplayer Guide

This guide details how to deploy **Prompt Relay** on [Render.com](https://render.com) so that 3 players on separate laptops anywhere can join the same party, collaborate in real time, and run simultaneous prompt engineering competitions.

---

## 🚀 Part 1: Deploying to Render (in < 3 Minutes)

The project includes a multi-stage [Dockerfile](file:///home/ricing/Documents/code/Projects/PromptRelay_v2/Dockerfile) and [render.yaml](file:///home/ricing/Documents/code/Projects/PromptRelay_v2/render.yaml) blueprint that builds the React frontend and serves both the API and client from a single unified service.

### Option A: Using Render Blueprints (Recommended)
1. Push your repository to GitHub.
2. Log in to [Render](https://dashboard.render.com).
3. Click **New +** in the top right and select **Blueprint**.
4. Connect your GitHub repository. Render will automatically detect `render.yaml`.
5. Under **Environment Variables**, set:
   * `GEMINI_API_KEY`: Your Google Gemini API Key.
6. Click **Apply**. Render will automatically build the container and deploy the app at `https://<your-app-name>.onrender.com`.

### Option B: Manual Web Service Setup
1. Log in to [Render](https://dashboard.render.com) and click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the following settings:
   * **Name**: `prompt-relay` (or any name you choose)
   * **Language / Environment**: `Docker`
   * **Branch**: `main`
   * **Region**: Choose the region closest to you (e.g., `Oregon`, `Frankfurt`, `Singapore`)
   * **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   * `GEMINI_API_KEY` = `your_actual_gemini_api_key`
   * `PROJECT_NAME` = `Prompt Relay: Multi-Agent Tournament`
5. Click **Create Web Service**.

> [!NOTE]
> Render's free tier spins down after 15 minutes of inactivity. When someone opens the link, it wakes up within ~30–45 seconds.

---

## 🎮 Part 2: 3-Laptop Party Playbook

Once deployed, follow these steps to play with 3 separate laptops:

### 1. Laptop 1 (Host Player): Create the Party
1. Open `https://<your-app-name>.onrender.com` in your browser.
2. Select **Multi-Laptop Relay** mode.
3. Enter your **Team Name** (e.g. `Apex Detectives`).
4. Enter your **Name** (e.g. `Alex`) and choose your role (e.g. `Seat 1: Player 1 - Evidence Extractor`).
5. Choose the case investigation:
   * **Flight SW 472**: The Airport Diamond Baggage Swap
   * **The Celestial Madonna**: The Riverton Museum Heist
6. Click **Create Team Room**.
7. In the lobby or modal, click **Copy Party Link for Teammates**.
   * It copies a direct URL: `https://<your-app-name>.onrender.com?room=ABCD`.

### 2. Laptops 2 & 3 (Teammates): Join via Link
1. Send the copied link to Player 2 and Player 3 (via Slack, WhatsApp, Discord, or email).
2. Player 2 and Player 3 open the link on their respective laptops.
   * **Automatic Pre-fill**: The 4-letter Room Code is filled automatically.
   * **Smart Seat Assignment**: Player 2 is automatically pre-assigned to **Seat 2 (Reconstructor)**, and Player 3 is pre-assigned to **Seat 3 (Logic Solver)**.
3. Each player enters their name and clicks **Join Team Room**.

### 3. Synchronized Live Room Lobby
* All 3 laptops update simultaneously in real time via secure WebSockets (`wss://`).
* Each laptop clearly displays:
  * Which seat belongs to this laptop (`Your Laptop - Active`).
  * Which seats are claimed by teammates with their names.
* When all 3 seats are occupied, the Host clicks **Launch Simultaneous Prompting Phase**.

### 4. Simultaneous Prompting & Execution
1. All 3 laptops transition together into their dedicated workspace:
   * **Player 1**: Inspects multi-source visual evidence and writes the extraction prompt.
   * **Player 2**: Analyzes the evidence and drafts the chronological timeline prompt.
   * **Player 3**: Reviews the case objective & rules and drafts the verdict prompt.
2. **Live Peer Indicators**: When a teammate is typing, a real-time typing indicator appears on everyone's screen.
3. **Lock In**: When each player finishes their prompt, they click **Lock In Prompt**.
4. Once all 3 players have locked in, the system automatically launches the **Relay Execution Theater**:
   * Agent 1 runs -> Agent 2 receives the extraction and runs -> Agent 3 deduces the final verdict -> Evaluator scores the team.
   * All 3 laptops watch the chain execution simultaneously!

---

## 🛠️ Part 3: Architecture & Reliability Highlights

* **Automatic Public URL Detection**: When hosted on Render, the backend and frontend automatically detect Render's public domain (`https://...`) instead of defaulting to internal container IPs (`10.x.x.x`).
* **Active WebSocket Heartbeat (Ping/Pong)**: Render's reverse proxy terminates idle WebSockets after 55 seconds. PromptRelay sends automated heartbeat pings every 20 seconds to keep connections permanently alive while players read dossiers.
* **Auto-Reconnection**: If a player's Wi-Fi blips or laptop sleeps briefly, the frontend automatically re-establishes the WebSocket connection within 2 seconds.
* **Unified Single Service**: Frontend static assets and backend REST/WebSocket APIs run on the same origin, avoiding CORS issues or multiple billable services.
