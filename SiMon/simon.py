import os
import os.path
import sys
import time
import logging
import glob
# from daemonize import Daemonize

import numpy as np

import daemon 
from daemon import pidfile
from daemonize import Daemonize
from SiMon import utilities
from SiMon import config 
from SiMon.simulation_container import SimulationContainer
from SiMon.priority_scheduler import PriorityScheduler
from SiMon.visualization import VisualizationCallback
from SiMon.dashboard.apps.dashboard_callback import DashboardCallback 



class SiMon(object):
    """
    Main code of Simulation Monitor (SiMon).
    """

    def __init__(
        self,
        logger,
        pidfile='SiMon.pid',
        stdin="/dev/tty",
        stdout="/dev/tty",
        stderr="/dev/tty",
        mode="interactive",
        cwd=os.getcwd(),
        config_file="SiMon.conf",
    ):

        # Only needed in interactive mode
        conf_path = os.path.join(cwd, config_file)
        self.config = utilities.parse_config_file(os.path.join(cwd, config_file), section='SiMon')
        config.current_config = self.config

        if self.config is None:
            print(
                "Error: Configuration file SiMon.conf does not exist on the current path: %s"
                % cwd
            )
            if (
                utilities.get_input(
                    "Would you like to generate the default SiMon.conf file to the current directory? [Y/N] "
                ).lower()
                == "y"
            ):
                # shutil.copyfile(os.path.join(__simon_dir__, 'SiMon.conf'), os.path.join(cwd, 'SiMon.conf'))
                utilities.generate_conf()
                print(
                    "SiMon.conf is now on the current directly. Please edit it accordingly and run ``simon [start|stop|interactive|i]``."
                )
            sys.exit(-1)
        else:
            if "Root_dir" in self.config:
                cwd = self.config["Root_dir"]
            else:
                print(
                    "Item Root_dir is missing in configuration file SiMon.conf. SiMon cannot start. Exiting..."
                )
                sys.exit(-1)

        # make sure that cwd is the absolute path
        if not os.path.isabs(cwd):
            cwd = os.path.join(
                os.getcwd(), cwd
            )  # now cwd is the simulation data root directory

        if not os.path.isdir(cwd):
            if (
                utilities.get_input(
                    "Simulation root directory does not exist. "
                    "Would you like to generate test simulations on the current directory? [Y/N] "
                ).lower()
                == "y"
            ):
                import SiMon.ic_generator_demo as ic_generator_demo

                ic_generator_demo.generate_ic(cwd)
                print(
                    "Demo simulations generated. Please start them with ``simon start``"
                )
            else:
                print("Exiting...")
            sys.exit(-1)


        self.stdin_path = stdin
        self.stdout_path = stdout
        self.stderr_path = stderr
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5
        self.mode = mode
        self.cwd = cwd
        self.logger = logger
        self.max_concurrent_jobs = 2

        self.simulations = None
        self.callbacks = []
        self.scheduler = None 

        self.__inited = False 

        os.chdir(cwd)


    def initialize(self):
        if not self.__inited:
            # create a logger 
            self.logger=utilities.get_logger(log_dir=self.cwd, log_file='SiMon_daemon.log')

            # create a container for all simulations
            self.simulations = SimulationContainer(root_dir=self.cwd)

            # load the callbacks
            print(self.config)
            if 'Visualization' in self.config:
                if self.config['Visualization']['Enabled'] is True:
                    self.callbacks.append(VisualizationCallback(container=self.simulations, 
                                                                plot_dir=os.path.join(self.cwd, self.config['Visualization']['Dir'])))

            if 'Dashboard' in self.config:
                print('1yy')
                if self.config['Dashboard']['Enabled'] is True:
                    print('2yy')
                    self.callbacks.append(DashboardCallback(container=self.simulations))

            # create a scheduler 
            self.scheduler = PriorityScheduler(self.simulations, self.logger, self.config, self.callbacks)
        
            self.__inited = True 




    def interactive_task_handler(self, opt):
        """
        Handles the task selection input from the user (in the interactive mode).

        :param opt: The option from user input.
        """

        if opt == "q":  # quit interactive mode
            sys.exit(0)
        if opt == "l":  # list all simulations
            print(self.simulations)
        if opt in ["s", "n", "r", "c", "x", "t", "d", "k", "b", "p"]:
            if self.mode == "interactive":
                if (
                    self.simulations.selected_inst is None
                    or len(list(self.simulations.selected_inst)) == 0
                    or opt == "s"
                ):
                    self.simulations.selected_inst = utilities.id_input(
                        "Please specify a list of IDs (seperated by comma): "
                    )
                    sys.stdout.write(
                        "Instances %s selected.\n" % self.simulations.selected_inst
                    )

        # TODO: use message? to rewrite this part in a smarter way
        if opt == "n":  # start new simulations
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_start()
                    # reset the selection list
                    self.simulations.selected_inst = []
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Simulation not started.\n"
                        % sid
                    )
        if opt == "r":  # restart simulations
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_restart()
                    # reset the selection list
                    self.simulations.selected_inst = []
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Simulation not restarted.\n"
                        % sid
                    )
        if (
            opt == "c"
        ):  # check the recent or current status of the simulation and print it
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_collect_recent_output_message()
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Simulation not restarted.\n"
                        % sid
                    )
        if opt == "x":  # execute an UNIX shell command in the simulation directory
            print("Executing an UNIX shell command in the selected simulations.")
            shell_command = utilities.get_input("CMD>> ")
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_shell_exec(shell_command=shell_command)
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Cannot execute command.\n"
                        % sid
                    )
        if (
            opt == "t"
        ):  # soft-stop the simulation in the ways that supported by the code
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_stop()
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Simulation not stopped.\n"
                        % sid
                    )
        if opt == "d":  # delete the simulation tree and all its data
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_delete()
                    # reset the selection list
                    self.simulations.selected_inst = []
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Cannot delete simulation.\n"
                        % sid
                    )
        if opt == "k":  # kill the UNIX process associate with a simulation task
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_kill()
                    # reset the selection list
                    self.simulations.selected_inst = []
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Cannot kill simulation.\n"
                        % sid
                    )
        if (
            opt == "b"
        ):  # backup the simulation checkpoint files (for restarting purpose in the future)
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_backup_checkpoint()
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Cannot backup checkpoint.\n"
                        % sid
                    )
        if (
            opt == "p"
        ):  # perform (post)-processing (usually after the simulation is done)
            for sid in self.simulations.selected_inst:
                sim_inst = self.simulations.get_simulation_by_id(sid)
                if sim_inst is not None:
                    sim_inst.sim_finalize()
                    # reset the selection list
                    self.simulations.selected_inst = []
                else:
                    print(
                        "The selected simulation with ID = %d does not exist. Cannot perform postprocessing.\n"
                        % sid
                    )


    def run(self):
        """
        The entry point of this script if it is run with the daemon.
        """
        if not self.__inited:
            self.initialize()
            
        os.chdir(self.cwd)
        self.simulations.build_simulation_tree()
        while True:
            # print('[%s] Auto scheduled' % datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            self.scheduler.schedule()
            sys.stdout.flush()
            sys.stderr.flush()
            if "Daemon_sleep_time" in self.config:
                time.sleep(self.config["Daemon_sleep_time"])
            else:
                time.sleep(180)

    def interactive_mode(self, autoquit=False):
        """
        Run SiMon in the interactive mode. In this mode, the user can see an overview of the simulation status from the
        terminal, and control the simulations accordingly.
        :return:
        """
        if not self.__inited:
            self.initialize()

        os.chdir(self.cwd)
        print(self.simulations)
        choice = ""
        if autoquit is False:
            while choice != "q":
                choice = utilities.print_task_selector()
                self.interactive_task_handler(choice)

    @staticmethod
    def daemon_mode(working_dir):
        """
        Run SiMon in the daemon mode.

        In this mode, SiMon will behave as a daemon process. It will scan all simulations periodically, and take measures
        if necessary.
        :return:
        """
        print('Working dir = ', working_dir)
        app = SiMon(
            logger=None,
            pidfile=os.path.join(working_dir, "SiMon_daemon.pid"),
            stdout=os.path.join(working_dir, "SiMon.out.txt"),
            stderr=os.path.join(working_dir, "SiMon.err.txt"),
            cwd=working_dir,
            mode="daemon",
        ).run()

        # initialize the daemon runner
        # logger=utilities.get_logger(log_dir=app.cwd, log_file='SiMon_daemon.log')
        # daemon = Daemonize(app='SiMon', pid=os.path.join(app.cwd, app.pidfile_path), action=app.run, logger=logger)
        # daemon.start()

        # with daemon.DaemonContext(stdout=sys.stdout, stderr=sys.stderr):
        # with daemon.DaemonContext(pidfile=pidfile.TimeoutPIDLockFile(os.path.join(working_dir, "SiMon_daemon.pid"))):
            # app.run()


