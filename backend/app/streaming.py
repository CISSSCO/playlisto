import httpx
import re
import asyncio
from fastapi import Request
from fastapi.responses import StreamingResponse, Response

CHUNK_SIZE = 1024 * 1024  # 1MB for faster startup

client = httpx.AsyncClient(
    follow_redirects=True,
    timeout=None,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
    ),
)

# cache for metadata
metadata_cache = {}

# cache for prefetched chunks
prefetch_cache = {}


async def fetch_metadata(file_id, params, headers):
    if file_id in metadata_cache:
        return metadata_cache[file_id]

    r = await client.get(
        "https://drive.google.com/uc",
        params=params,
        headers=headers,
    )

    metadata_cache[file_id] = r.headers
    return r.headers


async def prefetch_first_chunk(file_id):
    if file_id in prefetch_cache:
        return

    try:
        r = await client.get(
            "https://drive.google.com/uc",
            params={
                "export": "download",
                "id": file_id,
            },
            headers={
                "Range": f"bytes=0-{CHUNK_SIZE-1}"
            },
        )

        prefetch_cache[file_id] = r.content

    except Exception:
        pass


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

    # Kodi HEAD probe
    if request.method == "HEAD":

        meta = await fetch_metadata(file_id, params, headers)

        return Response(
            status_code=200,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Type": meta.get("content-type", "audio/flac"),
            },
        )

    meta = await fetch_metadata(file_id, params, headers)

    response_headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": meta.get("content-type", "audio/flac"),
    }

    if "content-range" in meta:
        response_headers["Content-Range"] = meta["content-range"]

    async def proxy_stream():

        try:

            # serve prefetched chunk if available
            if file_id in prefetch_cache:
                yield prefetch_cache.pop(file_id)

            async with client.stream(
                "GET",
                base_url,
                params=params,
                headers=headers,
            ) as response:

                # Google Drive confirm page handling
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

    # start background prefetch
    asyncio.create_task(prefetch_first_chunk(file_id))

    return StreamingResponse(
        proxy_stream(),
        status_code=206 if range_header else 200,
        headers=response_headers,
    )
