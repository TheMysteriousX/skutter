import asyncio
import logging
import psutil

from typing import Union

log = logging.getLogger(__name__)

NEGATIVE = False
POSITIVE = True


class Process(object):
    _delay = 0
    _process = ''

    _type = 'poll'

    def __init__(self,  config: dict, delay: int=60) -> None:
        log.info('Loaded plugin: %s', __name__)
        self._process = config['name']
        self._delay = delay

    def get_pid(self) -> Union[None, int]:
        log.debug("Hunting for process named %s", self._process)
        for p in psutil.process_iter():
            log.debug('Examining process %s', p.name())

            if p.name() == self._process:
                return p.pid

        return None

    def process_running(self) -> bool:
        return POSITIVE if self.get_pid() else NEGATIVE

    def oneshot(self) -> bool:
        return self.process_running()

    async def poll(self, current_state: bool) -> bool:
        while True:
            p = self.process_running()
            if p != current_state:
                # State has changed
                return p

            log.debug('Process state unchanged, going back to sleep for %is', self._delay)

            await asyncio.sleep(self._delay)