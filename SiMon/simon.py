import os
import os.path
import sys
import time
import logging
import glob

from SiMon.utilities import Utilities
import numpy as np
try:
    import configparser as cp  # Python 3 only
except ImportError:
    import ConfigParser as cp  # Python 2 only
from fnmatch import fnmatch
from daemon import runner
from SiMon.module_common import SimulationTask

__simon_dir__ = os.path.dirname(os.path.abspath(__file__))
__user_shell_dir__ = os.getcwd()

class SiMon(object):
    """
    Main code of Simulation Monitor (SiMon).
    """

    def __init__(self, pidfile=None, stdin='/dev/tty', stdout='/dev/tty', stderr='/dev/tty',
                 mode='interactive', cwd=os.getcwd(), config_file='SiMon.conf'):
        """
        :param pidfile:
        """

        # Only needed in interactive mode
        conf_path = os.path.join(cwd, config_file)
        self.config = self.parse_config_file(conf_path)

        if self.config is None:
            print('Error: Configuration file SiMon.conf does not exist on the current path: %s' % cwd)
            if Utilities.get_input('Would you like to generate the default SiMon.conf file to the current directory? [Y/N] ').lower() == 'y':
                # shutil.copyfile(os.path.join(__simon_dir__, 'SiMon.conf'), os.path.join(cwd, 'SiMon.conf'))
                Utilities.generate_conf()
                print('SiMon.conf is now on the current directly. Please edit it accordingly and run ``simon [start|stop|interactive|i]``.')
            sys.exit(-1)
        else:
            try:
                cwd = self.config.get('SiMon', 'Root_dir')
            except cp.NoOptionError:
                print('Item Root_dir is missing in configuration file SiMon.conf. SiMon cannot start. Exiting...')
                sys.exit(-1)
        # make sure that cwd is the absolute path
        if not os.path.isabs(cwd):
            cwd = os.path.join(os.getcwd(), cwd)  # now cwd is the simulation data root directory
        if not os.path.isdir(cwd):
            if Utilities.get_input('Simulation root directory does not exist. '
                                   'Would you like to generate test simulations on the current directory? [Y/N] ').lower() == 'y':
                import SiMon.ic_generator_demo as ic_generator_demo
                ic_generator_demo.generate_ic(cwd)
                print('Demo simulations generated. Please start them with ``simon start``')
            else:
                print('Exiting...')
            sys.exit(-1)

        self.module_dict = self.register_modules()

        self.selected_inst = []  # A list of the IDs of selected simulation instances
        self.sim_inst_dict = dict()  # the container of all SimulationTask objects (ID to object mapping)
        self.sim_inst_parent_dict = dict()  # given the current path, find out the instance of the parent

        # TODO: create subclass instance according to the config file
        self.sim_tree = SimulationTask(0, 'root', cwd, SimulationTask.STATUS_NEW)
        self.stdin_path = stdin
        self.stdout_path = stdout
        self.stderr_path = stderr
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5
        self.mode = mode
        self.cwd = cwd
        self.inst_id = 0
        self.logger = None
        self.max_concurrent_jobs = 2

        if self.config.has_option('SiMon', 'Max_concurrent_jobs'):
            self.max_concurrent_jobs = self.config.getint('SiMon', 'Max_concurrent_jobs')

        os.chdir(cwd)

    @staticmethod
    def parse_config_file(config_file):
        """
        Parse the configure file (SiMon.conf) for starting SiMon. The basic information of Simulation root directory
        must exist in the configure file before SiMon can start. A minimum configure file of SiMon looks like:

        ==============================================
        [SiMon]
        Root_dir: <the_root_dir_of_the_simulation_data>
        ==============================================

        :return: return 0 if succeed, -1 if failed (file not exist, and cannot be created). If the file does not exist
        but a new file with default values is created, the method returns 1.
        """
        conf = cp.ConfigParser()
        if os.path.isfile(config_file):
            conf.read(config_file)
            return conf
        else:
            return None

    @staticmethod
    def register_modules():
        """
        Register modules
        :return: A dict-like mapping between the name of the code and the filename of the module.
        """
        mod_dict = dict()
        module_candidates = glob.glob(os.path.join(__simon_dir__, 'module_*.py'))
        module_cwd = glob.glob(os.path.join(__user_shell_dir__, 'module_*.py'))  # load the modules also from cwd
        for m_cwd in module_cwd:
            module_candidates.append(m_cwd)
        for mod_name in module_candidates:
            sys.path.append(__simon_dir__)
            sys.path.append(os.getcwd())
            mod_name = os.path.basename(mod_name)
            mod = __import__(mod_name.split('.')[0])
            if hasattr(mod, '__simulation__'):
                # it is a valid SiMon module
                mod_dict[mod.__simulation__] = mod_name.split('.')[0]
        return mod_dict

    def traverse_simulation_dir_tree(self, pattern, base_dir, files):
        """
        Traverse the simulation file structure tree (Breadth-first search), until the leaf (i.e. no restart directory)
        or the simulation is not restartable (directory with the 'STOP' file).
        """
        for filename in sorted(files):
            if fnmatch(filename, pattern):
                if os.path.isdir(os.path.join(base_dir, filename)):
                    fullpath = os.path.join(base_dir, filename)
                    self.inst_id += 1
                    id = self.inst_id

                    # Try to determine the simulation code type by reading the config file
                    sim_config = self.parse_config_file(os.path.join(fullpath, 'SiMon.conf'))
                    sim_inst = None
                    if sim_config is not None:
                        try:
                            code_name = sim_config.get('Simulation', 'Code_name')
                            if code_name in self.module_dict:
                                sim_inst_mod = __import__(self.module_dict[code_name])
                                sim_inst = getattr(sim_inst_mod, code_name)(id, filename, fullpath,
                                                                            SimulationTask.STATUS_NEW,
                                                                            logger=self.logger)
                        except (cp.NoOptionError, cp.NoSectionError):
                            pass
                    else:
                        continue
                    if sim_inst is None:
                        continue
                    self.sim_inst_dict[id] = sim_inst
                    sim_inst.id = id
                    sim_inst.fulldir = fullpath
                    sim_inst.name = filename

                    # register child to the parent
                    self.sim_inst_parent_dict[base_dir].restarts.append(sim_inst)
                    sim_inst.level = self.sim_inst_parent_dict[base_dir].level + 1
                    # register the node itself in the parent tree
                    self.sim_inst_parent_dict[fullpath] = sim_inst
                    sim_inst.parent_id = self.sim_inst_parent_dict[base_dir].id

                    # Get simulation status
                    sim_inst.sim_get_status()

                    self.sim_inst_dict[sim_inst.parent_id].status = sim_inst.status

                    if (sim_inst.t > self.sim_inst_dict[sim_inst.parent_id].t and
                            not os.path.isfile(os.path.join(sim_inst.fulldir, 'ERROR'))) \
                            or sim_inst.status == SimulationTask.STATUS_RUN:
                        # nominate as restart candidate
                        self.sim_inst_dict[sim_inst.parent_id].cid = sim_inst.id
                        self.sim_inst_dict[sim_inst.parent_id].t_max_extended = sim_inst.t_max_extended

    def build_simulation_tree(self):
        """
        Generate the simulation tree data structure, so that a restarted simulation can trace back
        to its ancestor.

        :return: The method has no return. The result is stored in self.sim_tree.
        :type: None
        """
        os.chdir(self.cwd)
        self.sim_inst_dict = dict()

        self.sim_tree = SimulationTask(0, 'root', self.cwd, SimulationTask.STATUS_NEW)  # initially only the root node
        self.sim_inst_dict[0] = self.sim_tree  # map ID=0 to the root node
        self.sim_inst_parent_dict[self.cwd.strip()] = self.sim_tree  # map the current dir to be the sim tree root
        self.inst_id = 0

        for directory, dirnames, filenames in os.walk(self.cwd):
            self.traverse_simulation_dir_tree('*', directory, dirnames)

        # Synchronize the status tree (status propagation)
        update_needed = True
        max_iter = 0
        while update_needed and max_iter < 30:
            max_iter += 1
            inst_status_modified = False
            for i in self.sim_inst_dict:
                if i == 0:
                    continue
                inst = self.sim_inst_dict[i]
                if inst.status == SimulationTask.STATUS_RUN or inst.status == SimulationTask.STATUS_DONE:
                    if inst.parent_id > 0 and self.sim_inst_dict[inst.parent_id].status != inst.status:
                        # propagate the status of children (restarted simulation) to parents' status
                        self.sim_inst_dict[inst.parent_id].status = inst.status
                        inst_status_modified = True
            if inst_status_modified is True:
                update_needed = True
            else:
                update_needed = False
        return 0
        # print self.sim_tree

    def print_sim_status_overview(self, sim_id):
        """
        Output an overview of the simulation status in the terminal.

        :return: start and stop time
        :rtype: int
        """
        print(self.sim_inst_dict[sim_id])  # print the root node will cause the whole tree to be printed
        return self.sim_inst_dict[sim_id].t_min, self.sim_inst_dict[sim_id].t_max

    @staticmethod
    def print_help():
        print('Usage: python simon.py [start|stop|interactive|help]')
        print('\tTo show an overview of job status and quit: python simon.py (no arguments)')
        print('\tstart: start the daemon')
        print('\tstop: stop the daemon')
        print('\tinteractive/i/-i: run in interactive mode (no daemon)')
        print('\thelp: print this help message')

    @staticmethod
    def print_task_selector():
        """
        Prompt a menu to allow the user to select a task.

        :return: current selected task symbol.
        """
        opt = ''
        while opt.lower() not in ['l', 's', 'n', 'r', 'c', 'x', 't', 'd', 'k', 'b', 'p', 'q']:
            sys.stdout.write('\n=======================================\n')
            sys.stdout.write('\tList Instances (L), \n\tSelect Instance (S), '
                             '\n\tNew Run (N), \n\tRestart (R), \n\tCheck status (C), '
                             '\n\tStop Simulation (T), \n\tDelete Instance (D), \n\tKill Instance (K), '
                             '\n\tBackup Restart File (B), \n\tPost Processing (P), \n\tUNIX Shell (X), '
                             '\n\tQuit (Q): \n')
            opt = Utilities.get_input('\nPlease choose an action to continue: ').lower()

        return opt

    def task_handler(self, opt):
        """
        Handles the task selection input from the user (in the interactive mode).

        :param opt: The option from user input.
        """

        if opt == 'q':  # quit interactive mode
            sys.exit(0)
        if opt == 'l':  # list all simulations
            self.build_simulation_tree()
            self.print_sim_status_overview(0)
        if opt in ['s', 'n', 'r', 'c', 'x', 't', 'd', 'k', 'b', 'p']:
            if self.mode == 'interactive':
                if self.selected_inst is None or len(self.selected_inst) == 0 or opt == 's':
                    self.selected_inst = Utilities.id_input('Please specify a list of IDs (seperated by comma): ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')

        # TODO: use message? to rewrite this part in a smarter way
        if opt == 'n':  # start new simulations
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_start()
                    # reset the selection list
                    self.selected_inst = []
                else:
                    print('The selected simulation with ID = %d does not exist. Simulation not started.\n' % sid)
        if opt == 'r':  # restart simulations
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_restart()
                    # reset the selection list
                    self.selected_inst = []
                else:
                    print('The selected simulation with ID = %d does not exist. Simulation not restarted.\n' % sid)
        if opt == 'c':  # check the recent or current status of the simulation and print it
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_collect_recent_output_message()
                else:
                    print('The selected simulation with ID = %d does not exist. Simulation not restarted.\n' % sid)
        if opt == 'x':  # execute an UNIX shell command in the simulation directory
            print('Executing an UNIX shell command in the selected simulations.')
            shell_command = Utilities.get_input('CMD>> ')
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_shell_exec(shell_command=shell_command)
                else:
                    print('The selected simulation with ID = %d does not exist. Cannot execute command.\n' % sid)
        if opt == 't':  # soft-stop the simulation in the ways that supported by the code
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_stop()
                else:
                    print('The selected simulation with ID = %d does not exist. Simulation not stopped.\n' % sid)
        if opt == 'd':  # delete the simulation tree and all its data
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_delete()
                    # reset the selection list
                    self.selected_inst = []
                else:
                    print('The selected simulation with ID = %d does not exist. Cannot delete simulation.\n' % sid)
        if opt == 'k':  # kill the UNIX process associate with a simulation task
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_kill()
                    # reset the selection list
                    self.selected_inst = []
                else:
                    print('The selected simulation with ID = %d does not exist. Cannot kill simulation.\n' % sid)
        if opt == 'b':  # backup the simulation checkpoint files (for restarting purpose in the future)
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_backup_checkpoint()
                else:
                    print('The selected simulation with ID = %d does not exist. Cannot backup checkpoint.\n' % sid)
        if opt == 'p':  # perform (post)-processing (usually after the simulation is done)
            for sid in self.selected_inst:
                if sid in self.sim_inst_dict:
                    self.sim_inst_dict[sid].sim_finalize()
                    # reset the selection list
                    self.selected_inst = []
                else:
                    print('The selected simulation with ID = %d does not exist. Cannot perform postprocessing.\n' % sid)

    def auto_scheduler(self):
        """
        The automatic decision maker for the daemon.

        The daemon invokes this method at a fixed period of time. This method checks the
        status of all simulations by traversing to all simulation directories and parsing the
        output files. It subsequently deals with the simulation instance according to the informtion
        gathered.
        """
        os.chdir(self.cwd)
        self.build_simulation_tree()
        schedule_list = []
        # Sort jobs according to priority (niceness)
        sim_niceness_vec = []

        # check how many simulations are running
        concurrent_jobs = 0
        for i in self.sim_inst_dict.keys():
            inst = self.sim_inst_dict[i]
            sim_niceness_vec.append(inst.niceness)
            inst.sim_get_status()  # update its status
            # test if the process is running
            if inst.status == SimulationTask.STATUS_RUN and inst.cid == -1:
                concurrent_jobs += 1

        index_niceness_sorted = np.argsort(sim_niceness_vec)
        for ind in index_niceness_sorted:
            if self.sim_inst_dict[ind].status != SimulationTask.STATUS_DONE and self.sim_inst_dict[ind].id > 0:
                schedule_list.append(self.sim_inst_dict[ind])
                print(self.sim_inst_dict[ind].name)

        for sim in schedule_list:
            if sim.id == 0:  # the root group, skip
                continue
            sim.sim_get_status()  # update its status
            print('Checking instance #%d ==> %s [%s]' % (sim.id, sim.name, sim.status))
            if sim.status == SimulationTask.STATUS_RUN:
                sim.sim_backup_checkpoint()
            elif sim.status == SimulationTask.STATUS_STALL:
                sim.sim_kill()
                self.build_simulation_tree()
            elif sim.status == SimulationTask.STATUS_STOP and sim.level == 1:
                self.logger.warning('STOP detected: '+sim.fulldir)
                # check if there is available slot to restart the simulation
                if concurrent_jobs < self.max_concurrent_jobs and sim.level == 1:
                    # search only top level instance to find the restart candidate
                    # build restart path
                    current_inst = sim
                    # restart the simulation instance at the leaf node
                    while current_inst.cid != -1:
                        current_inst = self.sim_inst_dict[current_inst.cid]
                    print('RESTART: #%d ==> %s' % (current_inst.id, current_inst.fulldir))
                    self.logger.info('RESTART: #%d ==> %s' % (current_inst.id, current_inst.fulldir))
                    current_inst.sim_restart()
                    concurrent_jobs += 1
            elif sim.status == SimulationTask.STATUS_NEW:
                # check if there is available slot to start the simulation
                if concurrent_jobs < self.max_concurrent_jobs:
                    # Start new run
                    sim.sim_start()
                    concurrent_jobs += 1
        self.logger.info('SiMon routine checking completed. Machine load: %d/%d' % (concurrent_jobs,
                                                                                    self.max_concurrent_jobs))

    def run(self):
        """
        The entry point of this script if it is run with the daemon.
        """
        os.chdir(self.cwd)
        self.build_simulation_tree()
        while True:
            # print('[%s] Auto scheduled' % datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            self.auto_scheduler()
            sys.stdout.flush()
            sys.stderr.flush()
            if self.config.has_option('SiMon', 'daemon_sleep_time'):
                time.sleep(self.config.getfloat('SiMon', 'daemon_sleep_time'))
            else:
                time.sleep(180)

    def interactive_mode(self, autoquit=False):
        """
        Run SiMon in the interactive mode. In this mode, the user can see an overview of the simulation status from the
        terminal, and control the simulations accordingly.
        :return:
        """
        print(os.getcwd())
        os.chdir(self.cwd)
        self.build_simulation_tree()
        self.print_sim_status_overview(0)
        choice = ''
        if autoquit is False:
            while choice != 'q':
                choice = SiMon.print_task_selector()
                self.task_handler(choice)

    @staticmethod
    def daemon_mode(simon_dir):
        """
        Run SiMon in the daemon mode.

        In this mode, SiMon will behave as a daemon process. It will scan all simulations periodically, and take measures
        if necessary.
        :return:
        """
        app = SiMon(pidfile=os.path.join(simon_dir, 'SiMon_daemon.pid'),
                    stdout=os.path.join(simon_dir, 'SiMon.out.txt'),
                    stderr=os.path.join(simon_dir, 'SiMon.err.txt'),
                    cwd=simon_dir,
                    mode='daemon')
        # log system
        app.logger = logging.getLogger("DaemonLog")
        if app.config.has_option('SiMon', 'Log_level'):
            log_level = app.config.get('SiMon', 'Log_level')
            if log_level == 'INFO':
                app.logger.setLevel(logging.INFO)
            elif log_level == 'WARNING':
                app.logger.setLevel(logging.WARNING)
            elif log_level == 'ERROR':
                app.logger.setLevel(logging.ERROR)
            elif log_level == 'CRITICAL':
                app.logger.setLevel(logging.CRITICAL)
            else:
                app.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
        handler = logging.FileHandler(os.path.join(simon_dir, 'SiMon.log'))
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        # initialize the daemon runner
        app.logger.info('Starting SiMon daemon at log level %s' % log_level)
        daemon_runner = runner.DaemonRunner(app)
        # This ensures that the logger file handle does not get closed during daemonization
        daemon_runner.daemon_context.files_preserve = [handler.stream]
        daemon_runner.do_action()  # fixed time period of calling run()


