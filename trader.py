"""Trading-window control and low-frequency polling strategy."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from account import AccountSnapshot, get_account_snapshot
from api_client import APIClient
from config import Config
from market_data import get_current_price
from orders import submit_limit_order


class SamsungAutoTrader:
    def __init__(
        self,
        config: Config,
        client: APIClient,
        access_token: str,
        logger: logging.Logger,
    ) -> None:
        self.config = config
        self.client = client
        self.access_token = access_token
        self.logger = logger
        self.next_order_time: datetime | None = None

    def run(self) -> None:
        self.logger.info(
            "Program started in MOCK mode. Symbol=%s, trading window=%s-%s",
            self.config.symbol,
            self.config.trading_start.strftime("%H:%M"),
            self.config.trading_end.strftime("%H:%M"),
        )

        while True:
            now = datetime.now()

            if now.time() >= self.config.trading_end:
                self.logger.info("Trading window ended. Program will stop.")
                return

            if now.time() < self.config.trading_start:
                sleep_seconds = min(
                    self.config.polling_interval_seconds,
                    max(
                        1,
                        int(
                            (
                                datetime.combine(now.date(), self.config.trading_start)
                                - now
                            ).total_seconds()
                        ),
                    ),
                )
                self.logger.info(
                    "Outside trading window. Waiting %s seconds.", sleep_seconds
                )
                time.sleep(sleep_seconds)
                continue

            if self.next_order_time and now < self.next_order_time:
                wait = min(
                    self.config.polling_interval_seconds,
                    max(1, int((self.next_order_time - now).total_seconds())),
                )
                time.sleep(wait)
                continue

            self.logger.info("Trading cycle started.")
            try:
                self._run_cycle()
            except Exception:
                self.logger.exception("Trading cycle failed.")

            self.next_order_time = datetime.now() + timedelta(
                seconds=self.config.order_cooldown_seconds
            )
            self.logger.info(
                "Next order cycle will not start before %s.",
                self.next_order_time.strftime("%H:%M:%S"),
            )
            time.sleep(self.config.polling_interval_seconds)

    def _run_cycle(self) -> None:
        # One price call and one pre-order balance call per cycle.
        current_price = get_current_price(
            self.client, self.config, self.access_token
        )
        self.logger.info("Current price: %s KRW", current_price)

        before = get_account_snapshot(
            self.client, self.config, self.access_token
        )
        self._log_snapshot("Holdings before order", before)

        buy_price = max(1, current_price - self.config.buy_offset)
        sell_price = current_price + self.config.sell_offset

        self.logger.info(
            "Buy order request: symbol=%s price=%s quantity=%s",
            self.config.symbol,
            buy_price,
            self.config.order_quantity,
        )
        buy_result = submit_limit_order(
            self.client,
            self.config,
            self.access_token,
            side="BUY",
            price=buy_price,
            quantity=self.config.order_quantity,
        )
        self.logger.info(
            "Buy order response: accepted=%s order_number=%s message=%s",
            buy_result.accepted,
            buy_result.order_number,
            buy_result.message,
        )

        # Only one verification call after the buy order.
        time.sleep(self.config.execution_check_delay_seconds)
        after_buy = get_account_snapshot(
            self.client, self.config, self.access_token
        )
        self._log_snapshot("Holdings after buy order", after_buy)
        self.logger.info(
            "Buy execution seems to have occurred: %s",
            after_buy.samsung_quantity > before.samsung_quantity,
        )

        # A cash-account sell requires actual holdings; do not assume short selling.
        if after_buy.samsung_quantity <= 0:
            self.logger.info(
                "Sell order skipped because the account has no Samsung Electronics holdings."
            )
            return

        sell_quantity = min(
            self.config.order_quantity,
            after_buy.samsung_quantity,
        )
        self.logger.info(
            "Sell order request: symbol=%s price=%s quantity=%s",
            self.config.symbol,
            sell_price,
            sell_quantity,
        )
        sell_result = submit_limit_order(
            self.client,
            self.config,
            self.access_token,
            side="SELL",
            price=sell_price,
            quantity=sell_quantity,
        )
        self.logger.info(
            "Sell order response: accepted=%s order_number=%s message=%s",
            sell_result.accepted,
            sell_result.order_number,
            sell_result.message,
        )

        # Only one verification call after the sell order.
        time.sleep(self.config.execution_check_delay_seconds)
        after_sell = get_account_snapshot(
            self.client, self.config, self.access_token
        )
        self._log_snapshot("Holdings after sell order", after_sell)
        self.logger.info(
            "Sell execution seems to have occurred: %s",
            after_sell.samsung_quantity < after_buy.samsung_quantity,
        )

    def _log_snapshot(self, label: str, snapshot: AccountSnapshot) -> None:
        self.logger.info(
            "%s: samsung_quantity=%s available_cash=%s",
            label,
            snapshot.samsung_quantity,
            snapshot.available_cash,
        )
