from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.bot.delivery import DeliveryCoordinator
from src.bot.handlers import register_handlers
from src.bot.renderer import TelegramRenderer
from src.bot.middlewares.concurrency import ConcurrencyGuardMiddleware
from src.bot.managers.sweeper import MemorySweeper
from src.core.config import load_config
from src.core.services import DeliveryService, NavigationService, SearchService
from src.core.repository import PostgresContentRepository


log = logging.getLogger(__name__)


def build_dispatcher(bot: Bot, repository: PostgresContentRepository) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    # Register core execution safety lock 
    dispatcher.update.middleware(ConcurrencyGuardMiddleware())
    
    config = load_config(require_token=False)
    renderer = TelegramRenderer(bot, voyager_url=config.voyager_url)
    navigation = NavigationService(repository)
    delivery = DeliveryService(repository)
    search = SearchService(repository)
    coordinator = DeliveryCoordinator()
    register_handlers(dispatcher, repository, navigation, delivery, search, renderer, coordinator)
    return dispatcher


async def configure_bot(bot: Bot, dispatcher: Dispatcher) -> MemorySweeper:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="menu", description="Main menu"),
            BotCommand(command="help", description="Help"),
            BotCommand(command="ask", description="Ask a question"),
            BotCommand(command="top", description="Top questions"),
            BotCommand(command="my", description="My questions"),
            BotCommand(command="stop", description="Sign out"),
        ]
    )
    
    sweeper = MemorySweeper(dispatcher, bot, ttl_minutes=30.0, sweep_interval_minutes=10.0)
    
    log.info("event=bot_configured")
    return sweeper
