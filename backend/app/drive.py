import re
import httpx
from .models import DriveFile
from .storage import get_active_source, get_active_provider

AUDIO_EXTENSIONS = (".mp3", ".flac", ".wav", ".m4a", ".ogg")


def extract_folder_id(url: str) -> str:
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError("Invalid Google Drive folder URL")
    return match.group(1)


async def fetch_folder_recursive(client, folder_id, api_key):
    query = f"'{folder_id}' in parents and trashed=false"

    params = {
        "q": query,
        "key": api_key,
        "fields": "files(id,name,mimeType)",
        "pageSize": 1000,
    }

    response = await client.get(
        "https://www.googleapis.com/drive/v3/files",
        params=params
    )

    response.raise_for_status()
    data = response.json()

    files = []

    for item in data.get("files", []):
        if item["mimeType"] == "application/vnd.google-apps.folder":
            sub = await fetch_folder_recursive(client, item["id"], api_key)
            files.extend(sub)

        elif item["name"].lower().endswith(AUDIO_EXTENSIONS):
            files.append(
                DriveFile(
                    id=item["id"],
                    name=item["name"]
                )
            )

    return files


async def fetch_folder_files():
    active_source = get_active_source()
    if not active_source:
        raise ValueError("No active source configured")

    provider = get_active_provider()
    if not provider:
        raise ValueError("No active provider configured")

    api_key = provider.get("api_key")
    if not api_key:
        raise ValueError("Active provider has no API key")

    folder_url = active_source.get("url")
    if not folder_url:
        raise ValueError("Active source URL missing")

    folder_id = extract_folder_id(folder_url)

    async with httpx.AsyncClient(timeout=60) as client:
        files = await fetch_folder_recursive(client, folder_id, api_key)

    return files
