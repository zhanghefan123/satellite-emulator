import ephem
import math
import pika
import time
import json
from typing import List
from entities import satellite as sm
import datetime
from entities import normal_link as nlm
from const_vars import const_vars as cvm
from config import config_reader as crm
from multiprocessing import Queue
from entities import ground_station as gsm
from loguru import logger


class PositionCalculateService:
    def __init__(self, ground_stations: List[gsm.GroundStation],
                 satellites: List[sm.Satellite],
                 links: List[nlm.NormalLink],
                 config_reader: crm.ConfigReader,
                 stop_queue: Queue):
        self.inter_satellite_links = links
        self.ground_station_satellite_links = {}
        self.satellites = satellites
        self.config_reader = config_reader
        self.ground_stations = ground_stations
        self.continue_calc = True
        self.quit_msg = "quit"
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.config_reader.network_ip_address))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.config_reader.update_queue_name)
        self.isl_delay_map = {}  # 存储的是 {satellite_id <-> delay}
        self.gsl_connection_map = {item.node_id: None for item in self.satellites}  # 存储的是 {satellite_id <-> ground_id}
        self.stop_queue = stop_queue
        self.constellation_start_time = self.config_reader.constellation_start_time
        self.calculation_interval = self.config_reader.calculation_interval
        self.speed_rate = self.config_reader.speed_rate

    def calculate_satellites_position(self):
        # 对于每个卫星计算他的当前的位置
        # readtle 传入的第一个参数是卫星的名称 第二个参数是卫星的tle的第一行 第三个参数是卫星的tle的第二行
        ephem_time = ephem.Date(self.constellation_start_time)
        for satellite in self.satellites:
            ephem_obj = ephem.readtle(f"sat{satellite.node_id}", satellite.tle[0], satellite.tle[1])
            ephem_obj.compute(ephem_time)
            latitude = ephem_obj.sublat
            longitude = ephem_obj.sublong
            altitude = ephem_obj.elevation
            satellite.position = (altitude, longitude, latitude)

    @staticmethod
    def calculate_two_nodes_distance(source_position, dest_position):
        """
        计算两点间距离
        :return: 两点间的距离
        """
        # 计算两者之间的距离
        z1 = (source_position[cvm.ALTITUDE_KEY] + cvm.R_EARTH) * math.sin(source_position[cvm.LATITUDE_KEY])
        base1 = (source_position[cvm.ALTITUDE_KEY] + cvm.R_EARTH) * math.cos(source_position[cvm.LATITUDE_KEY])
        x1 = base1 * math.cos(source_position[cvm.LONGITUDE_KEY])
        y1 = base1 * math.sin(source_position[cvm.LONGITUDE_KEY])
        z2 = (dest_position[cvm.ALTITUDE_KEY] + cvm.R_EARTH) * math.sin(dest_position[cvm.LATITUDE_KEY])
        base2 = (dest_position[cvm.ALTITUDE_KEY] + cvm.R_EARTH) * math.cos(dest_position[cvm.LATITUDE_KEY])
        x2 = base2 * math.cos(dest_position[cvm.LONGITUDE_KEY])
        y2 = base2 * math.sin(dest_position[cvm.LONGITUDE_KEY])
        distance_in_meters = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
        return distance_in_meters

    def calculate_delay(self):
        for link in self.inter_satellite_links:
            # 拿到源节点
            source = link.source_node
            destination = link.dest_node
            distance_in_meters = PositionCalculateService.calculate_two_nodes_distance(source_position=source.position,
                                                                                       dest_position=destination.position)
            delay_in_ms = distance_in_meters / cvm.LIGHT_SPEED_M_S * 1000
            self.isl_delay_map[str(link.link_id)] = int(delay_in_ms)  # json.dumps 不支持 key 类型为 int

    def clear(self):
        """
        在每次完成重新计算之后需要清空
        :return:
        """
        self.isl_delay_map = {}

    def find_nearest_satellite_for_ground_station(self, check_ground_station):
        """
        给定一个地面站，检查所有的卫星，并返回最近的卫星
        :param check_ground_station:
        :return:
        """
        closest_distance = math.inf
        closest_satellite = None
        for satellite in self.satellites:
            current_distance = PositionCalculateService.calculate_two_nodes_distance(check_ground_station.position, satellite.position)
            if current_distance < closest_distance:
                closest_distance = current_distance
                closest_satellite = satellite
            else:
                pass
        return closest_satellite

    def update_connection_map(self):
        for ground_station in self.ground_stations:
            closest_satellite = self.find_nearest_satellite_for_ground_station(ground_station)  # 找到最近的卫星
            # 最近的卫星已经找到, 判断是否已经存在连接
            if self.gsl_connection_map[closest_satellite.node_id] is not None:
                # 如果已经存在连接，不进行任何操作
                pass
            else:
                # 判断地面站是否是初次连接
                if ground_station.initial_connected:
                    ground_station.initial_connected = False  # 更改初次连接状态
                    ground_station.initial_connect_satellite_id = closest_satellite.node_id  # 设置初始连接卫星
                    ground_station.current_connect_satellite_id = closest_satellite.node_id  # 设置当前连接卫星
                    self.gsl_connection_map[closest_satellite.node_id] = ground_station.node_id  # 更新连接关系
                # 如果不是初次连接
                else:
                    # 判断是否是相同的卫星
                    if self.gsl_connection_map[closest_satellite.node_id] == ground_station.node_id:
                        pass
                    # 如果不是相同的卫星,说明连接发生了变化
                    else:
                        logger.success(
                            f"ground station connect from {ground_station.current_connect_satellite_id} -> {closest_satellite.node_id}")
                        self.gsl_connection_map[ground_station.current_connect_satellite_id] = None
                        ground_station.current_connect_satellite_id = closest_satellite.node_id
                        self.gsl_connection_map[closest_satellite.node_id] = ground_station.node_id
        print(self.gsl_connection_map)

    def calculate_position_and_delay(self):
        self.calculate_satellites_position()  # 实时计算卫星的位置
        self.update_connection_map()  # 找到最近的地面站
        self.calculate_delay()
        self.sendmsg_to_notify()
        self.clear()

    def sendmsg_to_notify(self):
        big_map = {
            "isl_delay_map": self.isl_delay_map,
            "gsl_connection_map": self.gsl_connection_map
        }
        send_out_message = json.dumps(big_map, indent=2).encode("utf-8")
        self.channel.basic_publish(exchange="",
                                   routing_key=self.config_reader.update_queue_name,
                                   body=send_out_message)

    def send_quit_msg_to_notify(self):
        send_quit_msg = self.quit_msg.encode("utf-8")
        self.channel.basic_publish(exchange="",
                                   routing_key=self.config_reader.update_queue_name,
                                   body=send_quit_msg)

    def start(self):
        while True:
            if self.stop_queue.empty():
                time.sleep(self.calculation_interval)
                self.constellation_start_time = (self.constellation_start_time +
                                                 datetime.timedelta(seconds=self.calculation_interval * self.speed_rate))
                self.calculate_position_and_delay()
            else:
                self.send_quit_msg_to_notify()
                break
