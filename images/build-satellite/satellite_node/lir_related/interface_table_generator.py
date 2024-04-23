import socket
import time
from netlink_client import netlink_client as ncm


class InterfaceTableGenerator:
    def __init__(self, path_of_name_to_lid_file: str, netlink_client: ncm.NetlinkClient):
        """
        进行接口表的初始化
        :param path_of_name_to_lid_file: 从接口名称到接口对应的链路标识的映射
        :param netlink_client: netlink 客户端
        """
        self.name_to_lid_map = {}
        self.path_of_name_to_lid = path_of_name_to_lid_file  # 从接口名称到 link_identifier 的 mapping
        self.netlink_client = netlink_client  # 用来向内核进行消息的发送
        self.interface_name_to_ifindex = {}  # 从接口名称到 ifindex 的映射

    def load_name_to_lid_file(self):
        """
        将配置文件进行加载
        :return:
        """
        with open(self.path_of_name_to_lid) as f:
            all_lines = f.readlines()
        for single_line in all_lines:
            interface_name, link_identifier = single_line.split("->")
            self.name_to_lid_map[interface_name] = link_identifier.rstrip("\n")  # 右侧存在一个 "\n" 需要去掉

    def get_available_interfaces(self):
        """
        获取可用的从 interface_name -> ifindex 的映射
        :return:
        """
        available_interfaces = socket.if_nameindex()
        self.interface_name_to_ifindex = {item[1]: item[0] for item in available_interfaces}

    def check_network_interface(self):
        """
        每隔一段时间将调用这个函数，用来判断某个接口是否启动起来了。
        :return: 如果所有的接口都是存在的话，那么返回0，如果有接口不存在那么返回-1
        """
        self.get_available_interfaces()
        available_interface_names = [item for item in self.interface_name_to_ifindex.keys()]
        for name in self.name_to_lid_map.keys():
            if name not in available_interface_names:
                return -1
            else:
                pass
        return 0

    def construct_kernel_interface_table(self):
        """
        进行内核的接口表的构建
        :return:
        """
        while True:
            if 0 == self.check_network_interface():
                break
            else:
                time.sleep(1)
        # 进行 名称 -> 链路标识的映射的遍历
        final_str = ""
        for interface_name in self.name_to_lid_map.keys():
            final_str += f"{self.name_to_lid_map[interface_name]},{self.interface_name_to_ifindex[interface_name]}\n"
        print(final_str, flush=True)
        self.netlink_client.send_netlink_data(final_str, ncm.NetlinkMessageType.CMD_CONSTRUCT_INTERFACE_TABLE)

    def start(self):
        """
        开启生成的流程
        :return:
        """
        self.load_name_to_lid_file()  # 加载从 name->lid 的文件
        self.get_available_interfaces()  # 创建从接口名称到 ifindex 的映射
        self.construct_kernel_interface_table()  # 在内核之中进行接口表的创建
