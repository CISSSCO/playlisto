from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .drive import fetch_folder_files
from .streaming import stream_file
from .storage import (
    load_data,
    save_data,
    add_source,
    load_sources,
    activate_source,
    add_provider,
    get_providers_metadata,
    set_active_provider,
)

app = FastAPI(title="Playlisto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# LOAD PLAYLIST
# =========================

@app.post("/api/load-folder")
async def load_folder():
    files = await fetch_folder_files()

    data = load_data()

    folder_entry = {
        "name": "Active Source",
        "files": [f.dict() for f in files],
    }

    data["last_folder"] = "active_source"
    data["folders"] = [folder_entry]

    save_data(data)

    return {
        "name": folder_entry["name"],
        "files": folder_entry["files"],
    }

@app.get("/api/stream/{file_id}")
async def stream(file_id: str, filename: str, request: Request):
    return await stream_file(file_id, filename, request)

# =========================
# SOURCES
# =========================

@app.get("/api/sources")
async def list_sources():
    return load_sources()

@app.post("/api/sources")
async def create_source(payload: dict):
    name = payload.get("name")
    url = payload.get("url")
    provider_id = payload.get("provider_id")

    if not name or not url or not provider_id:
        raise HTTPException(status_code=400, detail="Invalid input")

    add_source(name, url, provider_id)
    return {"status": "created"}

@app.post("/api/sources/activate/{source_id}")
async def activate_source_endpoint(source_id: str):
    activate_source(source_id)
    return {"status": "activated"}

@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: str):
    from .storage import load_sources, save_sources

    data = load_sources()
    data["sources"] = [s for s in data["sources"] if s["id"] != source_id]

    if data.get("active_source_id") == source_id:
        data["active_source_id"] = None

    save_sources(data)
    return {"status": "deleted"}

# =========================
# PROVIDERS
# =========================

@app.get("/api/providers")
async def list_providers():
    return get_providers_metadata()

@app.post("/api/providers")
async def create_provider(payload: dict):
    name = payload.get("name")
    api_key = payload.get("api_key")

    if not name or not api_key:
        raise HTTPException(status_code=400, detail="Name and API key required")

    provider = add_provider(name, api_key)

    return {
        "id": provider["id"],
        "name": provider["name"],
        "type": provider["type"]
    }

@app.post("/api/providers/activate/{provider_id}")
async def activate_provider(provider_id: str):
    set_active_provider(provider_id)
    return {"status": "activated"}

# =========================
# SERVE REACT BUILD
# =========================

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built. Run npm run build."}
