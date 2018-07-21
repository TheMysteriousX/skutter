import asyncio
import psutil

from typing import Union


class Process(object):
    _delay = 0
    _process = ''

    def __init__(self,  process: str, delay: int=60) -> None:
        self._process = process
        self._delay = delay

    def get_pid(self) -> Union[None, int]:
        for p in psutil.process_iter():
            if p.name() == self._process:
                return p.pid

        return None

    def process_running(self) -> bool:
        return True if self.get_pid() else False

    def oneshot(self) -> bool:
        return self.process_running()

    async def poll(self) -> bool:
        while True:
            if not self.process_running():
                return False

            await asyncio.sleep(Process._delay)