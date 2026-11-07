import re
import httpx
from .models import DriveFile
from .storage import get_active_source, get_active_provider, get_provider_by_id
from .metadata import parse_filename_tags

AUDIO_EXTENSIONS = (".mp3", ".flac", ".wav", ".m4a", ".ogg", ".opus", ".aac")


def extract_folder_id(url: str) -> str:
    cleaned = url.strip()
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", cleaned)
    if match:
        return match.group(1)

    match_id = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", cleaned)
    if match_id:
        return match_id.group(1)

    # Google Drive IDs are typically 25 to 60 alphanumeric/dash characters
    if re.fullmatch(r"[a-zA-Z0-9_-]{25,60}", cleaned):
        return cleaned

    raise ValueError("Invalid Google Drive folder URL or Folder ID format")


async def fetch_folder_recursive(client: httpx.AsyncClient, folder_id: str, api_key: str):
    files = []
    page_token = None

    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "key": api_key,
            "fields": "nextPageToken,files(id,name,mimeType)",
            "pageSize": 1000,
        }
        if page_token:
            params["pageToken"] = page_token

        response = await client.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("files", []):
            mime = item.get("mimeType", "")
            name = item.get("name", "")
            if mime == "application/vnd.google-apps.folder":
                sub = await fetch_folder_recursive(client, item["id"], api_key)
                files.extend(sub)
            elif name.lower().endswith(AUDIO_EXTENSIONS):
                tags = parse_filename_tags(name)
                files.append(
                    DriveFile(
                        id=item["id"],
                        name=name,
                        title=tags.get("title") or name,
                        artist=tags.get("artist") or "",
                    )
                )

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return files


async def fetch_folder_files():
    active_source = get_active_source()
    if not active_source:
        raise ValueError("No active source configured")

    provider_id = active_source.get("provider_id")
    provider = None
    if provider_id:
        provider = get_provider_by_id(provider_id)
    if not provider:
        provider = get_active_provider()
    if not provider:
        raise ValueError("No provider configured for the active source")

    api_key = provider.get("api_key")
    if not api_key:
        raise ValueError("Active provider has no API key configured")

    folder_url = active_source.get("url")
    if not folder_url:
        raise ValueError("Active source URL missing")

    folder_id = extract_folder_id(folder_url)

    async with httpx.AsyncClient(timeout=60) as client:
        files = await fetch_folder_recursive(client, folder_id, api_key)

    return files
