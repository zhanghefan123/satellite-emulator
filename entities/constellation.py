import sys

if __name__ == "__main__":
    sys.path.append("..")
import os
import tqdm
import copy
import asyncio
import networkx as nx
from entities import entity as em
from entities import satellite as sm
from config import config_reader as crm
from entities import normal_link as islm
from entities import ground_station as gsm
from useful_tools import progress_bar as pbm
from generator import subnet_generator as sgm
from useful_tools import tle_generator as tgm
from useful_tools import multithread_executor as mem
from entities import lir_link_identification as llim
from docker_client import docker_client_http_impl as dchim
from const_vars import const_vars as cvm
from entities import constellation_type as ctm
from command_client import command_client_unit as ccum
from pyroute2 import IPRoute, NetNS


class Constellation:

    def __init__(self, config_reader: crm.ConfigReader):
        """
        进行星座的初始化
        :param config_reader: 配置对象
        """
        self.config_reader = config_reader
        self.id_to_satellite_map = {}  # 存储 [container_id <-> satellite]
        self.satellites = []  # 存储在当前星座下的所有的卫星
        self.id_to_groundstation_map = {}  # 存储 [container_id <-> ground_station]
        self.ground_stations = []  # 存储当前星座下的所有地面站
        self.satellite_links_without_direction = []  # 存储星间无向链路
        self.lir_link_identifiers = []  # lir 的链路标识序列
        self.map_from_source_dest_pair_to_link_identifier = {}  # 从 source->dest 对到链路标识的映射
        self.subnet_generator = sgm.SubnetGenerator.generate_subnets(
            base_network_tmp=self.config_reader.base_network_address)  # 这是一个生成器，为了保证不发生重复，我们只能使用这一个生成器
        self.direction_graph = None  # networkx 产生的有向图
        self.docker_client = dchim.DockerClientHttpImpl(self.config_reader.base_url)  # 创建容器的对象
        self.command_client = None  # 用来和容器进行 tcp 交互的
        self.set_command_client()

    def load_ground_stations(self):
        self.ground_stations = gsm.GroundStation.load_ground_stations_from_config_reader(self.config_reader)  # 读取地面站信息

    def set_command_client(self):
        if self.config_reader.generate_leo_or_chain == "leo":
            self.command_client = ccum.CommandClientUnit(
                server_listen_port=self.config_reader.listening_port,
                satellites=self.satellites,
                satellites_map=self.id_to_satellite_map)
        else:
            pass

    def start_generate_static_infos(self):
        """
        开始产生静态的信息
        :return:
        """
        self.load_ground_stations()
        self.generate_satellites_and_tle()
        self.generate_isls_without_direction()
        self.generate_lir_files()
        self.calculate_routes_with_all_nodes()  # 进行路由的计算和存储
        self.modify_nodes_chainmaker_yml()
        self.generate_id_to_addresses_mapping()  # 进行 ip 地址的留存
        self.generate_frr_files()

    async def generate_sky_nodes(self):
        """
        进行天空节点的生成
        :return:
        """
        tasks = []
        number_of_entity = self.config_reader.number_of_cm_node
        node_prefix = self.config_reader.node_prefix
        node_type = self.config_reader.node_type
        start_frr = self.config_reader.start_frr
        enable_lir = self.config_reader.lir_enabled
        for index in range(0, number_of_entity):
            node_name = f"{node_prefix}{index}"
            # ------------------------------- 如果进行的是长安链节点的创建 -------------------------------
            if node_type == em.EntityType.CONSENSUS_NODE:
                # 环境变量
                # ---------------------------------------------------------
                environment = [f"NODE_TYPE={node_prefix}",
                               f"NODE_ID={index}",
                               f"INTERFACE_COUNT={self.satellites[index].interface_index}",
                               f"LISTEN_ADDR={self.satellites[index].ip_addresses[0]}",
                               f"START_FRR={start_frr}",
                               f"LIR_ENABLED={enable_lir}"]
                # ---------------------------------------------------------

                # 容器卷映射
                # ---------------------------------------------------------
                volumes = [
                    f"{self.config_reader.abs_of_multi_node}/config/node{index + 1}:/chainmaker-go/config/wx-org{index + 1}.chainmaker.org",
                    f"{self.config_reader.abs_of_multi_node}/data/data{index + 1}:/chainmaker-go/data",
                    f"{self.config_reader.abs_of_multi_node}/log/log{index + 1}:/chainmaker-go/log",
                    f"{self.config_reader.abs_of_frr_configuration}:/configuration/frr",
                    f"{self.config_reader.abs_of_routes_configuration}:/configuration/routes",
                    f"{self.config_reader.abs_of_address_configuration}:/configuration/address",
                    f"{self.config_reader.abs_of_lir_configuration}:/configuration/lir"
                ]
                # print(volumes, flush=True)
                # ---------------------------------------------------------

                # 端口映射
                # ---------------------------------------------------------
                exposed_ports = {
                    # f"{self.config_reader.p2p_port + (index)}/tcp": {},
                    f"{self.config_reader.rpc_port + index}/tcp": {},
                }
                port_bindings = {
                    # f"{self.config_reader.p2p_port + (index)}/tcp": [
                    #     {
                    #         "HostIp": "",
                    #         "HostPort": f"{self.config_reader.p2p_port + (index)}"
                    #     }
                    # ]
                    # ,
                    f"{self.config_reader.rpc_port + index}/tcp": [
                        {
                            "HostIp": "",
                            "HostPort": f"{self.config_reader.rpc_port + index}"
                        }
                    ]
                }
                # ---------------------------------------------------------

                # 在容器内执行的命令
                # ---------------------------------------------------------
                command = [
                    "./chainmaker",
                    "start",
                    "-c",
                    f"../config/wx-org{index + 1}.chainmaker.org/chainmaker.yml"
                ]
                # f"./chainmaker start -c ../config/wx-org{index}.chainmaker.org/chainmaker.yml"
                # ---------------------------------------------------------

                # 工作目录
                # ---------------------------------------------------------
                working_dir = "/chainmaker-go/bin"
                # ---------------------------------------------------------
                task = asyncio.create_task(
                    self.docker_client.create_container(image_name=self.config_reader.chain_image_name,
                                                        environment=environment,
                                                        container_name=node_name,
                                                        volumes=volumes,
                                                        exposed_ports=exposed_ports,
                                                        port_bindings=port_bindings,
                                                        command=command,
                                                        working_dir=working_dir,
                                                        container_index=index))
                tasks.append(task)
            # ------------------------------- 如果进行的是长安链节点的创建 -------------------------------
            # -------------------------------- 如果进行的是卫星节点的创建 --------------------------------
            elif node_type == em.EntityType.SATELLITE_NODE:
                # 环境变量
                # ---------------------------------------------------------
                environment = [f"SATELLITE_NAME={node_name}",
                               f"LISTENING_PORT={self.config_reader.listening_port}",
                               f"NODE_TYPE={node_prefix}",
                               f"NODE_ID={index}",
                               f"DISPLAY=unix:0.0",
                               f"GDK_SCALE",
                               f"GDK_DPI_SCALE",
                               f"START_FRR={start_frr}",
                               f"LIR_ENABLED={enable_lir}"]
                # ---------------------------------------------------------
                # 容器卷映射
                # ---------------------------------------------------------
                volumes = [
                    f"{self.config_reader.abs_of_frr_configuration}:/configuration/frr",
                    f"{self.config_reader.abs_of_routes_configuration}:/configuration/routes",
                    f"{self.config_reader.abs_of_address_configuration}:/configuration/address",
                    f"{self.config_reader.abs_of_lir_configuration}:/configuration/lir",
                    f"{self.config_reader.abs_of_videos_storage}:/configuration/videos",  # 视频传输业务搜需要的视频
                    f"/tmp/.X11-unix:/tmp/.X11-unix"  # 视频传输时要用到宿主机的显示
                ]
                # ---------------------------------------------------------
                # 进行任务的创建
                # ---------------------------------------------------------
                task = asyncio.create_task(
                    self.docker_client.create_container(image_name=self.config_reader.satellite_image_name,
                                                        environment=environment,
                                                        container_name=node_name,
                                                        volumes=volumes,
                                                        container_index=index))
                # ---------------------------------------------------------
                tasks.append(task)
            # -------------------------------- 如果进行的是卫星节点的创建 --------------------------------
            else:
                raise ValueError("unsupported node type")
        await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="create sky nodes process")
        for single_task in tasks:
            container_index, entity_container_id = single_task.result()
            self.satellites[container_index].container_id = entity_container_id
            self.id_to_satellite_map[entity_container_id] = self.satellites[container_index]

    async def generate_ground_stations(self):
        """
        进行地面站的异步生成
        :return:
        """
        if len(self.ground_stations) > 0:
            tasks = []
            # 遍历每一个地面站
            for index, ground_station in enumerate(self.ground_stations):
                # 进行调用然后可以
                node_name = f"{cvm.GROUND_STATION_PREFIX}{index}"
                task = asyncio.create_task(
                    self.docker_client.create_container(image_name=self.config_reader.ground_image_name,
                                                        container_name=node_name,
                                                        container_index=index), )
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="create ground station process")
            for single_task in tasks:
                current_index, entity_container_id = single_task.result()
                self.ground_stations[current_index].container_id = entity_container_id
                self.id_to_groundstation_map[entity_container_id] = self.ground_stations[current_index]

    async def start_sky_nodes(self):
        tasks = []
        satellite_container_ids = [satellite.container_id for satellite in self.satellites]
        for container_id in satellite_container_ids:
            task = asyncio.create_task(
                self.docker_client.start_container(container_id))
            tasks.append(task)
        await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="start sky nodes process")

    async def start_ground_stations(self):
        if len(self.ground_stations) > 0:
            tasks = []
            ground_station_container_ids = [ground_station.container_id for ground_station in self.ground_stations]
            for container_id in ground_station_container_ids:
                task = asyncio.create_task(
                    self.docker_client.start_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="start ground_station process ")

    def set_default_params_of_bloom_filter(self):
        if self.command_client:
            asyncio.run(self.command_client.set_default_params_of_bloom_filter(
                default_bloom_filter_length=self.config_reader.default_bloom_filter_length,
                default_hash_seed=self.config_reader.default_hash_seed,
                default_number_of_hash_funcs=self.config_reader.default_number_of_hash_funcs))
        else:
            pass

    async def stop_sky_nodes(self):
        tasks = []
        satellite_container_ids = [satellite.container_id for satellite in self.satellites]
        for container_id in satellite_container_ids:
            task = asyncio.create_task(
                self.docker_client.stop_container(container_id))
            tasks.append(task)
        await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="stop sky nodes process")

    async def stop_ground_stations(self):
        if len(self.ground_stations) > 0:
            tasks = []
            ground_station_container_ids = [ground_station.container_id for ground_station in self.ground_stations]
            for container_id in ground_station_container_ids:
                task = asyncio.create_task(
                    self.docker_client.stop_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="stop ground stations process")

    async def remove_sky_nodes(self):
        tasks = []
        satellite_container_ids = [satellite.container_id for satellite in self.satellites]
        for container_id in satellite_container_ids:
            task = asyncio.create_task(self.docker_client.delete_container(container_id))
            tasks.append(task)
        await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove sky nodes process")

    async def remove_ground_stations(self):
        if len(self.ground_stations) > 0:
            tasks = []
            ground_station_container_ids = [ground_station.container_id for ground_station in self.ground_stations]
            for container_id in ground_station_container_ids:
                task = asyncio.create_task(self.docker_client.delete_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="remove ground stations process")

    async def inspect_sky_nodes_with_container_id(self):
        satellite_container_ids = [satellite.container_id for satellite in self.satellites]
        tasks = []
        for container_id in satellite_container_ids:
            task = asyncio.create_task(self.docker_client.inspect_container(container_id))
            tasks.append(task)
        await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="inspect sky nodes process")
        # 遍历所有已经完成的任务
        for single_finished_task in tasks:
            finished_task_result = single_finished_task.result()
            inspect_container_id = finished_task_result["ID"]
            inspect_container_addr = finished_task_result["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
            inspect_container_name = finished_task_result["Name"].lstrip("/")
            inspect_container_pid = finished_task_result["State"]["Pid"]
            self.id_to_satellite_map[
                inspect_container_id].addr_connect_to_docker_zero = inspect_container_addr
            self.id_to_satellite_map[inspect_container_id].container_name = inspect_container_name
            self.id_to_satellite_map[inspect_container_id].pid = inspect_container_pid

    async def inspect_ground_stations_with_container_id(self):
        if len(self.ground_stations) > 0:
            ground_station_container_ids = [ground_station.container_id for ground_station in self.ground_stations]
            tasks = []
            for container_id in ground_station_container_ids:
                task = asyncio.create_task(self.docker_client.inspect_container(container_id))
                tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(tasks, description="inspect ground stations process")
            # 遍历所有已经完成的任务
            for single_finished_task in tasks:
                finished_task_result = single_finished_task.result()
                inspect_container_id = finished_task_result["ID"]
                inspect_container_addr = finished_task_result["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
                inspect_container_name = finished_task_result["Name"].lstrip("/")
                inspect_container_pid = finished_task_result["State"]["Pid"]
                self.id_to_groundstation_map[inspect_container_id].addr_connect_to_docker_zero = inspect_container_addr
                self.id_to_groundstation_map[inspect_container_id].container_name = inspect_container_name
                self.id_to_groundstation_map[inspect_container_id].pid = inspect_container_pid

    def print_network_info(self):
        """
        进行区块链之中容器的信息的打印
        """
        # 进行总长度的获取
        total_length = 97
        top_and_bottom = "-" * total_length
        print(f"{top_and_bottom}")
        for satellite in self.satellites:
            print(f"satellite: {satellite}")
        for ground_station in self.ground_stations:
            print(f"ground station: {ground_station}")
        print(f"{top_and_bottom}")

    @staticmethod
    def generate_veth_pair_for_single_link_with_bridge(inter_satellite_link, node_type):
        """
        进行单条星间链路的生成 (带有 bridge)
        :param inter_satellite_link: 星间链路
        :param node_type: 节点类型
        :return:
        """
        if node_type == em.EntityType.CONSENSUS_NODE:
            first_veth_name = f"cn{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
            first_sat_pid = inter_satellite_link.source_node.pid
            first_sat_ip = inter_satellite_link.source_interface_address
            second_veth_name = f"cn{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
            second_sat_pid = inter_satellite_link.dest_node.pid
            second_sat_ip = inter_satellite_link.dest_interface_address
            bridge_name = inter_satellite_link.bridge_name
            bridge_interface_name_for_first_sat = f"vth{inter_satellite_link.source_node.node_id}_{bridge_name}"
            bridge_interface_name_for_second_sat = f"vth{inter_satellite_link.dest_node.node_id}_{bridge_name}"
        elif node_type == em.EntityType.SATELLITE_NODE:
            first_veth_name = f"sa{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
            first_sat_pid = inter_satellite_link.source_node.pid
            first_sat_ip = inter_satellite_link.source_interface_address
            second_veth_name = f"sa{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
            second_sat_pid = inter_satellite_link.dest_node.pid
            second_sat_ip = inter_satellite_link.dest_interface_address
            bridge_name = inter_satellite_link.bridge_name
            bridge_interface_name_for_first_sat = f"vth{inter_satellite_link.source_node.node_id}_{bridge_name}"
            bridge_interface_name_for_second_sat = f"vth{inter_satellite_link.dest_node.node_id}_{bridge_name}"
        else:
            raise ValueError("unsupported node type")
        first_sat_net_namespace_path = f"/var/run/netns/{first_sat_pid}"
        second_sat_net_namespace_path = f"/var/run/netns/{second_sat_pid}"
        ip = IPRoute()
        ip.link("add", ifname=bridge_name, kind="bridge")  # 创建网桥
        ip.link("add", ifname=first_veth_name, peer=bridge_interface_name_for_first_sat, kind="veth")  # 创建从接口1到交换机的连接
        ip.link("add", ifname=second_veth_name, peer=bridge_interface_name_for_second_sat, kind="veth")  # 创建从接口2到交换机的连接
        bridge_index = ip.link_lookup(ifname=bridge_name)[0]  # 拿到网桥 index
        first_veth_index = ip.link_lookup(ifname=first_veth_name)[0]  # 拿到接口1 index
        second_veth_index = ip.link_lookup(ifname=second_veth_name)[0]   # 拿到接口2 index
        bridge_interface_for_first_index = ip.link_lookup(ifname=bridge_interface_name_for_first_sat)[0]  # 拿到交换机接口1 index
        bridge_interface_for_second_index = ip.link_lookup(ifname=bridge_interface_name_for_second_sat)[0]  # 拿到交换机接口2 index
        ip.link("set", index=first_veth_index, net_ns_fd=first_sat_net_namespace_path)  # 设置网络命名空间
        ip.link("set", index=second_veth_index, net_ns_fd=second_sat_net_namespace_path)  # 设置网络命名空间
        ip.link("set", index=bridge_interface_for_first_index, master=bridge_index)  # 绑定接口到网桥
        ip.link("set", index=bridge_interface_for_second_index, master=bridge_index)  # 绑定接口到网桥
        ip.link("set", index=bridge_index, state="up")  # 启动网桥
        ip.link("set", index=bridge_interface_for_first_index, state="up")
        ip.link("set", index=bridge_interface_for_second_index, state="up")
        with NetNS(first_sat_net_namespace_path) as ns:
            idx = ns.link_lookup(ifname=first_veth_name)[0]
            ns.addr("add", index=idx, address=first_sat_ip[:-3], prefixlen=30)
            ns.link("set", index=idx, state="up")
        with NetNS(second_sat_net_namespace_path) as ns:
            idx = ns.link_lookup(ifname=second_veth_name)[0]
            ns.addr("add", index=idx, address=second_sat_ip[:-3], prefixlen=30)
            ns.link("set", index=idx, state="up")
        ip.close()

    @staticmethod
    def generate_veth_pair_for_single_link_without_bridge(inter_satellite_link, node_type):
        """
        进行单条星间链路的生成 (不带有 bridge)
        :param inter_satellite_link: 星间链路
        :param node_type: 节点类型
        :return:
        """
        if node_type == em.EntityType.CONSENSUS_NODE:
            first_veth_name = f"cn{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
            first_sat_pid = inter_satellite_link.source_node.pid
            first_sat_ip = inter_satellite_link.source_interface_address
            second_veth_name = f"cn{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
            second_sat_pid = inter_satellite_link.dest_node.pid
            second_sat_ip = inter_satellite_link.dest_interface_address
        elif node_type == em.EntityType.SATELLITE_NODE:
            first_veth_name = f"sa{inter_satellite_link.source_node.node_id}_index{inter_satellite_link.source_interface_index + 1}"
            first_sat_pid = inter_satellite_link.source_node.pid
            first_sat_ip = inter_satellite_link.source_interface_address
            second_veth_name = f"sa{inter_satellite_link.dest_node.node_id}_index{inter_satellite_link.dest_interface_index + 1}"
            second_sat_pid = inter_satellite_link.dest_node.pid
            second_sat_ip = inter_satellite_link.dest_interface_address
        else:
            raise ValueError("unsupported node type")
        first_sat_net_namespace_path = f"/var/run/netns/{first_sat_pid}"
        second_sat_net_namespace_path = f"/var/run/netns/{second_sat_pid}"
        # 在宿主机的命名空间之中
        ip = IPRoute()
        ip.link("add", ifname=first_veth_name, peer=second_veth_name, kind="veth")
        ip.link("set", index=ip.link_lookup(ifname=first_veth_name)[0], net_ns_fd=first_sat_net_namespace_path)
        ip.link("set", index=ip.link_lookup(ifname=second_veth_name)[0], net_ns_fd=second_sat_net_namespace_path)
        with NetNS(first_sat_net_namespace_path) as ns:
            idx = ns.link_lookup(ifname=first_veth_name)[0]
            ns.addr("add", index=idx, address=first_sat_ip[:-3], prefixlen=30)
            ns.link("set", index=idx, state="up")
        with NetNS(second_sat_net_namespace_path) as ns:
            idx = ns.link_lookup(ifname=second_veth_name)[0]
            ns.addr("add", index=idx, address=second_sat_ip[:-3], prefixlen=30)
            ns.link("set", index=idx, state="up")
        ip.close()

    @staticmethod
    def generate_veth_pair_for_single_link(inter_satellite_link, node_type, with_bridge):
        """
        进行单条星间链路的生成
        :param inter_satellite_link: 星间链路
        :param node_type: 节点类型
        :param with_bridge: 是否生成带有 bridge 的
        :return:
        """
        if with_bridge:
            Constellation.generate_veth_pair_for_single_link_with_bridge(inter_satellite_link, node_type)
        else:
            Constellation.generate_veth_pair_for_single_link_without_bridge(inter_satellite_link, node_type)

    def generate_veth_pairs_for_all_links(self):
        """
        进行所有星间链路的 veth pair 的生成
        :return:
        """
        tasks = []
        args = []
        with_bridge = self.config_reader.with_bridge
        for inter_satellite_link in self.satellite_links_without_direction:
            tasks.append(Constellation.generate_veth_pair_for_single_link)
            args.append((inter_satellite_link, inter_satellite_link.source_node.entity_type, with_bridge,))
        multithread_executor = mem.MultithreadExecutor(max_workers=50)
        multithread_executor.execute_with_multiple_thread(task_list=tasks, args_list=args,
                                                          description="generate veth pairs")

    def delete_all_bridges(self):
        """
        进行所有的桥的删除
        :return:
        """
        with_bridge = self.config_reader.with_bridge
        if with_bridge:
            # 需要进行删除
            ip = IPRoute()
            bar_format = '{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'
            description = "delete bridges"
            with tqdm.tqdm(total=len(self.satellite_links_without_direction), colour="green", ncols=97, postfix="", bar_format=bar_format) as pbar:
                pbar.set_description(description)
                for inter_satellite_link in self.satellite_links_without_direction:
                    bridge_index = ip.link_lookup(ifname=inter_satellite_link.bridge_name)[0]
                    ip.link("del", index=bridge_index)
                    pbar.update(1)
            ip.close()
        else:
            # 不需要进行删除
            pass

    def generate_id_to_addresses_mapping(self):
        """
        进行从节点编号到地址的映射的生成
        """
        generate_destination = self.config_reader.abs_of_address_configuration
        node_prefix = self.config_reader.node_prefix
        final_str = ""
        for single_satellite in self.satellites:
            line_str = f"{node_prefix}{single_satellite.node_id}|"
            for item in single_satellite.ip_addresses.items():
                if item[0] != (len(single_satellite.ip_addresses) - 1):
                    line_str += f"{item[1]}|"
                else:
                    line_str += item[1]
            final_str += f"{line_str}\n"
        with open(f"{generate_destination}/address_mapping.conf", "w") as f:
            f.write(final_str)

    def generate_lir_files(self):
        """
        进行 lir 配置文件的生成
        :return:
        """
        node_type = self.config_reader.node_type
        node_prefix = self.config_reader.node_prefix
        for satellite in self.satellites:
            lir_file_path = f"{self.config_reader.abs_of_lir_configuration}/{node_prefix}_{satellite.node_id}.conf"
            with open(lir_file_path, "w") as f:
                final_str = ""
                for interface_index in satellite.link_identifications:
                    if node_type == em.EntityType.SATELLITE_NODE:
                        final_str += f"sa{satellite.node_id}_index{interface_index + 1}->{satellite.link_identifications[interface_index]}\n"
                    elif node_type == em.EntityType.CONSENSUS_NODE:
                        final_str += f"cn{satellite.node_id}_index{interface_index + 1}->{satellite.link_identifications[interface_index]}\n"
                    else:
                        raise ValueError("unsupported value type")
                f.write(final_str)

    def generate_frr_files(self):
        """
        进行 frr 配置文件的生成
        :return:
        """
        generate_destination = self.config_reader.abs_of_frr_configuration
        node_prefix = self.config_reader.node_prefix
        if not os.path.exists(generate_destination):
            os.system(f"mkdir -p {generate_destination}")
        for single_satellite in self.satellites:
            with open(f"{generate_destination}/"
                      f"{node_prefix}_{single_satellite.node_id}.conf", "w") as f:
                full_str = \
                    f"""frr version 7.2.1 
frr defaults traditional
hostname satellite_{single_satellite.node_id}
log syslog informational
no ipv6 forwarding
service integrated-vtysh-config
!
router ospf
    redistribute connected
"""
                for connected_subnet in single_satellite.connect_subnet_list:
                    full_str += f"\t network {connected_subnet} area 0.0.0.0\n"
                full_str += "!\n"
                full_str += "line vty\n"
                full_str += "!\n"
                f.write(full_str)

    @staticmethod
    async def wait_tasks_with_tqdm(tasks, description=""):
        """
        按照给定的任务进行进度条的生成
        :param tasks:  任务
        :param description: 任务的描述
        :return:
        """
        copied_tasks = copy.copy(tasks)
        task_length = len(copied_tasks)
        bar_format = '{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'
        with tqdm.tqdm(total=task_length, colour="green", ncols=97, postfix="", bar_format=bar_format) as pbar:
            pbar.set_description(description)
            while True:
                done, pending = await asyncio.wait(copied_tasks, return_when=asyncio.FIRST_COMPLETED)
                copied_tasks = list(pending)
                pbar.update(len(done))
                if len(pending) == 0:
                    break

    def generate_satellites_and_tle(self) -> None:
        """
        生成在星座之中的卫星, 并存放到 self.satellites 列表之中
        """
        freq = 24  # 每天环绕地球的圈数
        line_1 = "1 00000U 23666A   %02d%012.8f  .00000000  00000-0 00000000 0 0000"
        line_2 = "2 00000  90.0000 %08.4f 0000011   0.0000 %8.4f %11.8f00000"
        constellation_start_time = self.config_reader.constellation_start_time
        year2, day = tgm.TleGenerator.get_year_day(constellation_start_time)
        start_latitude = 0
        start_longitude = 0
        delta = 5
        for orbit_id in range(0, self.config_reader.num_of_orbit):
            orbit_start_latitude = start_latitude + delta
            orbit_start_longitude = start_longitude + 180 * orbit_id / self.config_reader.sat_per_orbit
            for i in range(self.config_reader.sat_per_orbit * orbit_id,
                           self.config_reader.sat_per_orbit * (orbit_id + 1)):
                index_in_orbit = i % self.config_reader.sat_per_orbit
                satellite_latitude = orbit_start_latitude + 360 * index_in_orbit / self.config_reader.sat_per_orbit
                satellite_tle_line1 = line_1 % (year2, day)
                satellite_tle_line2 = line_2 % (orbit_start_longitude, satellite_latitude, freq)
                satellite_tle_line1 = satellite_tle_line1 + str(tgm.TleGenerator.str_checksum(satellite_tle_line1))
                satellite_tle_line2 = satellite_tle_line2 + str(tgm.TleGenerator.str_checksum(satellite_tle_line2))
                single_satellite = sm.Satellite(i, orbit_id, index_in_orbit, entity_type=em.EntityType.SATELLITE_NODE)
                single_satellite.container_name = f"{cvm.SATELLITE_NODE_PREFIX}{i}"
                single_satellite.tle = [satellite_tle_line1, satellite_tle_line2]
                # 这里进行 IP 地址的提前指定
                subnet, first_address, second_address = next(self.subnet_generator)
                single_satellite.gsl_subnet = subnet
                single_satellite.gsl_satellite_side_address = first_address
                single_satellite.gsl_ground_station_side_address = second_address
                self.satellites.append(single_satellite)

    def generate_isls_without_direction(self) -> None:
        """
        进行无向星间链路的生成, 并存放到 self.links_without_direction 列表之中
        """
        for single_satellite in self.satellites:
            # ----------------------------------- 进行同轨道星间链路的创建 -----------------------------------
            source_orbit_id = single_satellite.orbit_id
            source_index_in_orbit = single_satellite.index_in_orbit
            source_index = single_satellite.node_id
            source_node = self.satellites[source_index]
            source_interface_index = source_node.interface_index
            dest_orbit_id = source_orbit_id
            dest_index_in_orbit = (source_index_in_orbit + 1) % self.config_reader.sat_per_orbit
            dest_index = dest_orbit_id * self.config_reader.sat_per_orbit + dest_index_in_orbit
            dest_node = self.satellites[dest_index]
            dest_interface_index = dest_node.interface_index
            if (source_orbit_id == dest_orbit_id) and (source_index_in_orbit == dest_index_in_orbit):
                pass
            else:
                current_link_id = len(self.satellite_links_without_direction)
                # 生成一条无向的星间链路
                # 调用子网生成器进行 ip 的分配
                subnet, first_address, second_address = next(self.subnet_generator)
                source_node.connect_subnet_list.append(subnet)
                dest_node.connect_subnet_list.append(subnet)
                source_node.ip_addresses[source_node.interface_index] = first_address
                dest_node.ip_addresses[dest_node.interface_index] = second_address
                link_tmp = islm.NormalLink(link_id=current_link_id, source_node=source_node,
                                           source_interface_index=source_interface_index,
                                           source_interface_address=first_address,
                                           dest_node=dest_node,
                                           dest_interface_index=dest_interface_index,
                                           link_type=islm.NormalLink.Type.INTRA_ORBIT,
                                           dest_interface_address=second_address)
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                current_link_identification = len(self.lir_link_identifiers)
                forward_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=source_node,
                                                            source_interface_index=source_interface_index,
                                                            dest_node=dest_node)
                source_node.link_identifications[source_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(forward_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (source_node.node_id, dest_node.node_id)] = forward_identifier
                current_link_identification = len(self.lir_link_identifiers)
                reverse_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=dest_node,
                                                            source_interface_index=dest_interface_index,
                                                            dest_node=source_node)
                dest_node.link_identifications[dest_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(reverse_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (dest_node.node_id, source_node.node_id)] = reverse_identifier
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                source_node.interface_index += 1
                dest_node.interface_index += 1
                self.satellite_links_without_direction.append(link_tmp)
            # ----------------------------------- 进行同轨道星间链路的创建 -----------------------------------
            # ----------------------------------- 进行异轨道星间链路的创建 -----------------------------------
            dest_orbit_id = source_orbit_id + 1
            if dest_orbit_id < self.config_reader.num_of_orbit:
                dest_index_in_orbit = source_index_in_orbit
                dest_index = dest_orbit_id * self.config_reader.sat_per_orbit + dest_index_in_orbit
                dest_node = self.satellites[dest_index]
                current_link_id = len(self.satellite_links_without_direction)
                # 调用子网生成器进行 ip 的分配
                subnet, first_address, second_address = next(self.subnet_generator)
                source_node.connect_subnet_list.append(subnet)
                dest_node.connect_subnet_list.append(subnet)
                source_node.ip_addresses[source_node.interface_index] = first_address
                dest_node.ip_addresses[dest_node.interface_index] = second_address
                link_tmp = islm.NormalLink(link_id=current_link_id, source_node=source_node,
                                           source_interface_index=source_node.interface_index,
                                           source_interface_address=first_address,
                                           dest_node=dest_node,
                                           dest_interface_index=dest_node.interface_index,
                                           dest_interface_address=second_address,
                                           link_type=islm.NormalLink.Type.INTER_ORBIT)
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                current_link_identification = len(self.lir_link_identifiers)
                forward_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=source_node,
                                                            source_interface_index=source_interface_index,
                                                            dest_node=dest_node)
                source_node.link_identifications[source_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(forward_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (source_node.node_id, dest_node.node_id)] = forward_identifier
                current_link_identification = len(self.lir_link_identifiers)
                reverse_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=dest_node,
                                                            source_interface_index=dest_interface_index,
                                                            dest_node=source_node)
                dest_node.link_identifications[dest_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(reverse_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (dest_node.node_id, source_node.node_id)] = reverse_identifier
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                source_node.interface_index += 1
                dest_node.interface_index += 1
                self.satellite_links_without_direction.append(link_tmp)
            # ----------------------------------- 进行异轨道星间链路的创建 -----------------------------------
        # ----------------------- 如果是 walker delta 星座还需要额外的一步 [连接首尾轨道] -----------------------
        if self.config_reader.constellation_type == ctm.ConstellationType.WALKER_DELTA_CONSTELLATION:
            for source_index in range(0, self.config_reader.sat_per_orbit):
                source_node = self.satellites[source_index]
                source_interface_index = source_node.interface_index
                dest_index = (self.config_reader.num_of_orbit - 1) * self.config_reader.sat_per_orbit + source_index
                dest_node = self.satellites[dest_index]
                dest_interface_index = dest_node.interface_index
                current_link_id = len(self.satellite_links_without_direction)
                # 调用子网生成器进行 ip 的分配
                subnet, first_address, second_address = next(self.subnet_generator)
                source_node.connect_subnet_list.append(subnet)
                dest_node.connect_subnet_list.append(subnet)
                source_node.ip_addresses[source_node.interface_index] = first_address
                dest_node.ip_addresses[dest_node.interface_index] = second_address
                link_tmp = islm.NormalLink(link_id=current_link_id,
                                           source_node=source_node,
                                           source_interface_index=source_node.interface_index,
                                           source_interface_address=first_address,
                                           dest_node=dest_node,
                                           dest_interface_index=dest_node.interface_index,
                                           dest_interface_address=second_address,
                                           link_type=islm.NormalLink.Type.INTER_ORBIT)
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                current_link_identification = len(self.lir_link_identifiers)
                forward_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=source_node,
                                                            source_interface_index=source_interface_index,
                                                            dest_node=dest_node)
                source_node.link_identifications[source_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(forward_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (source_node.node_id, dest_node.node_id)] = forward_identifier
                current_link_identification = len(self.lir_link_identifiers)
                reverse_identifier = llim.LiRIdentification(link_identification_id=current_link_identification,
                                                            source_node=dest_node,
                                                            source_interface_index=dest_interface_index,
                                                            dest_node=source_node)
                dest_node.link_identifications[dest_node.interface_index] = current_link_identification
                self.lir_link_identifiers.append(reverse_identifier)
                self.map_from_source_dest_pair_to_link_identifier[
                    (dest_node.node_id, source_node.node_id)] = reverse_identifier
                # ---------------------------------- 进行正向和反向的两个链路标识的生成 ----------------------------------
                self.satellites[source_index].interface_index += 1
                self.satellites[dest_index].interface_index += 1
                self.satellite_links_without_direction.append(link_tmp)
        # ----------------------- 如果是 walker delta 星座还需要额外的一步 [连接首尾轨道] -----------------------

    # 进行 chainmaker.yml 的修改
    def modify_nodes_chainmaker_yml(self):
        """
        修改 multi_node/config/node*/chainmaker.yml 文件
        """
        path_of_multi_node_config = f"{self.config_reader.abs_of_multi_node}/config"
        if self.config_reader.node_type == em.EntityType.CONSENSUS_NODE:
            for satellite in self.satellites:
                new_seeds = []
                full_path_of_chainmaker_yml = f"{path_of_multi_node_config}/node{satellite.node_id + 1}/chainmaker.yml"
                with open(full_path_of_chainmaker_yml, "r") as f:
                    full_text = f.read()
                with open(full_path_of_chainmaker_yml, "w") as f:
                    start_index = full_text.find("seeds:") + 7
                    end_index = full_text.find("# Network tls settings") - 4
                    front_part = full_text[:start_index]
                    front_part = front_part.replace("listen_addr: /ip4/0.0.0.0/tcp/",
                                                    f"listen_addr: /ip4/{satellite.ip_addresses[0][:-3]}/tcp/")
                    end_part = full_text[end_index:]
                    seeds = full_text[start_index:end_index].split("\n")
                    for index, seed in enumerate(seeds):
                        new_seed = seed.replace("10.134.148.77", self.satellites[index].ip_addresses[0][:-3])
                        new_seeds.append(new_seed)
                    middle_part = "\n".join(new_seeds)
                    final_text = front_part + middle_part + end_part
                    f.write(final_text)

    # 展示相关
    # ------------------------------------------------------------

    def show_all_the_satellites(self) -> None:
        """
        展示所有的卫星
        :return None
        """
        for index, single_satellite in enumerate(self.satellites):
            print(f"[{index}] {str(single_satellite)}")

    def show_all_the_links_without_direction(self) -> None:
        """
        展示所有的无向链路
        :return None
        """
        for single_link_without_direction in self.satellite_links_without_direction:
            print(single_link_without_direction)

    def show_all_the_lir_link_identifications(self):
        """
        展示所有的 lir 链路标识
        :return: None
        """
        for single_lir_link_identification in self.lir_link_identifiers:
            print(single_lir_link_identification)

    def calculate_routes_with_all_nodes(self):
        """
        通过 networkx 计算路由, 注意这里需要计算的是
        """
        node_prefix = self.config_reader.node_prefix
        generate_destination = self.config_reader.abs_of_routes_configuration
        self.direction_graph = nx.DiGraph()
        node_ids = [single_satellite.node_id for single_satellite in self.satellites]
        link_identifiers = [(single_link_identifier.source_node.node_id, single_link_identifier.dest_node.node_id, 1)
                            for single_link_identifier
                            in self.lir_link_identifiers]
        self.direction_graph.add_nodes_from(node_ids)  # 进行节点的添加
        self.direction_graph.add_weighted_edges_from(link_identifiers)  # 进行链路标识的添加
        final_output_string = ""
        for single_node_id in node_ids:
            single_output_string = self.calculate_single_node_routes_to_other(single_node_id)
            final_output_string += single_output_string
            Constellation.write_routes_configuration_file(current_node_id=single_node_id,
                                                          generate_destination=generate_destination,
                                                          node_type=node_prefix,
                                                          file_content=single_output_string)
        # 所有的路由将会存放在另一个单独的文件之中
        Constellation.write_routes_configuration_file(current_node_id="all",
                                                      generate_destination=generate_destination,
                                                      node_type=node_prefix,
                                                      file_content=final_output_string)

    # ------------------------------------------------------------
    @classmethod
    def write_routes_configuration_file(cls, current_node_id, generate_destination, node_type, file_content):
        """
        将计算完成的图中任意两点的路径给存储好
        :param current_node_id 当前节点 id
        :param generate_destination:  生成的地址
        :param node_type: 节点的类型
        :param file_content: 文件的内容，也就是路由
        :return:
        """
        result_file_full_path = f"{generate_destination}/{node_type}_{current_node_id}.conf"
        with open(result_file_full_path, "w") as f:
            f.write(file_content)

    def calculate_single_node_routes_to_other(self, current_source_node):
        """
        计算从指定的源到其他节点的最短路径
        :param current_source_node: 当前节点的编号
        :return: 单个节点 (current_source_node) 到其他所有节点的最短路径
        """
        all_node_paths = {}
        all_identifier_paths = {}
        node_ids = [single_satellite.node_id for single_satellite in self.satellites]
        for node_id in node_ids:
            if node_id == current_source_node:
                continue
            else:
                path = nx.shortest_path(self.direction_graph, source=current_source_node, target=node_id)
                all_node_paths[node_id] = path
        # convert node path to link identifiers sequence
        for dest_node_id in all_node_paths.keys():
            identifier_path = []
            node_path = all_node_paths[dest_node_id]
            for index in range(len(node_path) - 1):
                source_dest_pair = (node_path[index], node_path[index + 1])
                identifier_path.append(
                    str(self.map_from_source_dest_pair_to_link_identifier[source_dest_pair].link_identification_id))
            all_identifier_paths[dest_node_id] = identifier_path
        final_writing_text = ""
        for dest_node_id in all_identifier_paths.keys():
            node_sequence_to_dest = all_node_paths[dest_node_id][1:]  # 到目的节点的节点序列
            identifier_sequence_to_dest = all_identifier_paths[dest_node_id]  # 到目的节点的链路标识序列
            # print(f"dest: {dest_node_id} node sequence: {all_node_paths[dest_node_id][1:]} identifier sequence {all_identifier_paths[dest_node_id]}")
            sequence = "->".join(all_identifier_paths[dest_node_id])
            new_sequence = ""
            for index in range(len(identifier_sequence_to_dest)):
                if index != len(identifier_sequence_to_dest) - 1:
                    new_sequence += (f"{identifier_sequence_to_dest[index]}->"
                                     f"{node_sequence_to_dest[index]}->")
                else:
                    new_sequence += (f"{identifier_sequence_to_dest[index]}->"
                                     f"{node_sequence_to_dest[index]}")
            single_path_str = f"source:{current_source_node} dest:{dest_node_id} {new_sequence}\n"
            final_writing_text += single_path_str
        return final_writing_text


if __name__ == "__main__":
    orbit_number_tmp = 1
    sat_per_orbit_tmp = 10
    docker_client_config = crm.ConfigReader("../resources/constellation_config.yml")
    constellation = Constellation(config_reader=docker_client_config)
    constellation.generate_satellites_and_tle()
    constellation.generate_isls_without_direction()
    constellation.show_all_the_satellites()
    constellation.show_all_the_links_without_direction()
    constellation.show_all_the_lir_link_identifications()
    constellation.calculate_routes_with_all_nodes()
