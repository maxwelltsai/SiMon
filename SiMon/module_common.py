import datetime
import abc
import glob
import os
import subprocess
import signal
import time
import sys
import re
import shutil

try:
    import configparser as cp  # Python 3 only
except ImportError:
    import ConfigParser as cp  # Python 2 only


class SimulationTask(object):
    """
    A simulation task is a single simulation which the user requests to finish.
    It is associated with 1) a set of initial conditions specified in the input file,
    2) a (bash) script to start up the code, 3) the status of the simulation (RUN/STOP/model time,
    start timestamp, last output timestamp, parent simulation ID if it is a restart, etc),
    and 4) the ending time of the simulation.

    Notes
    -----
    Traverse the directory structure:
    A hierarchical directory structure may form for a simulation that has been started for multiple times.
    For instance, a simulation is running on the directory '/sim1'. It crashes at T=120. So SiMon
    restarts it by creating a restart directory '/sim1/restart1'. 'restart1' runs until T=200, and then
    again crashes. So SiMon creates '/sim1/restart1/restart1' in attempt to start from T=200.

    """
    # Constants
    STATUS_NEW = 0x0  # newly initialized simulation
    STATUS_STOP = 0x1  # crashed simulation
    STATUS_RUN = 0x2  # the simulation is running
    STATUS_STALL = 0x3  # the simulation is running, but stalled
    STATUS_DONE = 0x4  # the simulation has finished

    STATUS_LABEL = ['NEW', 'STOP', 'RUN', 'STALL', 'DONE']

    __metaclass__ = abc.ABCMeta

    def __init__(self, sim_id, name, full_dir, status, mode='daemon', t_min=0, t_max=0, restarts=None):
        """
        :param sim_id:

        :param name: Usually the name of the simulation directory.
        :type name: basestring

        :param full_dir: The full path of the simulation directory.

        :param status: RUN, STOP, RESTARTED

        :param t_min: default as 0
        :param t_max: default as 0
        :param restarts: default as None
        :return:
        """
        self.id = sim_id
        self.name = name
        self.full_dir = full_dir
        self.status = status
        self.error_type = ''
        self.config_file = 'SiMon.conf'  # the file name of the config file to be placed in each simulation directory
        self.config = None
        self.t = 0  # the current model time
        self.t_min = t_min  # minimum time for the simulation to start
        self.t_max = t_max  # maximum time marking the completion of the simulation
        self.t_max_extended = t_max # extended t_max by restarts
        self.mtime = 0  # timestamp of the last modification of the simulation output files
        self.ctime = 0  # timestamp of the creation of the simulation output files

        # the candidate instance ID to restart in case crashes
        # (-1: no candidate, restart from itself;)
        # (>0: restart from the candidate. If the candidate cannot restart, try siblings)
        self.cid = -1

        self.level = 0
        self.parent_id = -1
        self.mode = mode
        self.niceness = 0  # Priority, same as UNIX (-20 ~ 19, the lower ==> higher priority)
        self.maximum_number_of_checkpoints = 20
        if restarts is None:
            self.restarts = list()
        else:
            self.restarts = restarts  # children
        self.parse_config_file()
        self.sim_get_status()

    def progress(self, count, total, suffix=''):
        bar_len = 40
        if total == 0:
            return ''
        else:
            filled_len = int(round(bar_len * count / float(total)))

            percents = round(100.0 * count / float(total), 1)
            bar = '=' * filled_len + '.' * (bar_len - filled_len)
            # return '[%s] %s%s %s\r' % (bar, percents, '%', suffix)
            return '[%s] %s %s\r' % (bar, '>>>', suffix)

    def __repr__(self, level=0):
        placeholder_dash = "|---" + '-' * (level * 4)
        placeholder_space = "    " + ' ' * (level * 4)
        ctime_str = datetime.datetime.fromtimestamp(self.ctime).strftime('%Y-%m-%d %H:%M:%S')
        mtime_str = datetime.datetime.fromtimestamp(self.mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        progress_bar = self.progress(self.t, self.t_max, int(self.t_max))

        info = "%s\t%s\n%s%s\tT=%g %s \t" % (repr(self.name), mtime_str, placeholder_space,
                                                                                   SimulationTask.STATUS_LABEL[self.status],
                                                                                   self.t, progress_bar)
        ret = "%d%s%s\n" % (self.id, placeholder_dash, info)
        # ret = "    "*level+str(self.id)+repr(self.name)+"\n"
        for child in self.restarts:
            ret += child.__repr__(level + 1)
        return ret

    def parse_config_file(self):
        """
        Parse the configure file (SiMon.conf) for the simulation. If the file does not exist, a new file with default
        values will be created.

        :return: return 0 if succeed, -1 if failed (file not exist, and cannot be created). If the file does not exist
        but a new file with default values is created, the method returns 1.
        """
        conf_fn = os.path.join(self.full_dir, self.config_file)
        conf = cp.ConfigParser()
        if os.path.isfile(conf_fn):
            conf.read(conf_fn)
            self.config = conf
            # synchronize config options to attributes
            if self.config.has_option('Simulation', 'T_end'):
                self.t_max = self.config.getfloat('Simulation', 'T_end')
            if self.config.has_option('Simulation', 'T_start'):
                self.t_min = self.config.getfloat('Simulation', 'T_start')
            if self.config.has_option('Simulation', 'Niceness'):
                self.niceness = self.config.getint('Simulation', 'Niceness')
            if self.config.has_option('Simulation', 'Maximum_n_checkpoints'):
                self.maximum_number_of_checkpoints = self.config.getint('Simulation', 'Maximum_n_checkpoints')

        else:
            if self.id > 0:
                print('WARNING: Simulation configuration file not exists! '
                      'Creating default configuration as SiMon.conf.\n')
            # TODO: write default config file
        return 0

    def sim_start(self):
        """
        Start a new simulation.

        :return: Return 0 if succeed, -1 if failed. If the simulation is already started, then it will do nothing
        but return 1.
        """
        start_script_template = '%s & echo $!>.process.pid'
        orig_dir = os.getcwd()
        os.chdir(self.full_dir)
        # Test if the process is running
        if self.config.has_option('Simulation', 'PID'):
            # It is also possible that the self.proc object is None, because it is created by another process
            pid = self.config.getint('Simulation', 'PID')
            if pid > 0:
                try:
                    os.kill(pid, 0)
                    return 1  # if no exception, the process is already running
                except (ValueError, OSError):
                    pass  # process not started yet
        # If the process is not started yet, then start it in a normal way
        if self.config.has_option('Simulation', 'Start_command'):
            start_cmd = self.config.get('Simulation', 'Start_command')
            # self.proc = subprocess.Popen(start_cmd, shell=True)
            os.system(start_script_template % start_cmd)
            # sleep for a little while to make sure that the pid file exist
            time.sleep(0.5)
            fpid = open('.process.pid', 'r')
            pid = int(fpid.readline())
            fpid.close()
            self.config.set('Simulation', 'PID', str(pid))
            self.config.set('Simulation', 'Timestamp_started', str(time.time()))
            self.config.write(open(self.config_file, 'w'))
        else:
            return -1
        os.chdir(orig_dir)
        return 0

    def sim_restart(self):
        """
        Restart the simulation.

        :return: Return 0 if succeed, -1 if failed. If the simulation is already running, then restart is not
        necessary, the method will do nothing but return 1.
        """
        # Test if the process is running
        start_script_template = '%s & echo $!>.process.pid'
        orig_dir = os.getcwd()
        os.chdir(self.full_dir)
        print 'restarting simulation: ', self.full_dir
        # Test if the process is running
        if self.config.has_option('Simulation', 'PID'):
            # It is also possible that the self.proc object is None, because it is created by another process
            pid = self.config.getint('Simulation', 'PID')
            if pid > 0:
                try:
                    os.kill(pid, 0)
                    return 1  # if no exception, the process is already running
                except (ValueError, OSError):
                    pass  # process not started yet
        # If the process is not started yet, then start it in a normal way
        if self.config.has_option('Simulation', 'Restart_command'):
            start_cmd = self.config.get('Simulation', 'Restart_command')
            print 'restart command:', start_cmd
            # self.proc = subprocess.Popen(start_cmd, shell=True)
            os.system(start_script_template % start_cmd)
            # sleep for a little while to make sure that the pid file exist
            time.sleep(0.5)
            fpid = open('.process.pid', 'r')
            pid = int(fpid.readline())
            fpid.close()
            self.config.set('Simulation', 'PID', str(pid))
            self.config.set('Simulation', 'Timestamp_started', str(time.time()))
            self.config.write(open(self.config_file, 'w'))
        else:
            return -1
        os.chdir(orig_dir)
        return 0

    def sim_get_model_time(self):
        """
        Get the model time of the simulation.

        Because different codes have different output formats, there is no generic way to obtain the model
        time. The user is required to implement this method to properly obtain the time.

        :return: the current model time
        """
        orig_dir = os.getcwd()
        os.chdir(self.full_dir)
        if self.config.has_option('Simulation', 'Output_file'):
            output_file = self.config.get('Simulation', 'Output_file')
            regex = re.compile('\\d+')
            if os.path.isfile(output_file):
                last_line = subprocess.check_output(['tail', '-1', output_file])
                res = regex.findall(last_line)
                if len(res) > 0:
                    self.t = float(res[0])
        os.chdir(orig_dir)
        return self.t

    def sim_get_status(self):
        """
        Get the current status of the simulation. Update the config file if necessary.

        :return: A dict containing the information of the current simulation status.
        """
        if self.config is None:
            return None
        orig_dir = os.getcwd()
        os.chdir(self.full_dir)
        self.t = self.sim_get_model_time()
        if self.config.has_option('Simulation', 'Output_file'):
            output_file = self.config.get('Simulation', 'Output_file')
            if os.path.isfile(output_file):
                self.mtime = os.stat(output_file).st_mtime
        if self.config.has_option('Simulation', 'Timestamp_started'):
            self.ctime = self.config.getfloat('Simulation', 'Timestamp_started')
        if self.config.has_option('Simulation', 'PID'):
            pid = self.config.getint('Simulation', 'PID')
            if pid == 0 and self.mtime == 0:
                self.status = SimulationTask.STATUS_NEW
            else:
                strpid = str(pid)
                try:
                    os.kill(pid, 0)
                    # it is running. Check if stalled.
                    stall_time = 300.0  # after 300s if the code doesn't advance, it is considered stalled
                    if self.config.has_option('Simulation', 'Stall_time'):
                        stall_time = self.config.getfloat('Simulation', 'Stall_time')
                    if time.time() - self.mtime > stall_time:
                        self.status = SimulationTask.STATUS_STALL
                    else:
                        self.status = SimulationTask.STATUS_RUN
                except (OSError, ValueError), e:
                    # The process is not running, check if stopped or done
                    if self.t >= self.t_max:
                        self.status = SimulationTask.STATUS_DONE
                    else:
                        if self.ctime == 0.0:
                            self.status = SimulationTask.STATUS_NEW
                        else:
                            self.status = SimulationTask.STATUS_STOP
        return self.status

    def sim_kill(self):
        """
        Forcibly kill (i.e. terminate) the current simulation. Practically, this method terminates the process of
        the simulation code and sets the simulation status to STOP.

        :return: Return 0 if succeed, -1 if failed. If the simulation is not running, then it cannot be killed, causing
        the method to do nothing but return 1.
        """
        # Find the process by PID
        if self.config.has_option('Simulation', 'PID'):
            pid = self.config.getint('Simulation', 'PID')
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError, err:
                print('Cannot kill the process: \n' + str(err))
        return 0

    def sim_stop(self):
        """
        Submit a request to the simulation code, in attempt to stop the simulation before it finishes the originally
        planned time checkpoint. This method will ask the code to stop the simulation by itself (if supported), rather
        than forcibly killing the simulation process.

        :return: Return 0 if succeed, -1 if failed. If the simulation is not running, then it cannot be stopped, causing
        the method to do nothing but return 1.
        """
        # Create an empty file called 'STOP'. The integrator that detects this file will (hopefully) stop the
        # integration.
        stop_file = open(os.path.join(self.full_dir, 'STOP'), 'w')
        stop_file.close()
        print('A stop request has been sent to simulation %s' % self.name)
        return 0

    def sim_backup_checkpoint(self):
        """
        Back up a snapshot of the latest restart files or simulation snapshot. In case of code crash, the backup files
        can be used for restarting.

        :return: Return 0 if succeed, -1 if failed. If the existing simulation snapshot is already the latest version,
        backup is not necessary, causing the method to do nothing but return 1.
        """
        # Try to get the restartable checkpoint file name from the config file
        if self.config.has_option('Simulation', 'Restart_file'):
            restart_fn = self.config.get('Simulation', 'Restart_file')
            ts = time.time()  # get the timestamp as part of the backup restart file name
            backup_restart_fn = 'restart.tmp.%d' % int(ts)
            if os.path.isfile(os.path.join(self.full_dir, restart_fn)):
                shutil.copyfile(os.path.join(self.full_dir, restart_fn), os.path.join(self.full_dir, backup_restart_fn))
                sys.stdout.write('Restart file has been backup as ' + backup_restart_fn + '\n')

                # delete the oldest backup if there is a limit of maximum number of backup files
                backup_file_list = sorted(glob.glob(os.path.join(self.full_dir, 'restart.tmp.*')))
                if 0 < self.maximum_number_of_checkpoints < len(backup_file_list):
                    for backup_restart_del_fn in backup_file_list[:-abs(self.maximum_number_of_checkpoints)]:
                        os.remove(os.path.join(self.full_dir, backup_restart_del_fn))
        else:
            # Without knowing the name of the restartable snapshot, SiMon will not be able to backup
            return -1
        return 0

    def sim_delete(self):
        """
        Delete the simulation data (including restarted simulation data).

        :return: Return 0 if succeed, -1 if failed. A simulation cannot be deleted if it is currently running. In this
        case, this method does nothing but just return 1.
        """
        if self.mode == 'interactive':
            confirm = raw_input('Are you sure you would like to delete the instance '
                                '#%d and its sub-instances? [Y/N] ' % self.id).lower()
            if confirm != 'y':
                return 1
        else:
            # TODO: code will not goes here because no functions in daemon mode will call inst_delete
            shutil.rmtree(self.full_dir)
            return 0
        return 0

    def sim_shell_exec(self, shell_command=None):
        """
        Execute a shell command under the data directory of the simulation.

        :param shell_command: the shell command to execute

        :return: Return 0 if succeed, -1 if failed.
        """
        if shell_command is None:
            shell_command = raw_input('CMD>> ')
        sys.stdout.write('========== Command on #%d ==> %s (PWD=%s) ==========\n'
                         % (self.id, self.full_dir, self.full_dir))
        original_dir = os.getcwd()
        os.chdir(self.full_dir)
        os.system(shell_command)
        sys.stdout.write('========== [DONE] Command on #%d ==> %s (PWD=%s) ==========\n'
                         % (self.id, self.full_dir, self.full_dir))
        os.chdir(original_dir)
        return 0

    def sim_clean(self):
        """
        Clean-up the simulation directory. Leaving only input files and restart file there.

        :return: Return 0 if succeed, -1 if failed. If the simulation is running, clean cannot be performed. In such
        case, the method does nothing but returns 1.
        """
        return 0

    def sim_reset(self):
        """
        Clean-up the simulation directory. Leaving only input files in the simulation directory. Reset the current
        Simulation status to NOT STARTED.

        :return: Return 0 if succeed, -1 if failed.
        """
        return 0

    def sim_init(self):
        """
        Perform necessary initialization procedures in order to start the simulation. Note that this method will NOT
        start the simulation. It will only make the simulation ready to start when sim_start() is called.

        :return: Return 0 if succeed, -1 if failed. If the simulation is running/stopped/finished, the method does
        nothing but just return 1.
        """
        return 0

    def sim_finalize(self):
        """
        Finalize the simulation (e.g. perform data processing) after the simulation is finished.

        :return: Return 0 if succeed, -1 if failed. If the simulation is running/stopped or not yet started, the method
        does nothing but return 1.
        """
        return 0

    def sim_collect_recent_output_message(self, lines=20):
        """
        Collect the recent lines of output/error messages, generated by the simulation code.

        :return: Return the messages as a combined string if available. Otherwise return an empty string.
        """
        if self.config.has_option('Simulation', 'Output_file'):
            output_file = self.config.get('Simulation', 'Output_file')
            sys.stdout.write('========== Diagnose for #%d ==> %s ==========\n' % (self.id, self.full_dir))
            check_dir_name = self.full_dir
            original_dir = os.getcwd()
            os.chdir(check_dir_name)
            os.system('\ntail -%d %s' % (lines, output_file))
            restart_dir = sorted(glob.glob('restart*/'))
            for r_dir in restart_dir:
                os.chdir(r_dir)
                sys.stdout.write('========== Diagnose for restart ==> %s ==========\n' % r_dir)
                os.system('\ntail -%d %s' % (lines, output_file))
                os.chdir('..')
            os.chdir(original_dir)
        return str()
