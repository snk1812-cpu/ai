"""Program entry point."""

from __future__ import annotations

from api_client import APIClient
from auth import TokenManager
from config import Config
from logger import build_logger
from trader import SamsungAutoTrader


def main() -> None:
    config = Config.from_environment()
    logger = build_logger(config.log_path)

    client = APIClient(
        base_url=config.base_url,
        timeout_seconds=config.request_timeout_seconds,
        max_retries=config.max_retries,
        logger=logger,
    )

    token_manager = TokenManager(config, client, logger)
    access_token = token_manager.get_token()

    trader = SamsungAutoTrader(
        config=config,
        client=client,
        access_token=access_token,
        logger=logger,
    )
    trader.run()


if __name__ == "__main__":
    main()
