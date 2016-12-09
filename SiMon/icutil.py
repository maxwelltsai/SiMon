"""
Generate initial conditions and populate simulation data directory structure.

"""

import os

sim_root_dir = '/Volumes/RamDisk/sim'
config_file_name = 'SiMon.conf'
output_file_name = 'output.txt'
output_dir = 'sun_pc_a_c=%g-i_c=%g-k_c=%g-k_p=%g-tau_c=%g-tau_p=%g'
error_file_name = 'error.txt'
sim_start_command = \
    '/Users/maxwell/Works/amuse/amuse.sh /Users/maxwell/Works/pluto_charon_secularmultiple/sun_pc_param.py --a_c=%f --i_c=%f --k_c=%f --k_p=%f --tau_c=%f --tau_p=%f --t_end=%f --dt=%f 1>output.txt 2>error.txt'
sim_restart_command = \
    '/Users/maxwell/Works/amuse/amuse.sh /Users/maxwell/Works/pluto_charon_secularmultiple/sun_pc_param.py --a_c=%f --i_c=%f --k_c=%f --k_p=%f --tau_c=%f --tau_p=%f --t_end=%f --dt=%f 1>output.txt 2>error.txt'
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

a_c_vec = [1.7e4]
i_c_vec = [110.0]
# k_c_vec = [4.e-1, 4.e-2, 4.e-3, 4.e-4, 4.e-5]
# k_p_vec = [4.e-1, 4.e-2, 4.e-3, 4.e-4, 4.e-5]
k_c_vec = [4.e-1]
k_p_vec = [4.e-1]
tau_c_vec = [6.e1, 6.e2, 6.e3]
tau_p_vec = [6.e1, 6.e2, 6.e3]
t_end = 10.0
dt = 1.e-2

for a_c in a_c_vec:
    for i_c in i_c_vec:
        for k_c in k_c_vec:
            for k_p in k_p_vec:
                for tau_c in tau_c_vec:
                    for tau_p in tau_p_vec:
                        # create directory
                        sim_dir = output_dir % (a_c, i_c, k_c, k_p, tau_c, tau_p)
                        if not os.path.isdir(os.path.join(sim_root_dir, sim_dir)):
                            print sim_dir
                            os.mkdir(os.path.join(sim_root_dir, sim_dir))
                        # create config file
                        conf_file = open(os.path.join(sim_root_dir, sim_dir, config_file_name), 'w')
                        sim_start_cmd = sim_start_command % (a_c, i_c, k_c, k_p, tau_c, tau_p, t_end, dt)
                        sim_restart_cmd = sim_restart_command % (a_c, i_c, k_c, k_p, tau_c, tau_p, t_end, dt)
                        conf_file.write(config_file_template % ('SecularMultiple',
                                                                '',
                                                                output_file_name,
                                                                error_file_name,
                                                                0,
                                                                0,
                                                                10.0,
                                                                sim_start_cmd,
                                                                sim_restart_cmd,
                                                                sim_stop_command))
                        conf_file.close()

