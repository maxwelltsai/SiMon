# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python testdaemon.py start

# standard python libs
import logging
import sys

from daemon import runner
from daemon_mode import DaemonModeManager
from interactive_mode import InteractiveModeManager


def print_help():
    print('Usage: python run.py start|stop|interactive|help')
    print('\tstart: start the daemon')
    print('\tstop: stop the daemon')
    print('\tinteractive: run in interactive mode (no daemon) [default]')
    print('\thelp: print this help message')


def interactive_mode():
    """
    Run SiMon in the interactive mode. In this mode, the user can see an overview of the simulation status from the
    terminal, and control the simulations accordingly.
    :return:
    """
    imm = InteractiveModeManager()
    imm.main()


def daemon_mode():
    """
    Run SiMon in the daemon mode.

    In this mode, SiMon will behave as a daemon process. It will scan all simulations periodically, and take measures
    if necessary.
    :return:
    """
    app = DaemonModeManager()

    # log system
    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("/tmp/testdaemon.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    daemon_runner = runner.DaemonRunner(app)

    # This ensures that the logger file handle does not get closed during daemonization
    daemon_runner.daemon_context.files_preserve = [handler.stream]
    daemon_runner.do_action()  # fixed time period of calling run()


if len(sys.argv) == 1:
    print('Running SiMon in the interactive mode...')
    interactive_mode()
elif len(sys.argv) > 1:
    if sys.argv[1] in ['start', 'stop']:
        # python daemon will handle these two arguments
        daemon_mode()
    elif sys.argv[1] in ['interactive', 'i']:
        interactive_mode()
    else:
        print_help()
        sys.exit(0)

