from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from academic_hub.clients.telegram.app import build_dispatcher, configure_bot
from academic_hub.config import load_config
from academic_hub.infrastructure.repository import FilesystemContentRepository
from academic_hub.utils.logging import LogCategory, log_event


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
        category = LogCategory.SYSTEM_ORPHAN if issue.code == "system_orphan_file" else LogCategory.SYSTEM_WARNING
        log_event(
            logging.getLogger(__name__),
            logging.WARNING,
            category,
            issue.message,
            code=issue.code,
            **issue.context,
        )
    errors = repository.validation_report.errors
    if errors:
        for issue in errors:
            log_event(
                logging.getLogger(__name__),
                logging.ERROR,
                LogCategory.VALIDATION_ERROR,
                issue.message,
                code=issue.code,
                **issue.context,
            )
        joined = "; ".join(f"{issue.code}: {issue.message}" for issue in errors)
        raise RuntimeError(f"Validation failed: {joined}")
    if repository.index_memory_mb > config.max_index_memory_mb:
        log_event(
            logging.getLogger(__name__),
            logging.WARNING,
            LogCategory.SYSTEM_WARNING,
            "In-memory index exceeded the configured warning threshold.",
            index_memory_mb=repository.index_memory_mb,
            threshold_mb=config.max_index_memory_mb,
        )
    else:
        log_event(
            logging.getLogger(__name__),
            logging.INFO,
            LogCategory.SYSTEM_WARNING,
            "In-memory index built successfully.",
            index_memory_mb=repository.index_memory_mb,
            threshold_mb=config.max_index_memory_mb,
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
