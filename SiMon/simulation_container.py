"""

A container for simulations.

"""
import os 
from fnmatch import fnmatch
import configparser as cp 
from SiMon.simulation import Simulation
from SiMon import utilities


class SimulationContainer(object):

    def __init__(self, root_dir=None) -> None:

        # The root directory on the file system containing all simulation data
        if root_dir is not None:
            self.root_dir = root_dir
        else: 
            self.root_dir = os.getcwd()

        self.selected_inst = []  # A list of the IDs of selected simulation instances
        self.sim_inst_dict = dict() # the container of all Simulation objects (ID to object mapping)
        self.sim_inst_parent_dict = dict() # given the current path, find out the instance of the parent
        
        self.sim_tree = Simulation(0, "root", root_dir, Simulation.STATUS_NEW)
        self.module_dict = utilities.register_simon_modules(module_dir=utilities.get_simon_dir(), user_shell_dir=os.getcwd())
        
    def traverse_simulation_dir_tree(self, pattern, base_dir, files):
        """
        Traverse the simulation file structure tree (Breadth-first search), until the leaf (i.e. no restart directory)
        or the simulation is not restartable (directory with the 'STOP' file).
        """
        for filename in sorted(files):
            if fnmatch(filename, pattern):
                if os.path.isdir(os.path.join(base_dir, filename)):
                    fullpath = os.path.join(base_dir, filename)
                    self.inst_id += 1
                    id = self.inst_id

                    # Try to determine the simulation code type by reading the config file
                    sim_config = utilities.parse_config_file(
                        os.path.join(fullpath, "SiMon.conf"),
                        section='Simulation'
                    )
                    sim_inst = None
                    if sim_config is not None:
                        try:
                            code_name = sim_config["Code_name"]
                            if code_name in self.module_dict:
                                sim_inst_mod = __import__(self.module_dict[code_name])
                                sim_inst = getattr(sim_inst_mod, code_name)(
                                    id,
                                    filename,
                                    fullpath,
                                    Simulation.STATUS_NEW,
                                    logger=utilities.get_logger(),
                                )
                        except (cp.NoOptionError, cp.NoSectionError):
                            pass
                    else:
                        continue
                    if sim_inst is None:
                        continue
                    self.sim_inst_dict[id] = sim_inst
                    sim_inst.id = id
                    sim_inst.fulldir = fullpath
                    sim_inst.name = filename

                    # register child to the parent
                    self.sim_inst_parent_dict[base_dir].restarts.append(sim_inst)
                    sim_inst.level = self.sim_inst_parent_dict[base_dir].level + 1
                    # register the node itself in the parent tree
                    self.sim_inst_parent_dict[fullpath] = sim_inst
                    sim_inst.parent_id = self.sim_inst_parent_dict[base_dir].id

                    # Get simulation status
                    sim_inst.sim_get_status()

                    self.sim_inst_dict[sim_inst.parent_id].status = sim_inst.status

                    if (
                        sim_inst.t > self.sim_inst_dict[sim_inst.parent_id].t
                        and not os.path.isfile(os.path.join(sim_inst.fulldir, "ERROR"))
                    ) or sim_inst.status == Simulation.STATUS_RUN:
                        # nominate as restart candidate
                        self.sim_inst_dict[sim_inst.parent_id].cid = sim_inst.id
                        self.sim_inst_dict[
                            sim_inst.parent_id
                        ].t_max_extended = sim_inst.t_max_extended

    def build_simulation_tree(self):
        """
        Generate the simulation tree data structure, so that a restarted simulation can trace back
        to its ancestor.

        :return: The method has no return. The result is stored in self.sim_tree.
        :type: None
        """
        os.chdir(self.root_dir)
        self.sim_inst_dict = dict()

        self.sim_tree = Simulation(
            0, "root", self.root_dir, Simulation.STATUS_NEW
        )  # initially only the root node

        self.sim_inst_dict[0] = self.sim_tree  # map ID=0 to the root node
        self.sim_inst_parent_dict[
            self.root_dir.strip()
        ] = self.sim_tree  # map the current dir to be the sim tree root
        self.inst_id = 0

        for directory, dirnames, filenames in os.walk(self.root_dir):
            self.traverse_simulation_dir_tree("*", directory, dirnames)

        # Synchronize the status tree (status propagation)
        update_needed = True
        max_iter = 0
        while update_needed and max_iter < 30:
            max_iter += 1
            inst_status_modified = False
            for i in self.sim_inst_dict:
                if i == 0:
                    continue
                inst = self.sim_inst_dict[i]
                if (
                    inst.status == Simulation.STATUS_RUN
                    or inst.status == Simulation.STATUS_DONE
                ):
                    if (
                        inst.parent_id > 0
                        and self.sim_inst_dict[inst.parent_id].status != inst.status
                    ):
                        # propagate the status of children (restarted simulation) to parents' status
                        self.sim_inst_dict[inst.parent_id].status = inst.status
                        inst_status_modified = True
            if inst_status_modified is True:
                update_needed = True
            else:
                update_needed = False
        return 0
        print(self.sim_tree)

    def __repr__(self, level=0):
        """
        Output an overview of the simulation status in the terminal.

        :return: start and stop time
        :rtype: int
        """
        self.build_simulation_tree()
        # print(
            # self.sim_tree
        # )  # print the root node will cause the whole tree to be printed
        return self.sim_tree.__repr__()

    def get_simulation_by_id(self, sid):
        if sid in self.sim_inst_dict:
            return self.sim_inst_dict[sid]
        else:
            return None 