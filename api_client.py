"""Small REST client with timeout and conservative retry handling."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests


class APIClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int,
        max_retries: int,
        logger: logging.Logger,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.logger = logger
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self.timeout_seconds,
                )

                # Retry only temporary server errors and rate limiting.
                if response.status_code == 429 or response.status_code >= 500:
                    raise requests.HTTPError(
                        f"Temporary API response: {response.status_code} {response.text}",
                        response=response,
                    )

                response.raise_for_status()
                payload = response.json()

                # KIS often returns HTTP 200 even when rt_cd signals a business error.
                if "rt_cd" in payload and str(payload["rt_cd"]) != "0":
                    raise RuntimeError(
                        f"KIS API error: msg_cd={payload.get('msg_cd')}, "
                        f"msg1={payload.get('msg1')}"
                    )

                return payload

            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as error:
                last_error = error
                self.logger.warning(
                    "API request failed: method=%s path=%s attempt=%s/%s error=%s",
                    method,
                    path,
                    attempt + 1,
                    self.max_retries + 1,
                    error,
                )
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)

            except ValueError as error:
                raise RuntimeError(f"API returned invalid JSON for {path}") from error

        raise RuntimeError(f"API request failed after retries: {path}") from last_error
