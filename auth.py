"""Access-token creation and same-day token cache."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path

from api_client import APIClient
from config import Config


class TokenManager:
    def __init__(
        self,
        config: Config,
        client: APIClient,
        logger: logging.Logger,
    ) -> None:
        self.config = config
        self.client = client
        self.logger = logger

    def get_token(self) -> str:
        cached = self._read_cached_token()
        if cached:
            self.logger.info("Reusing cached access token for %s.", date.today())
            return cached

        self.logger.info("No valid same-day token found. Requesting a new token.")
        payload = self.client.request(
            "POST",
            "/oauth2/tokenP",
            json_body={
                "grant_type": "client_credentials",
                "appkey": self.config.app_key,
                "appsecret": self.config.app_secret,
            },
        )

        token = str(payload.get("access_token", ""))
        if not token:
            raise RuntimeError("Token response did not contain access_token.")

        self._write_cache(token)
        self.logger.info("New access token issued and cached.")
        return token

    def _read_cached_token(self) -> str | None:
        path = Path(self.config.token_cache_path)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.logger.warning("Token cache could not be read. A new token will be issued.")
            return None

        if data.get("date") != date.today().isoformat():
            return None

        token = data.get("access_token")
        return str(token) if token else None

    def _write_cache(self, token: str) -> None:
        path = Path(self.config.token_cache_path)
        data = {
            "date": date.today().isoformat(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "access_token": token,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
