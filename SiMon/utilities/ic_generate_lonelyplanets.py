"""
Generate initial conditions and populate simulation data directory structure.

"""

import os
import h5py

sim_root_dir = '/home/maxwell/Works/lonelyplanets_simulations/ems/1k/sim'
config_file_name = 'SiMon.conf'
output_file_name = 'output.txt'
output_dir = 'p_sys_%d'
error_file_name = 'error.txt'
sim_start_command = \
    'python -u /home/maxwell/Works/lonelyplanets_simulations/ems/1k/lps.py -p %d 1>output.txt 2>error.txt'
sim_restart_command = \
    'python -u /home/maxwell/Works/lonelyplanets_simulations/ems/1k/lps.py -p %d 1>output.txt 2>error.txt'
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

host_stars = []
# Read HDF5 file to obtain a list of host star IDs
if os.path.isfile('/home/maxwell/Works/lonelyplanets_simulations/ems/1k/planetary_systems.h5ic'):
    print 'planetary_elem file found'
    h5_f = h5py.File('/home/maxwell/Works/lonelyplanets_simulations/ems/1k/planetary_systems.h5ic', 'r')
    n_p_sys = len(h5_f)
    print '%d planetary systems found' % n_p_sys
    h5_f.close()
else:
    print 'planetary_elem file not exists! Cannot obtain a list of host star ids.'
host_stars = range(n_p_sys)

for hs in host_stars:
    # create directory
    sim_dir = output_dir % (hs)
    if not os.path.isdir(os.path.join(sim_root_dir, sim_dir)):
	print sim_dir
	os.mkdir(os.path.join(sim_root_dir, sim_dir))
    # create config file
    conf_file = open(os.path.join(sim_root_dir, sim_dir, config_file_name), 'w')
    sim_start_cmd = sim_start_command % (hs)
    sim_restart_cmd = sim_restart_command % (hs)
    conf_file.write(config_file_template % ('LonelyPlanets',
					    '',
					    output_file_name,
					    error_file_name,
					    0,
					    0,
					    50000000.0,
					    sim_start_cmd,
					    sim_restart_cmd,
					    sim_stop_command))
    conf_file.close()

