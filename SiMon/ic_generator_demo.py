import os
import numpy as np
from SiMon.ic_generator import InitialConditionGenerator


def generate_ic(output_basedir=os.getcwd()):
    # parameter space
    a_vec = [1.0, 2.0, 3.0]
    o_vec = [3.5, 7.5, 10.5, 16.5]
    t_end = 30.0

    # templates
    code_name = 'DemoSimulation'
    executable_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo_simulation_code.py')
    start_cmd_template = 'python -u %s -a %f -o %f -t %f -p %f 1>%s 2>%s'
    restart_cmd_template = 'cp ../%s . ; python -u %s -a %f -o %f -t %f -p %f 1>%s 2>%s'
    stop_cmd = 'touch STOP'
    output_dir_template = 'demo_sim_t_end=%g_a=%g_e=%g'

    # IC generator
    ic = InitialConditionGenerator(conf_file='SiMon.conf')
    ic.parse_config_file()

    # generate the IC parameter space in the loops
    for a in a_vec:
        for o in o_vec:
            p_crash = 0.01 * np.random.rand()
            start_cmd = start_cmd_template % (executable_path, a, o, t_end, p_crash, 'output.txt', 'error.txt')
            restart_cmd = restart_cmd_template % ('restart.txt', executable_path, a, o, t_end, p_crash, 'output.txt', 'error.txt')
            output_dir = output_dir_template % (t_end, a, o)
            ic.generate_simulation_ic(code_name, t_end, output_dir, start_cmd,
                                      input_file='input.txt', output_file='output.txt', error_file='error.txt',
                                      restart_cmd=restart_cmd, stop_cmd=stop_cmd)

if __name__ == "__main__":
    generate_ic()
