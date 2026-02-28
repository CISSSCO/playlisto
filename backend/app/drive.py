import re
import httpx
from .models import DriveFile
from .storage import load_config

AUDIO_EXTENSIONS = (".mp3", ".flac", ".wav", ".m4a", ".ogg")



def extract_folder_id(url: str) -> str:
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError("Invalid Google Drive folder URL")
    return match.group(1)


async def fetch_folder_files(folder_url: str):
    config = load_config()
    api_key = config.get("google_api_key")

    if not api_key:
        raise ValueError("Google API key not configured")

    folder_id = extract_folder_id(folder_url)

    query = f"'{folder_id}' in parents and trashed=false"

    url = "https://www.googleapis.com/drive/v3/files"

    params = {
        "q": query,
        "key": api_key,
        "fields": "files(id,name,mimeType)",
        "pageSize": 1000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

    data = response.json()

    files = []
    for item in data.get("files", []):
        name = item["name"]
        if name.lower().endswith(AUDIO_EXTENSIONS):
            files.append(
                DriveFile(
                    id=item["id"],
                    name=name
                )
            )

    return files
