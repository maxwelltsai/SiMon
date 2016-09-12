# To kick off the script, run the following from the python directory:
#   PYTHONPATH=`pwd` python testdaemon.py start

#standard python libs
import logging
import time
import os

#third party libs
from daemon import runner
from run_manager2 import Run_Manager


app = Run_Manager(os.path.join(os.getcwd(),'run_mgr_daemon.pid'),
        stdout=os.path.join(os.getcwd(),'out'), stderr=os.path.join(os.getcwd(),'err'), mode='daemon')
#app = Run_Manager(os.path.join(os.getcwd(),'run_mgr_daemon.pid'),
#        mode='daemon')
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/tmp/testdaemon.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
#This ensures that the logger file handle does not get closed during daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