def main():
    # execute only if run as a script
    if len(sys.argv) == 1:
        print("Running SiMon in the interactive mode...")
        s = SiMon(logger=utilities.get_logger())
        s.interactive_mode(autoquit=True)
    elif len(sys.argv) > 1:
        if sys.argv[1] in ["start", "stop", "restart"]:
            if sys.argv[1] == "start":
                # test if the daemon is already started
                if os.path.isfile("SiMon_daemon.pid"):
                    try:
                        f_pid = open("SiMon_daemon.pid")
                        simon_pid = int(f_pid.readline())
                        os.kill(
                            simon_pid, 0
                        )  # test whether the process exists, does not kill the process
                        print(
                            "Error: the SiMon daemon is already running with process ID: %d"
                            % simon_pid
                        )
                        print(
                            "Please make sure that you stop the daemon before starting it. Exiting..."
                        )
                        sys.exit(-1)
                    except (ValueError, OSError):
                        pass
            # The python-daemon library will handle the start/stop/restart arguments by itself
            print('Starting daemon mode...')
            SiMon.daemon_mode(os.getcwd())
        elif sys.argv[1] in ["interactive", "i", "-i"]:
            s = SiMon(logger=utilities.get_logger())
            s.interactive_mode()
        else:
            print(sys.argv[1])
            SiMon.print_help()
            sys.exit(0)


if __name__ == "__main__":
    main()
