"""
Initial condition (IC) generator.
"""
import os
import sys
try:
    import configparser as cp  # Python 3 only
except ImportError:
    import ConfigParser as cp  # Python 2 only


class InitialConditionGenerator(object):

    config_file_template = '''# Per-simulation config file for SiMon
[Simulation]
# The name of the simulation code
Code_name = %s

# The file name of the initial condition input file (for stdin)
Input_file = %s

# The file name of the simulation log output (for stdout)
Output_file = %s

# The file name of the simulation error output (for stderr)
Error_file = %s

# The name of the file used to restart the simulation
Restart_file = %s

# The timestamp indicating the starting time of the simulation
Timestamp_started = %s

# The timestamp indicating the last time output files are updated
Timestamp_last_updated = %s

# The time (in second) beyond which a simulation is considered as stalled
Stall_time = %d

# The starting time
T_start = %f

# The termination time (i.e., t_max)
T_end = %f

# The process ID of the N-body code
PID = %d

# The priority (i.e. niceness) of the simulation (-20 to 19, lower are higher, same as UNIX systems)
Niceness = %d

# The shell command to start the simulation
Start_command: %s

# The shall command to restart the simulation
Restart_command: %s

# The shall command to stop the simulation
Stop_command: %s

# The maximum number of times a simulation will be restarted (a simulation is marked as ERROR when exceeding this limit)
Max_restarts: %d
    '''

    def __init__(self, conf_file):
        self.global_conf_file = conf_file  # the path of the global SiMon.conf
        self.config_file_per_sim = 'SiMon.conf'  # the per-simulation config file name
        self.config = None  # the parsed global config instance
        self.sim_data_dir = None  # simulation data dir
        self.max_restarts = 5  # maximum attempts a sim will be restarted, beyond which a sim is considered error
        self.stall_time = 6.e6  # Stall time

    def parse_config_file(self):
        print(self.global_conf_file)
        conf_fn = self.global_conf_file
        conf = cp.ConfigParser()
        if os.path.isfile(conf_fn):
            conf.read(conf_fn)
            self.config = conf
            if self.config.has_option('SiMon', 'Root_dir'):
                self.sim_data_dir = self.config.get('SiMon', 'Root_dir')
                # check whether the directory exist
                if not os.path.isdir(self.sim_data_dir):
                    print('Simulation data directory %s does not exist. Making the dir...' % self.sim_data_dir)
                    try:
                        os.makedirs(self.sim_data_dir)
                        print('Simulation data directory created successfully.')
                    except IOError as err:
                        print('Unable to create the simulation data directory: %s' % err)
                        print('Exiting...')
                        sys.exit(-1)
            else:
                print('Simulation root directory cannot be found in SiMon.conf. Existing...')
                sys.exit(-1)
            if self.config.has_option('SiMon', 'Max_restarts'):
                self.max_restarts = self.config.getint('SiMon', 'Max_restarts')
            if self.config.has_option('SiMon', 'Stall_time'):
                self.stall_time = self.config.getfloat('SiMon', 'Stall_time')

        else:
            print('Global config file %s cannot be found. Existing...' % self.global_conf_file)
            sys.exit(-1)

    def generate_simulation_ic(self, code_name, t_end, output_dir, start_cmd, input_file=None, output_file=None,
                               error_file=None, restart_file=None, t_stall=None, t_start=0, restart_cmd=None,
                               stop_cmd=None, niceness=0, max_restarts=None):
        """
        Generate the initial condition of a simulation and write it to the given directory.
        :param code_name: The name of the numerical code, e.g. DemoSimulation
        :param t_end: The termination time criterion
        :param output_dir: The directory in which the initial condition files and output files are contained
        :param start_cmd: The UNIX command to start the simulation
        :param input_file: The name of the input file (optional)
        :param output_file: The name of the output file (optional)
        :param error_file: The name of the error message file (optional)
        :param restart_file: The name of the restartable checkpoint file (optional)
        :param t_stall: How long (in sec) will a simulation be considered stalled since the last time the output file
                        is updated
        :param t_start: The starting model time (optional, default: 0)
        :param restart_cmd: The UNIX command to restart the simulation
        :param stop_cmd: The UNIX command to request the simulation code to stop the simulation (optional)
        :param niceness: The priority of the simulation, -20 to 19, lower are higher (optional, default: 0)
        :param max_restarts: The maximum number of attempts a simulation will be restarted, beyond which the simulation
                             is considered ERROR
        :return: return 0 if succeed, -1 if failed.
        """
        if max_restarts is None:
            max_restarts = self.max_restarts
        if t_stall is None:
            t_stall = self.stall_time
        if not os.path.isdir(os.path.join(self.sim_data_dir, output_dir)):
            print('Creating directory: %s' % os.path.join(self.sim_data_dir, output_dir))
            os.makedirs(os.path.join(self.sim_data_dir, output_dir))
        conf_file = open(os.path.join(self.sim_data_dir, output_dir, self.config_file_per_sim), 'w')
        conf_file.write(InitialConditionGenerator.config_file_template % (code_name,
                                                                          input_file,
                                                                          output_file,
                                                                          error_file,
                                                                          restart_file,
                                                                          0,  # timestamp started
                                                                          0,  # timestamp last modified
                                                                          t_stall,
                                                                          t_start,
                                                                          t_end,
                                                                          0,  # UNIX process ID (PID)
                                                                          niceness,
                                                                          start_cmd,
                                                                          restart_cmd,
                                                                          stop_cmd,
                                                                          max_restarts))  # max_restarts
        conf_file.close()


