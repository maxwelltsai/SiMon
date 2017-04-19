from module_common import SimulationTask
import re
import os
import subprocess
import time
import glob

__simulation__ = 'DemoSimulation'


class DemoSimulation(SimulationTask):

    def __init__(self, sim_id, name, full_dir, status, mode='daemon', t_min=0, t_max=0, restarts=None, logger=None):
        super(DemoSimulation, self).__init__(sim_id, name, full_dir, status, mode, t_min, t_max, restarts, logger)

    def sim_get_model_time(self):
        super(DemoSimulation, self).sim_get_model_time()
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

