import httpx
import re
import asyncio
from fastapi import Request
from fastapi.responses import StreamingResponse, Response

CHUNK_SIZE = 4 * 1024 * 1024

client = httpx.AsyncClient(
    follow_redirects=True,
    timeout=None,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
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

    # HEAD request (Kodi probe)
    if request.method == "HEAD":

        r = await client.get(
            base_url,
            params=params,
            headers=headers,
        )

        return Response(
            status_code=r.status_code,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Type": r.headers.get("content-type", "audio/flac"),
                "Content-Length": r.headers.get("content-length", ""),
            },
        )

    async def proxy_stream():

        try:

            async with client.stream(
                "GET",
                base_url,
                params=params,
                headers=headers,
            ) as response:

                # Handle Google Drive large file confirmation
                if "text/html" in response.headers.get("content-type", ""):

                    body = await response.aread()
                    text = body.decode()

                    match = re.search(r"confirm=([0-9A-Za-z_]+)", text)

                    if match:

                        params["confirm"] = match.group(1)

                        async with client.stream(
                            "GET",
                            base_url,
                            params=params,
                            headers=headers,
                        ) as response2:

                            async for chunk in response2.aiter_bytes(CHUNK_SIZE):
                                yield chunk

                        return

                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    yield chunk

        except (asyncio.CancelledError, httpx.ReadError):
            return

    # get metadata once (fast)
    meta = await client.get(
        base_url,
        params=params,
        headers=headers,
    )

    response_headers = {
        "Accept-Ranges": meta.headers.get("accept-ranges", "bytes"),
        "Content-Type": meta.headers.get("content-type", "audio/flac"),
    }

    if "content-length" in meta.headers:
        response_headers["Content-Length"] = meta.headers["content-length"]

    if "content-range" in meta.headers:
        response_headers["Content-Range"] = meta.headers["content-range"]

    return StreamingResponse(
        proxy_stream(),
        status_code=meta.status_code,
        headers=response_headers,
    )
