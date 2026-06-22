"""Account balance and Samsung Electronics holding lookup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api_client import APIClient
from config import Config


@dataclass(frozen=True)
class AccountSnapshot:
    samsung_quantity: int
    available_cash: int
    raw_holdings: list[dict[str, Any]]


def get_account_snapshot(
    client: APIClient,
    config: Config,
    access_token: str,
) -> AccountSnapshot:
    payload = client.request(
        "GET",
        "/uapi/domestic-stock/v1/trading/inquire-balance",
        headers=_headers(config, access_token, config.tr_id_balance),
        params={
            "CANO": config.account_number,
            "ACNT_PRDT_CD": config.account_product_code,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        },
    )

    holdings = payload.get("output1") or []
    summary = payload.get("output2") or []

    samsung_quantity = 0
    for item in holdings:
        if str(item.get("pdno", "")) == config.symbol:
            samsung_quantity = _to_int(
                item.get("hldg_qty", item.get("hold_qty", "0"))
            )
            break

    available_cash = 0
    if summary:
        first = summary[0]
        # KIS response fields can differ by API revision/account.
        # Keep the alternatives isolated here for easy adjustment.
        for field in ("dnca_tot_amt", "prvs_rcdl_excc_amt", "nxdy_excc_amt"):
            if first.get(field) not in (None, ""):
                available_cash = _to_int(first[field])
                break

    return AccountSnapshot(
        samsung_quantity=samsung_quantity,
        available_cash=available_cash,
        raw_holdings=holdings,
    )


def _to_int(value: Any) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def _headers(config: Config, access_token: str, tr_id: str) -> dict[str, str]:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {access_token}",
        "appkey": config.app_key,
        "appsecret": config.app_secret,
        "tr_id": tr_id,
        "custtype": "P",
    }
