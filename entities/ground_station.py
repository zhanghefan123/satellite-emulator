import math
from config import config_reader as crm
from entities import entity as em
from const_vars import const_vars as cvm


class GroundStation(em.Entity):
    def __init__(self, node_id, name: str, longitude: float, latitude: float, entity_type: em.EntityType):
        """
        进行 ground station 的初始化
        :param node_id 地面站的 id 索引
        :param longitude: 地面站的经度
        :param latitude:  地面站的纬度
        """
        super().__init__(entity_type)
        self.node_id = node_id
        self.name = name  # 地面站的名称
        self.latitude = latitude  # 地面站的纬度
        self.longitude = longitude  # 地面站的经度
        self.latitude_in_radian = latitude / 180 * math.pi  # 地面站的纬度/弧度
        self.longitude_in_radian = longitude / 180 * math.pi  # 地面站的经度/弧度
        self.initial_connect_satellite_id = None  # 最早连接到的卫星
        self.current_connect_satellite_id = None  # 当前连接到的卫星
        self.position = (0, self.longitude_in_radian, self.latitude_in_radian)
        self.initial_connected = True
        self.gsl_interface_index_map = {"gsl1": False,  # 总共存在4个可用的接口
                                        "gsl2": False,
                                        "gsl3": False,
                                        "gsl4": False}

    @staticmethod
    def load_ground_stations_from_config_reader(config_reader: crm.ConfigReader):
        """
        从 config_reader 之中加载地面站列表
        :param config_reader: 配置对象
        :return: 地面站的列表
        """
        ground_station_list = []
        for index, single_ground_station_str in enumerate(config_reader.ground_infos):
            ground_station_name, longitude_str, latitude_str = single_ground_station_str.split("|")
            longitude = float(longitude_str)
            latitude = float(latitude_str)
            ground_station = GroundStation(node_id=index,
                                           name=ground_station_name,
                                           longitude=longitude,
                                           latitude=latitude,
                                           entity_type=em.EntityType.GROUND_STATION)
            ground_station.container_name = f"{cvm.GROUND_STATION_PREFIX}{index}"
            ground_station_list.append(ground_station)
        return ground_station_list
