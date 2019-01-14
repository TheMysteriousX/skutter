import logging
import stevedore

from stevedore.exception import NoMatches

log = logging.getLogger(__name__)

NEGATIVE = False
POSITIVE = True


class JobManager(object):
    def __init__(self, name: str):
        self._name = name
        self._running = False
        self._current_state = None

        self._check = None
        self._check_module = None
        self._check_config = None

        self._naction = None
        self._naction_module = None
        self._naction_config = None

        self._paction = None
        self._paction_module = None
        self._paction_config = None

    def get_name(self):
        return self._name

    def check(self, module: str, config: dict) -> None:
        self._check_module = module
        self._check_config = config

    def paction(self, module: str, config: dict) -> None:
        self._paction_module = module
        self._paction_config = config

    def naction(self, module: str, config: dict) -> None:
        self._naction_module = module
        self._naction_config = config

    def init(self) -> bool:
        log.debug('Initialising job: check %s, paction %s, naction %s',
                  self._check_module,
                  self._paction_module,
                  self._naction_module)

        try:
            log.info('Attempting to load check plugin %s', self._check_module)
            self._check = stevedore.DriverManager(namespace='skutter.plugins.checks',
                                                  name=self._check_module,
                                                  invoke_on_load=True,
                                                  invoke_args=(self._check_config,)
                                                  )
        except NoMatches as e:
            log.error("%s unable to find check plugin called %s", self._name, self._check_module)
            log.debug(e)
            return False
        except (FileNotFoundError, ImportError) as e:
            log.error("%s encountered an exception while loading check plugin called %s", self._name, self._naction_module)
            log.debug(e)
            return False

        try:
            log.info('Attempting to load paction plugin %s', self._paction_module)
            self._paction = stevedore.DriverManager(namespace='skutter.plugins.actions',
                                                    name=self._paction_module,
                                                    invoke_on_load=True,
                                                    invoke_args=(self._paction_config,)
                                                    )
        except NoMatches as e:
            log.error("%s unable to find action plugin called %s", self._name, self._paction_module)
            return False
        except (FileNotFoundError, ImportError) as e:
            log.error("%s encountered an exception while loading action plugin called %s", self._name, self._paction_module)
            log.debug(e)
            return False

        try:
            log.info('Attempting to load naction plugin %s', self._naction_module)
            self._naction = stevedore.DriverManager(namespace='skutter.plugins.actions',
                                                    name=self._naction_module,
                                                    invoke_on_load=True,
                                                    invoke_args=(self._naction_config,)
                                                    )
        except NoMatches:
            log.error("%s unable to find action plugin called %s", self._name, self._naction_module)
            return False
        except (FileNotFoundError, ImportError) as e:
            log.error("%s encountered an exception while loading action plugin called %s", self._name, self._naction_module)
            log.debug(e)
            return False

        return True

    async def poll(self):
        log.debug("Executing check %s with config %s", self._check_module, self._check_config)

        if self._current_state is None:
            log.debug('Oneshot polling to establish current state')
            self._current_state = self._check.driver.oneshot()

            log.info('Initial check result is %s, running action plugin once', 'POSITIVE' if self._current_state == POSITIVE else 'NEGATIVE')
            if self._current_state == POSITIVE:
                self._paction.driver.do()
            else:
                self._naction.driver.do()

        self._running = True
        self._current_state = await self._check.driver.poll(self._current_state)
        self._running = False
        return self

    def act(self):
        if self._current_state == POSITIVE:
            self._naction.driver.undo()
            self._paction.driver.do()
        else:
            self._paction.driver.undo()
            self._naction.driver.do()

    def cleanup(self):
        log.info('Reverting actions to base state')
        if self._current_state == POSITIVE:
            self._paction.driver.undo()
        else:
            self._naction.driver.undo()

