import logging
import stevedore

from stevedore.exception import NoMatches

log = logging.getLogger(__name__)


class JobManager(object):
    _check_module = ''
    _check_config = {}

    _check = None

    _action_module = ''
    _action_config = {}

    _action = None

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

        try:
            self._action = stevedore.DriverManager(namespace='skutter.plugins.actions',
                                                   name=self._action_module,
                                                   invoke_on_load=True,
                                                   invoke_args=(self._action_config,)
                                                   )
        except NoMatches as e:
            log.error("Unable to find action plugin called %s, ignoring job", self._action_module)
            return False

        return True

    async def poll(self):
        pass
