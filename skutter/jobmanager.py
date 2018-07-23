import logging
import stevedore

from stevedore.exception import NoMatches

log = logging.getLogger(__name__)

NEGATIVE = False
POSITIVE = True


class JobManager(object):
    _check_module = ''
    _check_config = {}

    _check = None

    _action_module = ''
    _action_config = {}

    _action = None

    _running = False
    _current_state = None

    def check(self, module: str, config: dict) -> None:
        self._check_module = module
        self._check_config = config

    def action(self, module: str, config: dict) -> None:
        self._action_module = module
        self._action_config = config

    def init(self) -> bool:
        log.debug('Initialising job: check %s, action %s', self._check_module, self._action_module)

        try:
            self._check = stevedore.DriverManager(namespace='skutter.plugins.checks',
                                                  name=self._check_module,
                                                  invoke_on_load=True,
                                                  invoke_args=(self._check_config,)
                                                  )
        except NoMatches as e:
            log.error("Unable to find check plugin called %s, ignoring job", self._check_module)
            return False

        #try:
        #    self._action = stevedore.DriverManager(namespace='skutter.plugins.actions',
        #                                           name=self._action_module,
        #                                           invoke_on_load=True,
        #                                           invoke_args=(self._action_config,)
        #                                           )
        except NoMatches as e:
            log.error("Unable to find action plugin called %s, ignoring job", self._action_module)
            return False

        return True

    async def poll(self):
        log.debug("Executing check %s with config %s", self._check_module, self._check_config)

        if self._current_state is None:
            log.debug("Oneshot polling to establish current state")
            self._current_state = self._check.driver.oneshot()
            return self

        self._running = True
        self._current_state = await self._check.driver.poll(self._current_state)
        self._running = False
        return self

    def act(self):
        pass
