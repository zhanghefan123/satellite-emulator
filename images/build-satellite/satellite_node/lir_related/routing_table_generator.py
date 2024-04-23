import os
from netlink_client import netlink_client as ncm


class RoutingTableGenerator:
    def __init__(self, path_of_routes_configurations_file: str, netlink_client: ncm.NetlinkClient):
        """
        进行路由表的初始化
        :param path_of_routes_configurations_file 存储路由的文件
        :parm netlink_client: netlink 用户空间客户端
        """
        self.path_of_routes_configuration_file = path_of_routes_configurations_file
        self.netlink_client = netlink_client

    def read_routes_and_insert_into_kernel(self):
        """
        从文件之中进行路由信息的读取，并插入到内核之中形成路由表
        :return:
        """
        with open(self.path_of_routes_configuration_file, "r") as f:
            all_lines = f.readlines()
        # 接下来需要进行分析
        total_str = ""
        for single_line in all_lines:
            start_index_of_source = single_line.find("source:") + 7
            end_index_of_source = single_line.find(" ", start_index_of_source)
            source_node_id = int(single_line[start_index_of_source:end_index_of_source])
            # 将目的节点的 id 进行提取
            start_index_of_dest = single_line.find("dest:") + 5
            end_index_of_dest = single_line.find(" ", start_index_of_dest)
            destination_node_id = int(single_line[start_index_of_dest:end_index_of_dest])
            # 找到到目的节点的完整的序列
            remain_part = single_line[end_index_of_dest + 1:]
            # 进行所有的链路标识的查找
            sequence_identifiers = [int(item) for item in remain_part.split("->")]
            send_to_kernel_data = f"{source_node_id},"
            send_to_kernel_data += f"{destination_node_id},"
            send_to_kernel_data += f"{len(sequence_identifiers)/2},"
            for index, identifier in enumerate(sequence_identifiers):
                if index != len(sequence_identifiers) - 1:
                    send_to_kernel_data += f"{str(identifier)},"
                else:
                    send_to_kernel_data += str(identifier)
            send_to_kernel_data += "\n"
            total_str += send_to_kernel_data
        total_str.rstrip("\n")
        print(total_str, flush=True)
        self.netlink_client.send_netlink_data(total_str,
                                              message_type=ncm.NetlinkMessageType.CMD_INSERT_ROUTES)

    def start(self):
        """
        开启在内核之中的路由表生成
        :return:
        """
        self.read_routes_and_insert_into_kernel()