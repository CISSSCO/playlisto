import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

CHUNK_SIZE = 1024 * 1024


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

    async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:

        response = await client.get(
            base_url,
            params=params,
            headers=headers,
        )

        # Large file confirmation handling
        if "text/html" in response.headers.get("content-type", ""):
            import re
            match = re.search(r"confirm=([0-9A-Za-z_]+)", response.text)
            if match:
                confirm_token = match.group(1)
                params["confirm"] = confirm_token

                response = await client.get(
                    base_url,
                    params=params,
                    headers=headers,
                )

        async def file_iterator():
            async for chunk in response.aiter_bytes(CHUNK_SIZE):
                yield chunk

        # IMPORTANT FIX:
        status_code = response.status_code

        # If browser requested range but Google returned 200,
        # convert it to 206 manually
        if range_header and status_code == 200:
            status_code = 206

        return StreamingResponse(
            file_iterator(),
            status_code=status_code,
            headers={

                 "Content-Type": response.headers.get(
                     "content-type",
                     "audio/flac"
                 ),
                "Accept-Ranges": "bytes",
                "Content-Length": response.headers.get("content-length", ""),
                "Content-Range": response.headers.get("content-range", ""),
            },
        )
