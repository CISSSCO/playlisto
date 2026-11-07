from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx

from .drive import fetch_folder_files
from .streaming import stream_file
from .storage import (
    add_source,
    load_sources,
    activate_source,
    delete_source,
    add_provider,
    delete_provider,
    get_active_source,
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
    active_source = get_active_source()
    if not active_source:
        raise HTTPException(status_code=400, detail="No active source configured")

    try:
        files = await fetch_folder_files()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response else 502
        raise HTTPException(
            status_code=status,
            detail=f"Google Drive API error ({status}): {e.response.text if e.response else str(e)}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch files from source: {str(e)}")

    return {
        "name": active_source.get("name", "Active Source"),
        "files": [f.model_dump() if hasattr(f, "model_dump") else f.dict() for f in files],
    }


@app.api_route("/api/stream/{file_id}", methods=["GET", "HEAD"])
async def stream(file_id: str, request: Request, filename: str = "audio.flac"):
    try:
        return await stream_file(file_id, filename, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


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
        raise HTTPException(status_code=400, detail="Name, url, and provider_id are required")

    add_source(name, url, provider_id)
    return {"status": "created"}


@app.post("/api/sources/activate/{source_id}")
async def activate_source_endpoint(source_id: str):
    activate_source(source_id)
    return {"status": "activated"}


@app.delete("/api/sources/{source_id}")
async def remove_source_endpoint(source_id: str):
    delete_source(source_id)
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
        "type": provider["type"],
    }


@app.post("/api/providers/activate/{provider_id}")
async def activate_provider(provider_id: str):
    set_active_provider(provider_id)
    return {"status": "activated"}


@app.delete("/api/providers/{provider_id}")
async def remove_provider_endpoint(provider_id: str):
    delete_provider(provider_id)
    return {"status": "deleted"}


# =========================
# SERVE REACT BUILD
# =========================

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # Don't intercept API routes that might have 404ed
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")

    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        # Check if the requested file exists in dist (e.g. bg4.svg, favicon.ico)
        requested_file = FRONTEND_DIST / full_path
        if full_path and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(index_file)
    return {"status": "ok", "message": "Playlisto API is running. Build frontend with 'npm run build' to serve UI."}
