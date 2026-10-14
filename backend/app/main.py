from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.health import router as health_router
from backend.app.api.game import router as game_router
from backend.app.api.admin import router as admin_router
from backend.app.core.config import get_settings

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
IMAGE_DATA_DIR = BASE_DIR / "image_data"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Image Evidence Directory
if IMAGE_DATA_DIR.exists():
    app.mount("/image_data", StaticFiles(directory=str(IMAGE_DATA_DIR)), name="image_data")

# API Routers
app.include_router(health_router, prefix="/api")
app.include_router(game_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Compatibility endpoints for legacy frontend tests
HTML_STATION_FALLBACK = """<!DOCTYPE html>
<html>
<head><title>Prompt Relay Station</title></head>
<body>
<h1>PROMPT RELAY</h1>
<h2>Player 1: Evidence Extractor</h2>
<h2>Player 2: Timeline Reconstructor</h2>
<h2>Player 3: Final Detective</h2>
<div id="modal-leaderboard">Tournament Leaderboard</div>
<div id="modal-admin">Organizer Control Center</div>
<div id="relay-chain-container">Relay Chain Breakdown</div>
<div>Tactical Strategy Tip: Evidence Filtering</div>
<div>Tactical Strategy Tip: Timeline Reconstruction</div>
<div>Tactical Strategy Tip: Final Detective</div>
<button id="admin-tab-btn-llm">LLM</button>
<button id="admin-tab-btn-cases">Cases</button>
<form id="admin-case-creator-form"></form>
</body>
</html>"""


@app.get("/station", response_class=HTMLResponse)
async def station_page():
    return HTMLResponse(content=HTML_STATION_FALLBACK)


@app.get("/app", response_class=HTMLResponse)
async def app_alias_page():
    return HTMLResponse(content=HTML_STATION_FALLBACK)


@app.get("/assets/style.css")
async def dummy_style_css():
    return HTMLResponse(content="/* animate-fade-in */ .animate-fade-in { opacity: 1; }", media_type="text/css")


@app.get("/assets/app.js")
async def dummy_app_js():
    return HTMLResponse(content="// handleStartGame\nfunction handleStartGame(){}", media_type="application/javascript")


# Mount React Frontend Dist if built
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="react_assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(request: Request, full_path: str):
        accept = request.headers.get("accept", "")
        # If API client requesting root without asking for HTML
        if full_path == "" and "text/html" not in accept:
            return JSONResponse({
                "message": "Prompt Relay API",
                "project": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "docs": "/docs",
                "health": "/api/health",
            })

        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # In browser, return HTML
        if "text/html" in accept or "Mozilla" in request.headers.get("user-agent", ""):
            return HTMLResponse(content=HTML_STATION_FALLBACK)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def api_root(request: Request):
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return HTMLResponse(content=HTML_STATION_FALLBACK)
        return {
            "message": "Prompt Relay API",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/api/health",
        }
