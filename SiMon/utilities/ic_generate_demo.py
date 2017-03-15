"""
Generate initial conditions and populate simulation data directory structure.

"""

import os

sim_root_dir = '/Users/penny/Works/simon_project/test_code'
config_file_name = 'SiMon.conf'
output_file_name = 'output.txt'
output_dir = 'demo_sim_t_end=%g_a=%g_e=%g'
error_file_name = 'error.txt'
sim_start_command = \
    'python -u /Users/penny/Works/simon_project/SiMon/SiMon/utilities/demo_simulation_code.py -a %f -o %f -t %f 2>error.txt'
sim_restart_command = \
    'python -u /Users/penny/Works/simon_project/SiMon/SiMon/utilities/demo_simulation_code.py -a %f -o %f -t %f 2>error.txt'
sim_stop_command = 'touch STOP'

config_file_template = '''[Simulation]
# The name of the simulation code
Code_name = %s

# The file name of the initial condition input file (for stdin)
Input_file = %s

# The file name of the simulation log output (for stdout)
Output_file = %s

# The file name of the simulation error output (for stderr)
Error_file = %s

# The timestamp indicating the starting time of the simulation
Timestamp_started = %s

# The timestamp indicating the last time output files are updated
Timestamp_last_updated = %s

# The termination time (i.e., t_max)
T_end = %s

# The process ID of the N-body code
PID = 0

# The priority (i.e. niceness) of the simulation (-20 to 19, lower are higher, same as UNIX systems)
Niceness = 0

# The shell command to start the simulation
Start_command: %s

# The shall command to restart the simulation
Restart_command: %s

# The shall command to stop the simulation
Stop_command: %s
'''

a_vec = [1.0, 2.0, 3.0]
o_vec = [3.5, 7.5, 10.5, 16.5]
t_end = 30.0

for a in a_vec:
    for o in o_vec:
        # create directory
        sim_dir = output_dir % (a, o, t_end)
        if not os.path.isdir(os.path.join(sim_root_dir, sim_dir)):
            print sim_dir
            os.mkdir(os.path.join(sim_root_dir, sim_dir))
        # create config file
        conf_file = open(os.path.join(sim_root_dir, sim_dir, config_file_name), 'w')
        sim_start_cmd = sim_start_command % (a, o, t_end)
        sim_restart_cmd = sim_restart_command % (a, o, t_end)
        conf_file.write(config_file_template % ('DemoSimulation',
                                                '',
                                                output_file_name,
                                                error_file_name,
                                                0,
                                                0,
                                                t_end,
                                                sim_start_cmd,
                                                sim_restart_cmd,
                                                sim_stop_command))
        conf_file.close()

