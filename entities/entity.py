from enum import Enum
from const_vars import const_vars as cvm


class EntityType(Enum):
    SATELLITE_NODE = 1
    GROUND_STATION = 2
    CONSENSUS_NODE = 3

    def get_node_prefix(self):
        if self.value == EntityType.SATELLITE_NODE.value:
            return cvm.SATELLITE_NODE_PREFIX
        elif self.value == EntityType.GROUND_STATION.value:
            return cvm.GROUND_STATION_PREFIX
        elif self.value == EntityType.CONSENSUS_NODE.value:
            return cvm.CONSENSUS_NODE_PREFIX
        else:
            raise ValueError("unsupported entity type")


class Entity:
    """
    通用的属性
    :param entity_type 实体的类型
    """

    def __init__(self, entity_type: EntityType):
        self.entity_type = entity_type
        self.node_prefix = entity_type.get_node_prefix()
        self.container_id = None
        self.container_name = None
        self.addr_connect_to_docker_zero = None
        self.pid = None

    @staticmethod
    def resolve_entity_type(container_name: str):
        if cvm.SATELLITE_NODE_PREFIX in container_name:
            return EntityType.SATELLITE_NODE
        elif cvm.GROUND_STATION_PREFIX in container_name:
            return EntityType.GROUND_STATION
        elif cvm.CONSENSUS_NODE_PREFIX in container_name:
            return EntityType.CONSENSUS_NODE
        else:
            return False

    def __str__(self):
        """
        将对象信息作为字符串返回
        :return:
        """
        return (f"ID[{self.container_id}]|NAME[{self.container_name}]|ADDR[{self.addr_connect_to_docker_zero}]|"
                f"PID[{self.pid}]")
