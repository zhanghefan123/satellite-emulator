from enum import Enum
from loguru import logger
from config import config_reader as crm
from docker_client import docker_client_http_impl as dchim
from docker_client import docker_namespace_builder as dnbm
from entities import constellation as cm
from chain_maker_related import contract_manager as cmm


class LeoOrChainGenerator:
    class NetworkState(Enum):
        """
        链的状态，可能有 not_created | created | running | exited 四种状态
        """
        not_created = 0
        created = 1,
        running = 2,
        exited = 3

    def __init__(self, config_reader: crm.ConfigReader, my_logger: logger):
        """
        进行容器的初始化
        :param config_reader: 配置读取对象
        :param my_logger: 日志记录器
        """
        self.my_logger = my_logger  # 日志记录器
        self.config_reader = config_reader  # 配置对象
        self.contract_manager = cmm.ContractManager(cmc_exe_dir=config_reader.abs_of_cmc_dir, my_logger=my_logger)  # 合约管理
        self.docker_client = dchim.DockerClientHttpImpl(self.config_reader.base_url)  # 创建容器的对象
        self.chain_state = LeoOrChainGenerator.NetworkState.not_created  # 当前状态
        self.logical_constellation: cm.Constellation = cm.Constellation(config_reader=self.config_reader)  # 逻辑星座
        self.container_prefix = None    # 容器前缀
        self.number_of_containers = None  # 容器数量
        self.set_prepare_param()  # 预先准备的属性

    # ----------------------------- 链管理相关  -----------------------------

    def set_prepare_param(self):
        """
        1、进行前缀的设置
        2、进行镜像名的设置
        3、进行节点数量的设置
        """
        # 进行节点 prefix 的确定：
        if self.config_reader.generate_leo_or_chain == "leo":
            self.container_prefix = "sat"
            self.number_of_containers = self.config_reader.number_of_satellites  # number_of_satellites 等于轨道数 * 每轨道的卫星的数量
        elif self.config_reader.generate_leo_or_chain == "chain":
            self.container_prefix = "consensus_node"
            self.number_of_containers = self.config_reader.number_of_cm_node
        else:
            raise ValueError("generate_or_chain must be leo or chain")

    async def create_network(self):
        """
        1. 根据配置信息 (环境变量、容器卷映射、端口映射等)，进行区块链上的节点的创建
        2. 将状态从 not_created 切换为 created 状态
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.not_created:
            self.logical_constellation = cm.Constellation(config_reader=self.config_reader)
            self.logical_constellation.start_generate_static_infos()
            await self.logical_constellation.generate_ground_stations()
            await self.logical_constellation.generate_sky_nodes()
            self.chain_state = LeoOrChainGenerator.NetworkState.created

    async def start_network(self):
        """
        进行停止容器的恢复, 只有容器处于 STOPPED 或者 CREATED 的状态的时候才能够被 start 启动起来。
        :return:
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.exited or \
                self.chain_state == LeoOrChainGenerator.NetworkState.created:
            await self.logical_constellation.start_sky_nodes()
            await self.logical_constellation.start_ground_stations()
            self.chain_state = LeoOrChainGenerator.NetworkState.running
        else:
            self.my_logger.error("satellite containers not in stopped or created state! could not be started!")
        await self.inspect_network_with_id()
        self.generate_connections()

    async def stop_network(self):
        """
        进行容器的停止 - 只有位于运行状态的容器才能被停止，并将状态转换为停止状态。
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.running:
            await self.logical_constellation.stop_sky_nodes()
            await self.logical_constellation.stop_ground_stations()
            self.chain_state = LeoOrChainGenerator.NetworkState.exited
        else:
            self.my_logger.error("satellite containers not in running state! cannot be stopped!")

    async def remove_network(self):
        """
        进行容器的删除:
            1. 如果容器位于运行状态，那么需要先进行停止，然后进行删除，将状态转换为 NOT_CREATED
            2. 如果容器位于刚创建的状态，那么直接进行删除即可
            3. 如果容器位于停止状态，那么直接进行删除，将状态转换为 NOT_CREATED
        """
        # 进行其他容器的删除
        # 如果容器位于运行状态的处理
        if self.chain_state == LeoOrChainGenerator.NetworkState.running:
            await self.stop_network()
            await self.logical_constellation.remove_sky_nodes()
            await self.logical_constellation.remove_ground_stations()
            self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        # 如果容器位于创建状态的处理
        elif self.chain_state == LeoOrChainGenerator.NetworkState.created:
            await self.logical_constellation.remove_sky_nodes()
            await self.logical_constellation.remove_ground_stations()
            self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        # 如果容器位于停止状态的处理
        elif self.chain_state == LeoOrChainGenerator.NetworkState.exited:
            await self.logical_constellation.remove_sky_nodes()
            await self.logical_constellation.remove_ground_stations()
            self.chain_state = LeoOrChainGenerator.NetworkState.not_created
        else:
            self.my_logger.error("constellation are already be removed!")
        self.logical_constellation.delete_all_bridges()

    async def inspect_network_with_id(self):
        """
        进行卫星网络之中的容器的信息的检查
        """
        if self.chain_state == LeoOrChainGenerator.NetworkState.not_created:
            self.my_logger.error("satellite containers must be created before being inspected!")
        else:
            await self.logical_constellation.inspect_sky_nodes_with_container_id()
            await self.logical_constellation.inspect_ground_stations_with_container_id()
            self.logical_constellation.print_network_info()

    # ----------------------------- 链管理相关  -----------------------------

    # ----------------------------- 创建链路相关  -----------------------------
    def generate_connections(self):
        """
        进行节点间的连接
        """
        sky_nodes_pid_list = [item.pid for item in self.logical_constellation.satellites]
        ground_station_pid_list = [item.pid for item in self.logical_constellation.ground_stations]
        dnbm.DockerNamespaceBuilder.build_network_namespace(sky_nodes_pid_list + ground_station_pid_list)
        self.logical_constellation.generate_veth_pairs_for_all_links()

    # ----------------------------- 创建链路相关  -----------------------------
