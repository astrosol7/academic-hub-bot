from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from academic_hub.clients.telegram.app import build_dispatcher, configure_bot
from academic_hub.config import load_config
from academic_hub.infrastructure.repository import FilesystemContentRepository


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_repository() -> FilesystemContentRepository:
    config = load_config(require_token=False)
    repository = FilesystemContentRepository(
        manifests_root=config.manifests_root,
        resources_root=config.resources_root,
        institution_slug=config.institution_slug,
    )
    for issue in repository.validation_report.warnings:
        logging.getLogger(__name__).warning("event=validation_warning code=%s message=%s", issue.code, issue.message)
    errors = repository.validation_report.errors
    if errors:
        joined = "; ".join(f"{issue.code}: {issue.message}" for issue in errors)
        raise RuntimeError(f"Validation failed: {joined}")
    return repository


async def main() -> None:
    config = load_config(require_token=True)
    configure_logging(config.log_level)

    repository = build_repository()
    bot = Bot(token=config.token)
    dispatcher = build_dispatcher(bot, repository)

    await configure_bot(bot)
    logging.getLogger(__name__).info(
        "event=bot_start institution=%s resources_root=%s",
        config.institution_slug,
        config.resources_root,
    )
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def run() -> None:
    asyncio.run(main())
