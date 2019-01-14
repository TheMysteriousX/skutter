import asyncio
import functools
import logging
import os
import signal
import sys
import traceback
import types

from asyncio import CancelledError
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

    _loop = None

    @classmethod
    def run(cls) -> None:
        # Load and prepare configuration
        Configuration.load(Configuration.get('conf'))
        Configuration.parse()

        # If we're not running under systemd and not in debug mode, do the double fork dance
        if Configuration.get('systemd') and 'SKUTTER' not in os.environ:
            cls.daemonise()

        # Switch on the event loop
        cls._loop = asyncio.get_event_loop()
        cls._loop.add_signal_handler(signal.SIGHUP, functools.partial(cls.signal, signal.SIGHUP))
        cls._loop.add_signal_handler(signal.SIGINT, functools.partial(cls.signal, signal.SIGINT))
        cls._loop.add_signal_handler(signal.SIGTERM, functools.partial(cls.signal, signal.SIGTERM))

        # Set up Job Managers
        for j in Configuration.get_job_managers():
            if j.init():
                cls._jobs.append(j)
            else:
                log.error("Failed to load job named %s", j.get_name())

        # Enter main loop
        cls.loop()

        # We're exiting, close the event loop
        log.debug('Terminating event loop')
        cls._loop.close()
        log.debug('Event loop terminated')

        [j.cleanup() for j in cls._jobs]

    @classmethod
    def terminate(cls):
        # Cancel all tasks
        for task in asyncio.Task.all_tasks():
            task.cancel()

    @classmethod
    def daemonise(cls) -> None:
        cls.fork()
        cls.env()
        cls.fork()
        cls.descriptors()
        cls.writepid()

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
                try:
                    tasks = [x.poll() for x in cls._jobs]

                    if len(tasks) == 0:
                        log.error('No jobs found or all jobs failed to load - exiting')
                        cls._run = False
                        return

                    finished, unfinished = cls._loop.run_until_complete(asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED))

                    log.debug('Checking for finished tasks')

                    for task in finished:
                        job = task.result()
                        log.debug("Job with check %s returned, new state is %s", job._check_module, job._current_state)

                        job.act()
                        unfinished.add(job)
                except CancelledError as e:
                    log.debug("Tasks were cancelled, was a signal received?")

            if cls.handle_signal():
                log.info('Terminal signal received, leaving main loop')
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
    def signal(cls, signum: int, frame: types.FrameType = None) -> None:
        log.info("Signal %i received", signum)

        if signum == signal.SIGHUP:
            cls._SIGHUP = (True, frame)
            cls.terminate()

        elif signum == signal.SIGINT:
            cls._SIGINT = (True, frame)
            cls.terminate()

        elif signum == signal.SIGTERM:
            cls._SIGTERM = (True, frame)
            cls.terminate()

        cls._run = False

    @classmethod
    def writepid(cls):
        with open(Configuration.get('pidfile'), 'w') as f:
            f.write(str(os.getpid()))

    @classmethod
    def logging(cls) -> None:
        log.critical('Configuring logging')
        try:
            # Grab the root logger so we can set the logging configuration globally
            cls.root_logger = logging.getLogger('skutter')
            cls.root_logger.setLevel(logging.DEBUG)

            # Define the log format
            cls.console_format = logging.Formatter('%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s')
            cls.system_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

            # Define console handler
            cls.console = logging.StreamHandler()
            cls.console.setLevel(logging.DEBUG)
            cls.console.setFormatter(cls.console_format)

            # Define system handler
            if JournalHandler:
                cls.system = JournalHandler()
            else:
                cls.system = SysLogHandler()

            cls.system.setLevel(logging.DEBUG)
            cls.system.setFormatter(cls.system_format)

            # Attach handlers
            cls.root_logger.addHandler(cls.console)
            #cls.root_logger.addHandler(cls.system)
            # Sysloghandler is garbage

        except Exception as e:
            print('Initialising logger failed; aborting startup as I can\'t tell you when I\'m online!\n')
            print('The underlying exception was: {}\n\n\n'.format(e))

            traceback.print_exc()

            sys.exit(Configuration.BROKEN_LOGGING)
