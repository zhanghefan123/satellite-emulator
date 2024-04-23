import os
import time
import threading
from satellite_node_decorator import signal_decorator as sdm
from satellite_node_useful_tools import logger as lm
from command_server import command_server_unit as csu
from satellite_node_useful_tools import envs_reader as erm
from netlink_client import netlink_client as ncm
from lir_related import new_interface_table_generator as nitgm
from lir_related import routing_table_generator as rtgm
from lir_related import net_to_id_mapper as ntimm


class Starter:
    def __init__(self):
        """
        进行唯一的 logger 的创建
        """
        self.logger = lm.Logger().get_logger()
        self.envs_reader = erm.EnvsReader()
        if os.getenv("LIR_ENABLED") == "1":
            self.netlink_userspace_client = ncm.NetlinkClient()
        else:
            self.netlink_userspace_client = None
        self.server = csu.CommandServerUnit(listening_port=self.envs_reader.listening_port,
                                            my_logger=self.logger,
                                            netlink_client=self.netlink_userspace_client,
                                            starter=self)
        # ---------------------------------------- lir 相关的代码 ----------------------------------------
        self.new_interface_table_generator = nitgm.NewInterfaceTableGenerator(
            path_of_name_to_lid_file=f"/configuration/lir/{os.getenv('NODE_TYPE')}_{os.getenv('NODE_ID')}.conf",
            netlink_client=self.netlink_userspace_client)
        self.routing_table_generator = rtgm.RoutingTableGenerator(
            path_of_routes_configurations_file=f"/configuration/routes/{os.getenv('NODE_TYPE')}_{os.getenv('NODE_ID')}.conf",
            netlink_client=self.netlink_userspace_client
        )
        self.net_to_id_mapper = ntimm.NetToIdMapper(
            netlink_client=self.netlink_userspace_client
        )
        # ---------------------------------------- lir 相关的代码 ----------------------------------------

    def start_server_as_a_thread(self):
        """
        开启服务器守护子线程，如果主线程 down 了，这个子线程跟着一起 down
        :return:
        """
        server_thread = threading.Thread(target=self.server.listen_at_docker_zero_address)
        server_thread.setDaemon(True)
        server_thread.start()

    @sdm.signal_decorator
    def never_stop_until_signal(self):
        """
        主线程，只有当收到了 signal 的时候 才会结束，否则反复进行睡觉。
        :return:
        """
        while True:
            time.sleep(60)

    def start_frr(self):
        """
        将文件复制到指定的位置，并调用命令 service frr start
        :return:
        """
        if os.getenv("START_FRR") == "1":
            print("START FRR", flush=True)
            frr_configuration_file_source = f"/configuration/frr/{os.getenv('NODE_TYPE')}_{os.getenv('NODE_ID')}.conf"
            frr_configuration_file_dest = f"/etc/frr/frr.conf"
            copy_command = f"cp {frr_configuration_file_source} {frr_configuration_file_dest}"
            start_frr_command = "service frr start"
            os.system(copy_command)
            os.system(start_frr_command)
        else:
            print("NOT START FRR", flush=True)

    def delete_default_route(self):
        """
        进行默认路由的删除
        :return:
        """
        delete_default_route_command = "ip route del default"
        os.system(delete_default_route_command)

    def main_logic(self):
        """
        主逻辑：容器节点只需要调用这一个方法即可。
        :return:
        """
        # 开启服务器子线程
        try:
            # 1.启动服务器
            self.start_server_as_a_thread()
            # 2.为模拟拓扑新增的代码
            # ------------------------------
            self.start_frr()
            # 3. 删除默认路由
            # self.delete_default_route()
            # ------------------------------
            # 4.主线程
            self.never_stop_until_signal()
        except Exception as e:
            self.logger.error(e)


if __name__ == "__main__":
    starter = Starter()
    starter.main_logic()
