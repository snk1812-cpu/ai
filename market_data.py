"""Domestic-stock market-data functions."""

from __future__ import annotations

from api_client import APIClient
from config import Config


def get_current_price(
    client: APIClient,
    config: Config,
    access_token: str,
) -> int:
    payload = client.request(
        "GET",
        "/uapi/domestic-stock/v1/quotations/inquire-price",
        headers=_headers(config, access_token, config.tr_id_current_price),
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": config.symbol,
        },
    )

    output = payload.get("output", {})
    price_text = output.get("stck_prpr")
    if price_text is None:
        raise RuntimeError("Current-price response did not contain output.stck_prpr.")

    return int(price_text)


def _headers(config: Config, access_token: str, tr_id: str) -> dict[str, str]:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {access_token}",
        "appkey": config.app_key,
        "appsecret": config.app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }
