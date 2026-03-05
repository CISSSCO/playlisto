import httpx
import re
import asyncio
from fastapi import Request
from fastapi.responses import StreamingResponse, Response

CHUNK_SIZE = 1024 * 1024

# Reusable global HTTP client (important for performance)
client = httpx.AsyncClient(
    follow_redirects=True,
    timeout=None,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50
    ),
)


async def stream_file(file_id: str, filename: str, request: Request):
    base_url = "https://drive.google.com/uc"

    params = {
        "export": "download",
        "id": file_id,
    }

    headers = {}

    range_header = request.headers.get("range")

    if range_header:
        headers["Range"] = range_header

    response = await client.get(
        base_url,
        params=params,
        headers=headers,
    )

    # Handle Google Drive large file confirmation
    if "text/html" in response.headers.get("content-type", ""):
        match = re.search(r"confirm=([0-9A-Za-z_]+)", response.text)

        if match:
            confirm_token = match.group(1)
            params["confirm"] = confirm_token

            response = await client.get(
                base_url,
                params=params,
                headers=headers,
            )

    # Kodi probe support
    if request.method == "HEAD":
        head_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": response.headers.get(
                "content-type",
                "audio/flac"
            ),
        }

        if "content-length" in response.headers:
            head_headers["Content-Length"] = response.headers["content-length"]

        if "content-range" in response.headers:
            head_headers["Content-Range"] = response.headers["content-range"]

        return Response(
            status_code=response.status_code,
            headers=head_headers,
        )

    async def file_iterator():
        try:
            async for chunk in response.aiter_bytes(CHUNK_SIZE):
                yield chunk
        except asyncio.CancelledError:
            # Kodi often disconnects while probing
            return

    status_code = response.status_code

    if range_header and status_code == 200:
        status_code = 206

    stream_headers = {
        "Content-Type": response.headers.get(
            "content-type",
            "audio/flac"
        ),
        "Accept-Ranges": "bytes",
    }

    if "content-length" in response.headers:
        stream_headers["Content-Length"] = response.headers["content-length"]

    if "content-range" in response.headers:
        stream_headers["Content-Range"] = response.headers["content-range"]

    return StreamingResponse(
        file_iterator(),
        status_code=status_code,
        headers=stream_headers,
    )
