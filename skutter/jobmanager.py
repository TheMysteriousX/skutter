import logging

log = logging.getLogger(__name__)

class JobManager(object):
    _check_module = ''
    _check_config = {}

    _action_module = ''
    _action_config = {}

    def check(self, module: str, config: dict) -> None:
        self._check_module = module
        self._check_config = config

    def action(self, module: str, config: dict) -> None:
        self._action_module = module
        self._action_config = config

    def init(self) -> None:
        log.debug('Initialising job: check %s, action %s', self._check_module, self._action_module)