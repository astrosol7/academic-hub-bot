from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from academic_hub.clients.telegram.app import build_dispatcher, configure_bot
from academic_hub.config import load_config
from academic_hub.infrastructure.repository_db import PostgresContentRepository
from academic_hub.utils.logging import LogCategory, log_event


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_repository() -> PostgresContentRepository:
    config = load_config(require_token=False)
    repository = PostgresContentRepository(
        manifests_root=config.manifests_root,
        resources_root=config.resources_root,
        institution_slug=config.institution_slug,
    )
    # The DB repository handles validation differently or assumes pre-validated sync.
    log_event(
        logging.getLogger(__name__),
        logging.INFO,
        LogCategory.SYSTEM_WARNING,
        "PostgreSQL Content Repository initialized successfully.",
        institution=config.institution_slug
    )
    return repository


async def main() -> None:
    config = load_config(require_token=True)
    configure_logging(config.log_level)

    repository = build_repository()
    bot = Bot(token=config.token)
    dispatcher = build_dispatcher(bot, repository)

    sweeper = await configure_bot(bot, dispatcher)
    log_event(
        logging.getLogger(__name__),
        logging.INFO,
        LogCategory.SCREEN,
        "Bot polling started.",
        institution=config.institution_slug,
        resources_root=str(config.resources_root),
    )
    
    sweeper.start()
    try:
        await dispatcher.start_polling(bot)
    finally:
        await sweeper.stop()
        await bot.session.close()


def run() -> None:
    asyncio.run(main())

if __name__ == "__main__":
    run()
