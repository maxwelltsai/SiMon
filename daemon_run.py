# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python testdaemon.py start

# standard python libs
import logging

from daemon import runner
from daemon_mode import DaemonModeManager

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
