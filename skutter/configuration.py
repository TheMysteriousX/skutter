import logging
import yaml

from typing import Any

from skutter import JobManager

log = logging.getLogger(__name__)


class Configuration(object):
    _config = None
    _jobs = []

    _kvp = {}
    _defaults = {
        'systemd': False,
        'rundir': '/var/run/skutter/',
        'conf': './conf/skutter.yaml'
    }

    @classmethod
    def load(cls, path: str) -> None:
        log.info("Loading configuration from %s", path)
        cls._config = yaml.safe_load(open(path, 'r'))

    @classmethod
    def parse(cls) -> None:
        log.debug("Parsing configuration: root")
        cls.parse_service(cls._config['service'])
        cls.parse_jobs(cls._config['jobs'])

    @classmethod
    def parse_service(cls, conf: dict) -> None:
        log.debug("Parsing configuration: root:service")
        for key, value in conf.items():
            cls._kvp[key] = value

    @classmethod
    def parse_jobs(cls, conf: dict) -> None:
        log.debug("Parsing configuration: root:jobs")
        cls._jobs = [cls.parse_job(y, JobManager(x)) for x, y in conf.items()]

    @classmethod
    def parse_job(cls, conf: dict, j: JobManager) -> JobManager:
        log.debug("Parsing configuration: root:jobs:job")
        j.check(*cls.parse_check(conf['check']))
        j.paction(*cls.parse_action(conf['positive-action']))
        j.naction(*cls.parse_action(conf['negative-action']))
        return j

    @classmethod
    def parse_check(cls, conf: dict) -> (str, dict):
        log.debug("Parsing configuration: root:jobs:job:check")
        return conf['module'], conf['config']

    @classmethod
    def parse_action(cls, conf: dict) -> (str, dict):
        log.debug("Parsing configuration: root:jobs:job:action")
        return conf['module'], conf['config']

    @classmethod
    def get_job_managers(cls) -> list:
        log.debug("Returning %i job managers", len(cls._jobs))
        for j in cls._jobs:
            yield j

    @classmethod
    def get(cls, key: str) -> Any:
        if key in cls._kvp:
            log.debug("Found kvp: %s -> %s", key, cls._kvp[key])
            return cls._kvp[key]
        elif key in cls._defaults:
            log.debug("Default kvp: %s -> %s", key, cls._defaults[key])
            return cls._defaults[key]
        else:
            log.debug("kvp not found: %s, key")
            return None

    @classmethod
    def args(cls, args: dict) -> None:
        cls._kvp.update(args)

    @classmethod
    def reset(cls) -> None:
        cls._kvp = {}
        cls._config = None
        cls._kvp.update(cls._defaults)

    # Exit Codes
    NO_ERROR = 0
    FORK_FAILED = 1
    LOG_SETUP_FAILED = 2
    BROKEN_LOGGING = 3
    LIBSKUTTER_MISSING = 4