"""Flutterwave V3 API client (live keys)."""
import os
import httpx

FLW_SECRET_KEY = os.environ.get("FLW_SECRET_KEY", "")
FLW_BASE_URL = "https://api.flutterwave.com"


async def flw_request(method: str, path: str, json: dict = None, params: dict = None) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        return await client.request(method, f"{FLW_BASE_URL}{path}", json=json, params=params, headers=headers)


def is_flutterwave_configured() -> bool:
    return bool(FLW_SECRET_KEY)
