from logging import Logger
from SiMon.scheduler import Scheduler
from SiMon.simulation import Simulation
from SiMon.simulation_container import SimulationContainer
from SiMon import config 
import os 
import numpy as np 


class PriorityScheduler(Scheduler):

    def __init__(self, container: SimulationContainer = None, logger: Logger = None, config: dict = None, callbacks: list = None ) -> None:
        super().__init__(container, logger, config, callbacks)
    
    def schedule(self):
        """
        Schedule the simulations based on their priorities.
        """
        super().schedule()

        self.container.build_simulation_tree()
        schedule_list = []
        # Sort jobs according to priority (niceness)
        sim_niceness_vec = []
        sim_id_vec = []

        # check how many simulations are running
        concurrent_jobs = 0
        for i in self.container.sim_inst_dict.keys():
            inst = self.container.sim_inst_dict[i]
            sim_niceness_vec.append(inst.niceness)
            sim_id_vec.append(inst.id)
            inst.sim_get_status()  # update its status
            # test if the process is running
            if inst.status == Simulation.STATUS_RUN and inst.cid == -1:
                concurrent_jobs += 1

        index_niceness_sorted = np.argsort(sim_niceness_vec)
        for _, i in enumerate(index_niceness_sorted):
            ind = sim_id_vec[i]
            if (
                self.container.sim_inst_dict[ind].status != Simulation.STATUS_DONE
                and self.container.sim_inst_dict[ind].id > 0
            ):
                schedule_list.append(self.container.sim_inst_dict[ind])

        for sim in schedule_list:
            if sim.id == 0:  # the root group, skip
                continue
            sim.sim_get_status()  # update its status
            self.logger.debug("Checking instance #%d ==> %s [%s]" % (sim.id, sim.name, sim.status))
            if sim.status == Simulation.STATUS_RUN:
                sim.sim_backup_checkpoint()
            elif sim.status == Simulation.STATUS_STALL:
                sim.sim_kill()
                self.container.build_simulation_tree()
            elif sim.status == Simulation.STATUS_STOP and sim.level == 1:
                self.logger.warning("STOP detected: " + sim.fulldir)
                # check if there is available slot to restart the simulation
                if concurrent_jobs < int(self.config['Max_concurrent_jobs']) and sim.level == 1:
                    # search only top level instance to find the restart candidate
                    # build restart path
                    current_inst = sim
                    # restart the simulation instance at the leaf node
                    while current_inst.cid != -1:
                        current_inst = self.container.sim_inst_dict[current_inst.cid]
                    print(
                        "RESTART: #%d ==> %s" % (current_inst.id, current_inst.fulldir)
                    )
                    self.logger.info(
                        "RESTART: #%d ==> %s" % (current_inst.id, current_inst.fulldir)
                    )
                    current_inst.sim_restart()
                    concurrent_jobs += 1
            elif sim.status == Simulation.STATUS_NEW:
                # check if there is available slot to start the simulation
                if concurrent_jobs < int(self.config['Max_concurrent_jobs']):
                    # Start new run
                    sim.sim_start()
                    concurrent_jobs += 1
        self.logger.info(
            "SiMon routine checking completed. Machine load: %d/%d"
            % (concurrent_jobs, int(self.config['Max_concurrent_jobs']))
        )