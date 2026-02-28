import httpx
import mimetypes
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse


def guess_mime_type(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


async def stream_file(file_id: str, filename: str, request: Request):
    drive_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    media_type = guess_mime_type(filename)

    headers = {}
    if "range" in request.headers:
        headers["Range"] = request.headers["range"]

    async def iterator():
        async with httpx.AsyncClient(
            timeout=None,
            follow_redirects=True
        ) as client:
            async with client.stream("GET", drive_url, headers=headers) as response:

                if response.status_code not in (200, 206):
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Drive download failed"
                    )

                async for chunk in response.aiter_bytes():
                    yield chunk

    # We must pre-fetch headers once to send proper metadata
    async with httpx.AsyncClient(
        timeout=None,
        follow_redirects=True
    ) as client:
        async with client.stream("GET", drive_url, headers=headers) as response:

            if response.status_code not in (200, 206):
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Drive download failed"
                )

            response_headers = {}
            for h in ["Content-Length", "Content-Range", "Accept-Ranges"]:
                if h in response.headers:
                    response_headers[h] = response.headers[h]

            return StreamingResponse(
                iterator(),
                status_code=response.status_code,
                headers=response_headers,
                media_type=media_type,
            )
