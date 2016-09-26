# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python testdaemon.py start

# standard python libs
import logging

from daemon import runner
from daemon_mode import DaemonModeManager
from interactive_mode import InteractiveModeManager

user_input = raw_input('select a mode: interactive[i] or daemon[d] \n')

while user_input.lower() not in ['i', 'd']:
    user_input = raw_input('input again: must be either i or d\n')

if user_input.lower() == 'i':
    imm = InteractiveModeManager()
    imm.main()

if user_input.lower() == 'd':
    # instance of run_manager
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
