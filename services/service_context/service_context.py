import multiprocessing
from multiprocessing import Queue
from config import config_reader as crm
from entities import constellation as cm
from services.update_topology_service import update_topology_service as utsm
from services.position_calculate_service import position_calculate_service as pcsm


class ServiceContext:
    def start_service_context(self, constellation: cm.Constellation):
        self.update_topology_service = utsm.UpdateTopologyService(config_reader=self.config_reader,
                                                                  links=constellation.satellite_links_without_direction,
                                                                  stop_queue=self.stop_queue)
        self.position_calculate_service = pcsm.PositionCalculateService(
            ground_stations=constellation.ground_stations,
            config_reader=self.config_reader,
            links=constellation.satellite_links_without_direction,
            satellites=constellation.satellites,
            stop_queue=self.stop_queue)
        multiprocessing.Process(target=self.update_topology_service.start, args=()).start()
        multiprocessing.Process(target=self.position_calculate_service.start, args=()).start()

    def __init__(self, config_reader: crm.ConfigReader):
        self.stop_queue = Queue(maxsize=1)
        self.config_reader = config_reader
        self.update_topology_service = None
        self.position_calculate_service = None

    def quit_service_context(self):
        self.stop_queue.put("stop")
