import datetime
import abc

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

    __metaclass__ = abc.ABCMeta

    def __init__(self, id, name, fulldir, status, t_min=0, t_max=0, restarts=None):
        """
        :param id:

        :param name: Usually the name of the simulation directory.
        :type name: basestring

        :param fulldir: The full path of the simulation directory.

        :param status: RUN, STOP, RESTARTED

        :param t_min: default as 0
        :param t_max: default as 0
        :param restarts: default as None
        :return:
        """
        self.id = id
        self.name = name
        self.fulldir = fulldir
        self.status = status
        self.errortype = ''
        self.t_min = t_min
        self.t_max = t_max
        self.t_max_extended = t_max # extended t_max by restarts
        self.mtime = 0
        self.ctime = 0
        self.cid = -1 # the candidate instance ID to restart in case crashes
                      # (-1: no candidate, restart from itself;)
                      # (>0: restart from the candidate. If the candidate cannot restart, try siblings)
        self.level = 0
        self.parent_id = -1
        if restarts == None:
            self.restarts = list()
        else:
            self.restarts = restarts # children

    def __repr__(self, level=0):
        """
        :param level: traverse level
        :return:
        """
        placeholder_dash = "|---"+'-'*(level*4)
        placeholder_space = "    "+' '*(level*4)
        ctime_str = datetime.datetime.fromtimestamp(self.ctime).strftime('%Y-%m-%d %H:%M:%S')
        mtime_str = datetime.datetime.fromtimestamp(self.mtime).strftime('%Y-%m-%d %H:%M:%S')
        info = "%s\t%s\t%s\n%s%s\tT=[%d-%d]\t%s\tCID=%d\tlevel=%d" % (repr(self.name), ctime_str, mtime_str,
                placeholder_space, self.status, self.t_min, self.t_max, self.errortype, self.cid, self.level)
        ret = "%d%s%s\n" % (self.id, placeholder_dash, info)
        #ret = "    "*level+str(self.id)+repr(self.name)+"\n"
        for child in self.restarts:
            ret += child.__repr__(level+1)
        return ret

    @abc.abstractmethod
    def sim_start(self):
        """
        Start a new simulation
        :return: Return 0 if succeed, -1 if failed. If the simulation is already started, then it will do nothing
        but return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_restart(self):
        """
        Restart the simulation.
        :return: Return 0 if succeed, -1 if failed. If the simulation is already running, then restart is not
        necessary, the method will do nothing but return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_get_status(self):
        """
        Get the current status of the simulation.
        :return: A dict containing the information of the current simulation status.
        """
        return dict()

    @abc.abstractmethod
    def sim_kill(self):
        """
        Forcibly kill (i.e. terminate) the current simulation. Practically, this method terminates the process of
        the simulation code and sets the simulation status to STOP.
        :return: Return 0 if succeed, -1 if failed. If the simulation is not running, then it cannot be killed, causing
        the method to do nothing but return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_stop(self):
        """
        Submit a request to the simulation code, in attempt to stop the simulation before it finishes the originally
        planned time checkpoint. This method will ask the code to stop the simulation by itself (if supported), rather
        than forcibly killing the simulation process.
        :return: Return 0 if succeed, -1 if failed. If the simulation is not running, then it cannot be stopped, causing
        the method to do nothing but return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_backup_checkpoint(self):
        """
        Back up a snapshot of the latest restart files or simulation snapshot. In case of code crash, the backup files
        can be used for restarting.
        :return: Return 0 if succeed, -1 if failed. If the existing simulation snapshot is already the latest version,
        backup is not necessary, causing the method to do nothing but return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_delete(self):
        """
        Delete the simulation data (including restarted simulation data).
        :return: Return 0 if succeed, -1 if failed. A simulation cannot be deleted if it is currently running. In this
        case, this method does nothing but just return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_shell_exec(self, shell_command):
        """
        Execute a shell command under the data directory of the simulation.
        :param shell_command: the shell command to execute
        :return: Return 0 if succeed, -1 if failed.
        """
        return 0

    @abc.abstractmethod
    def sim_clean(self):
        """
        Clean-up the simulation directory. Leaving only input files and restart file there.
        :return: Return 0 if succeed, -1 if failed. If the simulation is running, clean cannot be performed. In such
        case, the method does nothing but returns 1.
        """
        return 0

    @abc.abstractmethod
    def sim_reset(self):
        """
        Clean-up the simulation directory. Leaving only input files in the simulation directory. Reset the current
        Simulation status to NOT STARTED.
        :return: Return 0 if succeed, -1 if failed.
        """
        return 0

    @abc.abstractmethod
    def sim_init(self):
        """
        Perform necessary initialization procedures in order to start the simulation. Note that this method will NOT
        start the simulation. It will only make the simulation ready to start when sim_start() is called.
        :return: Return 0 if succeed, -1 if failed. If the simulation is running/stopped/finished, the method does
        nothing but just return 1.
        """
        return 0

    @abc.abstractmethod
    def sim_finalize(self):
        """
        Finalize the simulation (e.g. perform data processing) after the simulation is finished.
        :return: Return 0 if succeed, -1 if failed. If the simulation is running/stopped or not yet started, the method
        does nothing but return 1.
        """
        return 0