"""Mock domestic-stock limit-order functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from api_client import APIClient
from config import Config


OrderSide = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class OrderResult:
    side: OrderSide
    accepted: bool
    order_number: str
    message: str
    raw: dict[str, Any]


def submit_limit_order(
    client: APIClient,
    config: Config,
    access_token: str,
    *,
    side: OrderSide,
    price: int,
    quantity: int,
) -> OrderResult:
    tr_id = config.tr_id_buy if side == "BUY" else config.tr_id_sell

    payload = client.request(
        "POST",
        "/uapi/domestic-stock/v1/trading/order-cash",
        headers=_headers(config, access_token, tr_id),
        json_body={
            "CANO": config.account_number,
            "ACNT_PRDT_CD": config.account_product_code,
            "PDNO": config.symbol,
            "ORD_DVSN": "00",  # 00: limit order
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price),
        },
    )

    output = payload.get("output") or {}
    order_number = str(output.get("ODNO", output.get("odno", "")))
    message = str(payload.get("msg1", ""))

    return OrderResult(
        side=side,
        accepted=str(payload.get("rt_cd", "0")) == "0",
        order_number=order_number,
        message=message,
        raw=payload,
    )


def _headers(config: Config, access_token: str, tr_id: str) -> dict[str, str]:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {access_token}",
        "appkey": config.app_key,
        "appsecret": config.app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }
