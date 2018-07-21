import yaml

from typing import Any

from skutter import JobManager


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
        cls._config = yaml.safe_load(open(path, 'r'))

    @classmethod
    def parse(cls) -> None:
        cls.parse_service(cls._config['service'])
        cls.parse_jobs(cls._config['jobs'])

    @classmethod
    def parse_service(cls, conf: dict) -> None:
        for key, value in conf.items():
            cls._kvp[key] = value

    @classmethod
    def parse_jobs(cls, conf: dict) -> None:
        cls._jobs = [cls.parse_job(y) for x, y in conf.items()]

    @classmethod
    def parse_job(cls, conf: dict) -> JobManager:
        j = JobManager()
        j.check(*cls.parse_check(conf['check']))
        j.action(*cls.parse_action(conf['action']))
        return j

    @classmethod
    def parse_check(cls, conf: dict) -> (str, dict):
        return conf['module'], conf['config']

    @classmethod
    def parse_action(cls, conf: dict) -> (str, dict):
        return conf['module'], conf['config']

    @classmethod
    def get_job_managers(cls) -> list:
        return cls._jobs

    @classmethod
    def get(cls, key: str) -> Any:
        if key in cls._kvp:
            return cls._kvp[key]
        elif key in cls._defaults:
            return cls._defaults[key]
        else:
            return None
