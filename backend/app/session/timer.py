import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class QuestionTimer:
    def __init__(self, duration_sec: float = 12.0, on_timeout: Callable[[], Awaitable] | None = None):
        self.duration = duration_sec
        self.on_timeout = on_timeout
        self._task: asyncio.Task | None = None
        self.remaining = 0.0

    async def start(self):
        self.cancel()
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        self.remaining = self.duration
        while self.remaining > 0:
            await asyncio.sleep(1.0)
            self.remaining -= 1.0
        if self.on_timeout:
            await self.on_timeout()

    def cancel(self):
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    @property
    def is_active(self) -> bool:
        return self._task is not None and not self._task.done()
