import logging
import os
import signal
import sys
import time
import types

from skutter import Configuration


class Skutterd(object):
    _run = True
    _SIGTERM = (False, None)
    _SIGINT = (False, None)
    _SIGHUP = (False, None)

    _jobs = []

    @classmethod
    def run(cls) -> None:
        # Load and prepare configuration
        Configuration.load(Configuration.get('conf'))
        Configuration.parse()

        # Set up managers
        cls._jobs = Configuration.get_job_managers()

        if Configuration.get('systemd'):
            cls.daemonise()

        # Enter main loop
        cls.loop()

    @classmethod
    def daemonise(cls) -> None:
        cls.fork()
        cls.env()
        cls.fork()
        cls.descriptors()

    @classmethod
    def fork(cls) -> None:
        try:
            pid = os.fork()

            if pid > 0:
                sys.exit(0)

        except OSError as e:
            sys.exit(1)

    @classmethod
    def env(cls) -> None:
        os.setsid()
        os.chdir(Configuration.get('rundir'))
        os.umask(0o22)

    @classmethod
    def descriptors(cls) -> None:
        sys.stdout.flush()
        sys.stderr.flush()

        os.dup2(open(os.devnull, 'r').fileno(), sys.stdin.fileno())
        os.dup2(open(os.devnull, 'a+').fileno(), sys.stdout.fileno())
        os.dup2(open(os.devnull, 'a+').fileno(), sys.stderr.fileno())

    @classmethod
    def loop(cls) -> None:
        while cls._run:
            print("Loop")
            time.sleep(5)

    @classmethod
    def signal(cls, signum: int, frame: types.FrameType) -> None:

        if signum == signal.SIGHUP:
            cls._SIGHUP = (True, frame)

        elif signum == signal.SIGINT:
            cls._SIGINT = (True, frame)

        elif signum == signal.SIGTERM:
            cls._SIGTERM = (True, frame)

        cls._run = False


# Signal Handlers
signal.signal(signal.SIGHUP, Skutterd.signal)
signal.signal(signal.SIGINT, Skutterd.signal)
signal.signal(signal.SIGTERM, Skutterd.signal)
