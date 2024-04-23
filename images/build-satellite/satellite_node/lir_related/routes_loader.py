import os
from netlink_client import netlink_client as ncm


class RoutesLoader:
    def __init__(self, path_of_routes_configuration_file):
        """
        加载 LiR 路由条目的加载器
        :param path_of_routes_configuration_file: LiR 路由的存储文件
        """
        self.path_of_routes_configuration_file = path_of_routes_configuration_file
        self.routing_table = {}
        self.netlink_client = ncm.NetlinkClient()

    def load_lir_routes(self):
        """
        将 LiR 路由加载进来
        :return:
        """
        with open(self.path_of_routes_configuration_file) as f:
            all_lines = f.readlines()
        for single_line in all_lines:
            source_node_id, destination_node_id, link_identifiers = self.analyze_single_line(single_line)
            if source_node_id not in self.routing_table.keys():
                self.routing_table[source_node_id] = {}
                self.routing_table[source_node_id][destination_node_id] = link_identifiers
            else:
                self.routing_table[source_node_id][destination_node_id] = link_identifiers

    def analyze_single_line(self, single_line):
        """
        进行 LiR 路由文件单行内容的加载
        :return: 源节点id 目的节点id 链路标识序列
        """
        # 进行源节点的 id 的提取
        start_index_of_source = single_line.find("source:") + 7
        end_index_of_source = single_line.find(" ", start_index_of_source)
        source_node_id = int(single_line[start_index_of_source:end_index_of_source])
        # 进行目的节点的 id 进行提取
        start_index_of_dest = single_line.find("dest:") + 5
        end_index_of_dest = single_line.find(" ", start_index_of_dest)
        destination_node_id = int(single_line[start_index_of_dest:end_index_of_dest])
        # 获取链路序列
        # 找到到目的节点的完整的序列
        remain_part = single_line[end_index_of_dest + 1:]
        # 进行所有的链路标识的查找
        sequence_identifiers = [int(item) for item in remain_part.split("->")]
        # 将提取到的三段内容进行返回
        return source_node_id, destination_node_id, sequence_identifiers

    def print_routing_table(self):
        """
        将 load 完成的路由表打印出来
        :return:
        """
        print(self.routing_table, flush=True)

    def insert_route(self, source, destination):
        """
        进行路由的插入
        :param source: 源节点
        :param destination: 目的节点
        :return:
        """
        # source_node_id, destination_node_id, length_of_path, sequence_identifiers
        # find corresponding route
        link_identifiers = self.routing_table[source][destination]
        link_identifier_str = ""
        for index, link_identifier in enumerate(link_identifiers):
            if index != len(link_identifiers) - 1:
                link_identifier_str += str(link_identifier) + ","
            else:
                link_identifier_str += str(link_identifier)
        send_str = f"{source},{destination},{len(link_identifiers)/2},{link_identifier_str}"
        print(send_str, flush=True)
        self.netlink_client.send_netlink_data(data=send_str,
                                              message_type=ncm.NetlinkMessageType.CMD_INSERT_ROUTES)

    def test(self):
        """
        进行测试
        :return:
        """
        self.load_lir_routes()
        self.print_routing_table()


if __name__ == "__main__":
    routes_loader = RoutesLoader(
        path_of_routes_configuration_file=f"/configuration/routes/{os.getenv('NODE_TYPE')}_all.conf")
    routes_loader.test()
