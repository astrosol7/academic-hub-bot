import asyncio
import logging

log = logging.getLogger(__name__)

class AsyncTaskRegistry:
    def __init__(self) -> None:
        # Dict[user_id, Dict[task_type, asyncio.Task]]
        self._tasks: dict[int, dict[str, asyncio.Task]] = {}

    def register(self, user_id: int, task_type: str, task: asyncio.Task) -> None:
        if user_id not in self._tasks:
            self._tasks[user_id] = {}
            
        # Cancel exact task type if it exists to prevent collision
        existing = self._tasks[user_id].get(task_type)
        if existing and not existing.done():
            log.debug(f"Cancelling existing task '{task_type}' for user {user_id}")
            existing.cancel()
            
        self._tasks[user_id][task_type] = task
        # Add cleanup callback
        task.add_done_callback(lambda t: self._cleanup(user_id, task_type, t))

    def _cleanup(self, user_id: int, task_type: str, task: asyncio.Task) -> None:
        user_tasks = self._tasks.get(user_id)
        if user_tasks and user_tasks.get(task_type) is task:
            del user_tasks[task_type]

    def cancel(self, user_id: int, task_type: str | None = None) -> None:
        """Cancel a specific task type for a user, or all tasks if task_type is None."""
        user_tasks = self._tasks.get(user_id)
        if not user_tasks:
            return
            
        if task_type:
            task = user_tasks.get(task_type)
            if task and not task.done():
                log.debug(f"Cancelling '{task_type}' task for user {user_id}")
                task.cancel()
        else:
            for t_type, task in list(user_tasks.items()):
                if not task.done():
                    log.debug(f"Cancelling '{t_type}' task for user {user_id}")
                    task.cancel()

task_registry = AsyncTaskRegistry()
