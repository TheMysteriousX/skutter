import yaml


class Configuration(object):
    _config = None

    @classmethod
    def load(cls, path: str) -> bool:
        cls._config = yaml.safe_load(open(path, 'r'))
        return True