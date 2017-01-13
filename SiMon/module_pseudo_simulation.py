from simulation_task import SimulationTask
import re
import os
import subprocess
import time

__simulation__ = 'PseudoSimulation'


class PseudoSimulation(SimulationTask):

    def __init__(self, sim_id, name, full_dir, status, mode='daemon', t_min=0, t_max=0, restarts=None):
        super(PseudoSimulation, self).__init__(sim_id, name, full_dir, status, mode, t_min, t_max, restarts)

    def sim_get_status(self):
        super(PseudoSimulation, self).sim_get_status()
        orig_dir = os.getcwd()
        os.chdir(self.full_dir)
        if self.config.has_option('Simulation', 'Output_file'):
            output_file = self.config.get('Simulation', 'Output_file')
            regex = re.compile('\\d+')
            if os.path.isfile(output_file):
                last_line = subprocess.check_output(['tail', '-1', output_file])
                res = regex.findall(last_line)
                try:
                    if len(res) > 0:
                        self.t = float(res[0])
                        if self.t >= self.t_max:
                            self.status = 'DONE'
                        hang_time = 60  # after 120s if the code doesn't advance, it is considered hang
                        if self.config.has_option('Simulation', 'Hang_time'):
                            hang_time = self.config.getfloat('Simulation', 'Hang_time')
                        if time.time() - self.mtime > hang_time:
                            self.status = 'HANG'
                            # update the dt in the config file
                            if self.config.has_option('Simulation', 'dt'):
                                dt = self.config.getfloat('Simulation', 'dt')
                                self.config.set('Simulation', 'dt', str(dt/2))
                                self.config.write(open(self.config_file, 'w'))
                                print('WARNING: HANG detected in instance %s. Reducing dt by half.' % self.name)
                except ValueError:
                    pass
        os.chdir(orig_dir)
        return dict()
