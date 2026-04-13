import asyncio
import logging
from time import monotonic

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey

from academic_hub.clients.telegram.managers.tasks import task_registry
from academic_hub.clients.telegram.middlewares.concurrency import concurrency_guard
from academic_hub.utils.logging import LogCategory, log_event


log = logging.getLogger(__name__)


class MemorySweeper:
    def __init__(self, dispatcher: Dispatcher, bot: Bot, ttl_minutes: float = 30.0, sweep_interval_minutes: float = 10.0) -> None:
        self.dispatcher = dispatcher
        self.bot = bot
        self.ttl_seconds = ttl_minutes * 60
        self.sweep_interval = sweep_interval_minutes * 60
        self._task: asyncio.Task | None = None
        self._stopping = False

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stopping = False
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopping = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        while not self._stopping:
            await asyncio.sleep(self.sweep_interval)
            if self._stopping:
                break
            try:
                await self._sweep()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.exception(f"Sweeper encountered an error: {exc}")

    async def _sweep(self) -> None:
        now = monotonic()
        stale_users: list[int] = []
        
        # 1. Identify stale users
        for user_id, last_active in concurrency_guard._last_active_at.items():
            if (now - last_active) > self.ttl_seconds:
                stale_users.append(user_id)

        for user_id in stale_users:
            try:
                # 2. Cancel and Await Graceful Shutdown of Active Tasks
                running_tasks = list(task_registry._tasks.get(user_id, {}).values())
                if running_tasks:
                    log_event(
                        log, logging.DEBUG, LogCategory.SYSTEM_TASK_KILLED,
                        "Sweeper terminating active tasks for stale user.",
                        user_id=user_id, action="SWEEPER_TASK_KILL"
                    )
                    for t in running_tasks:
                        if not t.done():
                            t.cancel()
                    # Await graceful death
                    await asyncio.gather(*running_tasks, return_exceptions=True)
                
                # Cleanup registry
                task_registry._tasks.pop(user_id, None)

                # 3. Clear FSM State
                key = StorageKey(bot_id=self.bot.id, chat_id=user_id, user_id=user_id)
                await self.dispatcher.storage.set_data(key, {})
                await self.dispatcher.storage.set_state(key, None)

                # 4. Remove Locks and Intent Data
                concurrency_guard._user_locks.pop(user_id, None)
                concurrency_guard._latest_intent_low.pop(user_id, None)
                concurrency_guard._last_active_at.pop(user_id, None)

                log_event(
                    log, logging.INFO, LogCategory.SYSTEM_TASK_KILLED,
                    "Memory sweeper successfully evicted stale user session.",
                    user_id=user_id, action="TTL_EVICTION", reason="Inactive > TTL"
                )

            except Exception as exc:
                log.error(f"Error sweeping user {user_id}: {exc}")
