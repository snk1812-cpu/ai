"""Application configuration loaded from GitHub Codespaces environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class Config:
    # Mock trading only. This project intentionally has no live-trading URL.
    base_url: str = "https://openapivts.koreainvestment.com:29443"

    account_number: str = ""
    account_product_code: str = "01"
    app_key: str = ""
    app_secret: str = ""

    symbol: str = "005930"
    stock_name: str = "Samsung Electronics"

    # The professor's prompt contains both ±2,000 and ±1,000.
    # Functional requirement is used as the default. Change only these values if needed.
    buy_offset: int = 1_000
    sell_offset: int = 1_000
    order_quantity: int = 1

    trading_start: time = time(9, 10)
    trading_end: time = time(15, 30)

    # Conservative settings for the mock environment.
    polling_interval_seconds: int = 60
    order_cooldown_seconds: int = 300
    execution_check_delay_seconds: int = 5
    request_timeout_seconds: int = 10
    max_retries: int = 2

    token_cache_path: str = "token_cache.json"
    log_path: str = "logs/auto_trader.log"

    # KIS mock transaction IDs. Kept together so they are easy to edit if KIS changes them.
    tr_id_current_price: str = "FHKST01010100"
    tr_id_balance: str = "VTTC8434R"
    tr_id_buy: str = "VTTC0802U"
    tr_id_sell: str = "VTTC0801U"

    @classmethod
    def from_environment(cls) -> "Config":
        account_raw = os.getenv("GH_ACCOUNT", "").strip()
        app_key = os.getenv("GH_APPKEY", "").strip()
        app_secret = os.getenv("GH_APPSECRET", "").strip()

        missing = [
            name
            for name, value in {
                "GH_ACCOUNT": account_raw,
                "GH_APPKEY": app_key,
                "GH_APPSECRET": app_secret,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        account_number, product_code = _parse_account(account_raw)

        return cls(
            account_number=account_number,
            account_product_code=product_code,
            app_key=app_key,
            app_secret=app_secret,
        )


def _parse_account(value: str) -> tuple[str, str]:
    """Accept `12345678-01`, `1234567801`, or only the first eight digits."""
    cleaned = value.replace("-", "").replace(" ", "")

    if not cleaned.isdigit():
        raise ValueError("GH_ACCOUNT must contain only account digits and an optional hyphen.")

    if len(cleaned) == 8:
        return cleaned, "01"

    if len(cleaned) == 10:
        return cleaned[:8], cleaned[8:]

    raise ValueError(
        "GH_ACCOUNT must be 8 digits, 10 digits, or formatted like 12345678-01."
    )
