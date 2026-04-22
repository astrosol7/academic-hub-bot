from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from aiogram import Bot
from src.bot.app import build_dispatcher, configure_bot
from src.core.repository import PostgresContentRepository
from src.core.config import load_config

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("bot.main")

async def main():
    log.info("🚀 Initializing Station Orbit Bot...")
    
    # Load configuration
    try:
        config = load_config()
        if not config.bot.token:
            log.error("❌ TELEGRAM_BOT_TOKEN not found in environment.")
            return
    except Exception as e:
        log.error(f"❌ Configuration error: {e}")
        return

    # Initialize Repository
    repository = PostgresContentRepository()
    
    # Build Bot and Dispatcher
    bot = Bot(token=config.bot.token)
    dp = build_dispatcher(bot, repository)
    
    # Configure shared services (commands, etc.)
    await configure_bot(bot, dp)
    
    log.info("📡 Uplink established. Bot is now polling.")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        log.error(f"❌ Critical error in bot polling: {e}")
    finally:
        await bot.session.close()
        log.info("💤 Station Orbit Bot shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
