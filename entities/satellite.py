from entities import entity as em


class Satellite(em.Entity):
    def __init__(self, node_id: int, orbit_id: int, index_in_orbit: int, entity_type: em.EntityType):
        """
        进行卫星的初始化
        :param node_id: 卫星的 id
        :param orbit_id: 卫星所处的轨道的 id
        :param index_in_orbit: 卫星在自己轨道内的位置
        :param entity_type: 实体的类型
        """
        super().__init__(entity_type)
        self.node_id = node_id
        self.orbit_id = orbit_id
        self.index_in_orbit = index_in_orbit
        self.interface_index = 0
        self.link_identifications = {}  # 这是一个 map 从 interface_index --> link_identification
        self.container_id = "None"  # 这是这个节点所对应的容器的id
        self.pid = "None"  # 这个节点对应的进程 id
        self.connect_subnet_list = []  # 节点连接到的子网的数量
        self.ip_addresses = {}  # [从接口索引 -> 接口对应的 ip 地址的映射]
        self.tle = "None"
        self.position = "None"  # 纬度 经度 高度

        # ----------------------- 星地链路 -----------------------
        self.gsl_subnet = None
        self.gsl_satellite_side_address = None
        self.gsl_ground_station_side_address = None
        # ----------------------- 星地链路 -----------------------

    # def __str__(self):
    #     """
    #     返回卫星代表的字符串
    #     :return: str
    #     """
    #     return ("LEO Satellite: " + str(self.node_id) +
    #             " ContainerId: " + self.container_id[:10] + "..."
    #                                                         " Pid: " + str(self.pid) +
    #             " Orbit: " + str(self.orbit_id) +
    #             " Index in orbit: " + str(self.index_in_orbit) +
    #             " Interface IP: " + str(self.ip_addresses))


if __name__ == "__main__":
    sat = Satellite(1, 1, 1)
    print(sat)
    # 输出结果
    # LEO Satellite: 1 Orbit: 1 Index in orbit: 1
