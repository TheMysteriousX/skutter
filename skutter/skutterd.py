import logging
import os
import signal
import sys
import time
import traceback
import types

from logging.handlers import SysLogHandler

from skutter import Configuration

try:
    import systemd.booted
    import systemd.journal

    from systemd.journal import JournalHandler

except ImportError:
    systemd = None
    JournalHandler = None

log = logging.getLogger(__name__)


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

        # If we're not running under systemd, do the double fork dance
        if Configuration.get('systemd'):
            cls.daemonise()

        # Set up Job Managers
        cls._jobs = Configuration.get_job_managers()
        for j in cls._jobs:
            j.init()

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
                sys.exit(Configuration.NO_ERROR)

        except OSError as e:
            sys.exit(Configuration.FORK_FAILED)

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
        while True:
            while cls._run:
                print("Loop")
                time.sleep(5)

            if cls.handle_signal():
                break

    @classmethod
    def handle_signal(cls) -> bool:
        terminate = False

        if cls._SIGHUP[0]:
            # Not supported yet
            cls._SIGHUP = (False, None)
            cls._run = True


        if cls._SIGINT[0]:
            cls._SIGINT = (False, None)
            log.info("SIGINT received, shutting down cleanly")
            terminate = True

        if cls._SIGTERM[0]:
            cls._SIGTERM = (False, None)
            log.info("SIGTERM received, shutting down cleanly")
            terminate = True

        return terminate

    @classmethod
    def signal(cls, signum: int, frame: types.FrameType) -> None:

        if signum == signal.SIGHUP:
            cls._SIGHUP = (True, frame)

        elif signum == signal.SIGINT:
            cls._SIGINT = (True, frame)

        elif signum == signal.SIGTERM:
            cls._SIGTERM = (True, frame)

        cls._run = False

    @classmethod
    def logging(cls) -> None:
        try:
            # Grab the root logger so we can set the logging configuration globally
            l = logging.getLogger('skutter')
            l.setLevel(logging.DEBUG)

            # Define the log format
            console_format = logging.Formatter('%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s')
            system_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

            # Define console handler
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            console.setFormatter(console_format)

            # Define system handler
            if JournalHandler:
                system = JournalHandler()
            else:
                system = SysLogHandler()

            system.setLevel(logging.DEBUG)
            system.setFormatter(system_format)

            # Attach handlers
            l.addHandler(console)
            l.addHandler(system)

        except Exception as e:
            print('Initialising logger failed; aborting startup as I can\'t tell you when I\'m online!\n')
            print('The underlying exception was: {}\n\n\n'.format(e))

            traceback.print_exc()

            sys.exit(Configuration.BROKEN_LOGGING)

# Signal Handlers
signal.signal(signal.SIGHUP, Skutterd.signal)
signal.signal(signal.SIGINT, Skutterd.signal)
signal.signal(signal.SIGTERM, Skutterd.signal)
