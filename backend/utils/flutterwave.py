"""Flutterwave V4 API Client with OAuth2 Token Management"""
import os
import time
import logging
import httpx

logger = logging.getLogger(__name__)

FLW_CLIENT_ID = os.environ.get("FLW_CLIENT_ID", "")
FLW_CLIENT_SECRET = os.environ.get("FLW_CLIENT_SECRET", "")
FLW_ENV = os.environ.get("FLW_ENV", "sandbox")

if FLW_ENV == "production":
    FLW_BASE_URL = "https://f4bexperience.flutterwave.com"
else:
    FLW_BASE_URL = "https://developersandbox-api.flutterwave.com"

FLW_TOKEN_URL = "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token"


class FlutterwaveTokenManager:
    def __init__(self):
        self._token = None
        self._expires_at = 0.0

    async def refresh_token(self):
        async with httpx.AsyncClient(timeout=15.0) as client:
            data = {
                "client_id": FLW_CLIENT_ID,
                "client_secret": FLW_CLIENT_SECRET,
                "grant_type": "client_credentials",
            }
            response = await client.post(
                FLW_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 401:
                logger.error("Flutterwave OAuth2 credentials rejected (401). Verify FLW_CLIENT_ID and FLW_CLIENT_SECRET.")
                raise Exception("Flutterwave authentication failed — invalid credentials")
            response.raise_for_status()
            payload = response.json()
            self._token = payload.get("access_token")
            expires_in = payload.get("expires_in", 600)
            self._expires_at = time.time() + (expires_in - 60)
            logger.info("Flutterwave token refreshed")

    async def get_token(self):
        if not self._token or time.time() >= self._expires_at:
            await self.refresh_token()
        return self._token


token_manager = FlutterwaveTokenManager()


async def flw_request(method: str, path: str, **kwargs) -> httpx.Response:
    """Make authenticated request to Flutterwave API."""
    token = await token_manager.get_token()
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    headers.setdefault("Content-Type", "application/json")
    async with httpx.AsyncClient(base_url=FLW_BASE_URL, timeout=30.0) as client:
        response = await client.request(method, path, headers=headers, **kwargs)
        return response


def is_flutterwave_configured():
    return bool(FLW_CLIENT_ID and FLW_CLIENT_SECRET)
