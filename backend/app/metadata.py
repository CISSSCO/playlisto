import io
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import httpx
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

from .streaming import client

# Cache for metadata and artwork by file_id
_metadata_cache: Dict[str, Dict[str, Any]] = {}
_artwork_cache: Dict[str, Optional[Tuple[bytes, str]]] = {}


def parse_filename_tags(filename: str) -> Dict[str, str]:
    """Parse artist and title from standard filename patterns like 'Artist - Title.mp3'."""
    stem = Path(filename).stem
    # Remove leading track numbers like '01. ' or '01 - ' or '1- '
    cleaned = re.sub(r"^\d+[\s\.\-_]+", "", stem).strip()

    if " - " in cleaned:
        parts = cleaned.split(" - ", 1)
        return {
            "artist": parts[0].strip(),
            "title": parts[1].strip(),
        }

    return {
        "artist": "",
        "title": cleaned,
    }


async def fetch_file_header(file_id: str, bytes_to_fetch: int = 512 * 1024) -> bytes:
    """Fetch the initial chunk of an audio file using HTTP Range."""
    base_url = "https://drive.google.com/uc"
    params = {"export": "download", "id": file_id}
    headers = {"Range": f"bytes=0-{bytes_to_fetch - 1}"}

    try:
        resp = await client.get(base_url, params=params, headers=headers)
        if resp.status_code in (200, 206):
            return resp.content
    except Exception:
        pass
    return b""


def extract_tags_and_art_from_bytes(data: bytes, filename: str) -> Tuple[Dict[str, str], Optional[Tuple[bytes, str]]]:
    """Attempt to parse ID3, FLAC, MP4 or Ogg tags and embedded artwork."""
    tags = parse_filename_tags(filename)
    artwork: Optional[Tuple[bytes, str]] = None
    ext = Path(filename).suffix.lower()

    if not data:
        return tags, artwork

    # FLAC
    if ext == ".flac" or data.startswith(b"fLaC"):
        try:
            flac = FLAC(io.BytesIO(data))
            if flac.get("title"):
                tags["title"] = flac["title"][0]
            if flac.get("artist"):
                tags["artist"] = flac["artist"][0]
            if flac.get("album"):
                tags["album"] = flac["album"][0]
            if flac.pictures:
                pic = flac.pictures[0]
                artwork = (pic.data, pic.mime or "image/jpeg")
        except Exception:
            pass

    # MP3 (ID3)
    elif ext == ".mp3" or data.startswith(b"ID3"):
        try:
            id3 = ID3(io.BytesIO(data))
            if id3.get("TIT2"):
                tags["title"] = id3["TIT2"].text[0]
            if id3.get("TPE1"):
                tags["artist"] = id3["TPE1"].text[0]
            if id3.get("TALB"):
                tags["album"] = id3["TALB"].text[0]
            apic_frames = id3.getall("APIC")
            if apic_frames:
                pic = apic_frames[0]
                artwork = (pic.data, pic.mime or "image/jpeg")
        except Exception:
            pass

    # MP4 / M4A
    elif ext in (".m4a", ".mp4"):
        try:
            mp4 = MP4(io.BytesIO(data))
            if mp4.get("\xa9nam"):
                tags["title"] = mp4["\xa9nam"][0]
            if mp4.get("\xa9ART"):
                tags["artist"] = mp4["\xa9ART"][0]
            if mp4.get("\xa9alb"):
                tags["album"] = mp4["\xa9alb"][0]
            covr = mp4.get("covr")
            if covr and len(covr) > 0:
                artwork = (bytes(covr[0]), "image/jpeg")
        except Exception:
            pass

    # OGG
    elif ext in (".ogg", ".opus"):
        try:
            ogg = OggVorbis(io.BytesIO(data))
            if ogg.get("title"):
                tags["title"] = ogg["title"][0]
            if ogg.get("artist"):
                tags["artist"] = ogg["artist"][0]
            if ogg.get("album"):
                tags["album"] = ogg["album"][0]
        except Exception:
            pass

    return tags, artwork


async def get_or_extract_metadata(file_id: str, filename: str) -> Dict[str, Any]:
    if file_id in _metadata_cache:
        return _metadata_cache[file_id]

    data = await fetch_file_header(file_id)
    tags, artwork = extract_tags_and_art_from_bytes(data, filename)

    _metadata_cache[file_id] = tags
    _artwork_cache[file_id] = artwork
    return tags


async def get_artwork(file_id: str, filename: str = "") -> Optional[Tuple[bytes, str]]:
    if file_id in _artwork_cache:
        return _artwork_cache[file_id]

    data = await fetch_file_header(file_id)
    _, artwork = extract_tags_and_art_from_bytes(data, filename)
    _artwork_cache[file_id] = artwork
    return artwork
