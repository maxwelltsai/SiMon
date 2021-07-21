"""
Abstract base class for simulation scheduling algorithms. 
"""

from abc import ABC

from SiMon.simulation import Simulation 
from SiMon.simulation_container import SimulationContainer

class Scheduler(ABC):

    def __init__(self, container: SimulationContainer = None) -> None:
        super().__init__()
        self.container = container

    def schedule(self):
        pass 