from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .drive import fetch_folder_files
from .streaming import stream_file
from .storage import load_data, save_data, load_config, save_config

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


# -----------------------------
# API KEY MANAGEMENT
# -----------------------------

@app.post("/set-api-key")
async def set_api_key(payload: dict):
    api_key = payload.get("api_key")

    if not api_key:
        raise HTTPException(status_code=400, detail="API key required")

    save_config({"google_api_key": api_key})
    return {"status": "saved"}


@app.get("/api-key-status")
async def api_key_status():
    config = load_config()
    return {"configured": bool(config.get("google_api_key"))}


# -----------------------------
# MAIN PAGE
# -----------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = load_data()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
        },
    )


# -----------------------------
# LOAD FOLDER (Encrypted Storage)
# -----------------------------

@app.post("/load-folder")
async def load_folder(payload: dict):
    folder_url = payload.get("url")

    if not folder_url:
        raise HTTPException(status_code=400, detail="Folder URL required")

    files = await fetch_folder_files(folder_url)

    data = load_data()

    folder_entry = {
        # IMPORTANT:
        # We still store URL internally (encrypted by storage layer)
        # but we do NOT rely on returning it to frontend.
        "url": folder_url,
        "name": folder_url.split("/")[-1],
        "files": [f.dict() for f in files],
    }

    data["last_folder"] = folder_url

    existing = [f for f in data["folders"] if f["url"] == folder_url]
    if not existing:
        data["folders"].append(folder_entry)

    save_data(data)

    # DO NOT return full data structure.
    # Only return what's needed for frontend.
    return {
        "name": folder_entry["name"],
        "files": folder_entry["files"],
    }


# -----------------------------
# STREAMING (UNCHANGED)
# -----------------------------

@app.get("/stream/{file_id}")
async def stream(file_id: str, filename: str, request: Request):
    return await stream_file(file_id, filename, request)
