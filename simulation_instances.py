"""
Traverse the directory structure:
A hierarchical directory structure may form for a simulation that has been started for multiple times.
For instance, a simulation is running on the directory '/sim1'. It crashes at T=120. So SiMon
restarts it by creating a restart directory '/sim1/restart1'. 'restart1' runs until T=200, and then
again crashes. So SiMon creates '/sim1/restart1/restart1' in attempt to start from T=200.

"""

import datetime


class SimulationInstance(object):
    """
    A simulation instance is a single simulation task which the user requests to finish.
    It is associated with 1) a set of initial conditions specified in the input file,
    2) a (bash) script to start up the code, 3) the status of the simulation (RUN/STOP/model time,
    start timestamp, last output timestamp, parent simulation ID if it is a restart, etc),
    and 4) the ending time of the simulation.

    Parameters
    ----------
    name : string
        Usually the name of the simulation directory.
    fulldir : string
        The full path of the simulation directory.
    status : string
        RUN, STOP, RESTARTED
    """

    def __init__(self, id, name, fulldir, status, t_min = 0, t_max = 0, restarts = None):
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
                placeholder_space, self.status, self.t_min, self.t_max, self.errortype,self.cid,self.level)
        ret = "%d%s%s\n" % (self.id, placeholder_dash, info)
        #ret = "    "*level+str(self.id)+repr(self.name)+"\n"
        for child in self.restarts:
            ret += child.__repr__(level+1)
        return ret

