
class JobManager(object):
    _check_module = ''
    _check_config = {}

    _action_module = ''
    _action_config = {}

    def check(self, module: str, config: dict) -> None:
        self._check_module = module
        self._check_config = config

    def action(self, module: str, config: dict) -> None:
        self._check_module = module
        self._check_config = config