def main():
    # execute only if run as a script
    if len(sys.argv) == 1:
        print('Running SiMon in the interactive mode...')
        s = SiMon()
        s.interactive_mode(autoquit=True)
    elif len(sys.argv) > 1:
        if sys.argv[1] in ['start', 'stop', 'restart']:
            if sys.argv[1] == 'start':
                # test if the daemon is already started
                if os.path.isfile('SiMon_daemon.pid'):
                    try:
                        f_pid = open('SiMon_daemon.pid')
                        simon_pid = int(f_pid.readline())
                        os.kill(simon_pid, 0)  # test whether the process exists, does not kill the process
                        print('Error: the SiMon daemon is already running with process ID: %d' % simon_pid)
                        print('Please make sure that you stop the daemon before starting it. Exiting...')
                        sys.exit(-1)
                    except (ValueError, OSError):
                        pass
            # The python-daemon library will handle the start/stop/restart arguments by itself
            try:
                SiMon.daemon_mode(os.getcwd())
            except runner.DaemonRunnerStopFailureError:
                print('Error: the SiMon daemon is not running. There is no need to stop it.')
                sys.exit(-1)
        elif sys.argv[1] in ['interactive', 'i', '-i']:
            s = SiMon()
            s.interactive_mode()
        else:
            print(sys.argv[1])
            SiMon.print_help()
            sys.exit(0)

if __name__ == "__main__":
    main()
