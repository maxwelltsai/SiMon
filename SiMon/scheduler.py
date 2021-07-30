"""
Abstract base class for simulation scheduling algorithms. 
"""

from abc import ABC
from logging import Logger

from SiMon.simulation import Simulation 
from SiMon.simulation_container import SimulationContainer

class Scheduler(ABC):

    def __init__(self, container: SimulationContainer = None, logger: Logger = None, config: dict = None) -> None:
        super().__init__()
        self.container = container
        self.logger = logger 
        self.config = config 

    def schedule(self):
        pass 