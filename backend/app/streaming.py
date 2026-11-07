import asyncio
import re
from pathlib import Path
import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse, Response

CHUNK_SIZE = 512 * 1024  # 512KB chunks for fast responsiveness

client = httpx.AsyncClient(
    follow_redirects=True,
    timeout=httpx.Timeout(connect=15.0, read=None, write=30.0, pool=None),
    limits=httpx.Limits(
        max_keepalive_connections=30,
        max_connections=100,
    ),
)

MIME_TYPES = {
    ".flac": "audio/flac",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".ogg": "audio/ogg",
    ".opus": "audio/opus",
    ".aac": "audio/aac",
}


def guess_content_type(filename: str, upstream_content_type: str = "") -> str:
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in MIME_TYPES:
            return MIME_TYPES[ext]
    if upstream_content_type and "text" not in upstream_content_type:
        return upstream_content_type
    return "audio/flac"


async def open_drive_stream(file_id: str, headers: dict) -> httpx.Response:
    base_url = "https://drive.google.com/uc"
    params = {"export": "download", "id": file_id}

    req = client.build_request("GET", base_url, params=params, headers=headers)
    resp = await client.send(req, stream=True)

    # Check for Google Drive virus scan warning / confirm screen on large files
    content_type = resp.headers.get("content-type", "").lower()
    if "text/html" in content_type:
        body = await resp.aread()
        await resp.aclose()
        text = body.decode("utf-8", errors="ignore")

        confirm_token = None
        match = re.search(r"confirm=([0-9A-Za-z_-]+)", text)
        if match:
            confirm_token = match.group(1)
        else:
            match_input = re.search(r'name="confirm"\s+value="([^"]+)"', text)
            if match_input:
                confirm_token = match_input.group(1)

        if confirm_token:
            params["confirm"] = confirm_token
            req2 = client.build_request("GET", base_url, params=params, headers=headers)
            resp = await client.send(req2, stream=True)

    return resp


async def stream_file(file_id: str, filename: str, request: Request):
    headers = {}
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    # Fast HEAD request support for media players probing file info
    if request.method == "HEAD":
        resp = await open_drive_stream(file_id, headers)
        try:
            status = resp.status_code
            content_type = guess_content_type(filename, resp.headers.get("content-type", ""))
            resp_headers = {
                "Accept-Ranges": "bytes",
                "Content-Type": content_type,
            }
            if "content-length" in resp.headers:
                resp_headers["Content-Length"] = resp.headers["content-length"]
            if "content-range" in resp.headers:
                resp_headers["Content-Range"] = resp.headers["content-range"]
            return Response(status_code=status, headers=resp_headers)
        finally:
            await resp.aclose()

    resp = await open_drive_stream(file_id, headers)
    status_code = resp.status_code
    content_type = guess_content_type(filename, resp.headers.get("content-type", ""))

    resp_headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
    }
    if "content-length" in resp.headers:
        resp_headers["Content-Length"] = resp.headers["content-length"]
    if "content-range" in resp.headers:
        resp_headers["Content-Range"] = resp.headers["content-range"]

    async def body_stream():
        try:
            async for chunk in resp.aiter_bytes(CHUNK_SIZE):
                yield chunk
        except (asyncio.CancelledError, httpx.ReadError, httpx.RemoteProtocolError):
            pass
        finally:
            await resp.aclose()

    return StreamingResponse(
        body_stream(),
        status_code=status_code,
        headers=resp_headers,
    )
