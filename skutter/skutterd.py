import signal
import types


class Skutterd(object):
    _SIGTERM = (False, None)
    _SIGINT = (False, None)
    _SIGHUP = (False, None)

    @classmethod
    def run(cls):
        pass

    @classmethod
    def signal(cls, signum: int, frame: types.FrameType) -> None:

        if signum == signal.SIGHUP:
            cls._SIGHUP = (True, frame)

        elif signum == signal.SIGINT:
            cls._SIGINT = (True, frame)

        elif signum == signal.SIGTERM:
            cls._SIGTERM = (True, frame)


# Signal Handlers
signal.signal(signal.SIGHUP, Skutterd.signal)
signal.signal(signal.SIGINT, Skutterd.signal)
signal.signal(signal.SIGTERM, Skutterd.signal)
