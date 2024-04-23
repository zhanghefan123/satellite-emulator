if __name__ == "__main__":
    import sys

    sys.path.append("../")
import time
import socket
from PyInquirer import prompt
from interact_module import questions as qm
from interact_module import different_types as dtm
from advanced_udp_client import lir_udp_handler as luhm
from advanced_udp_client import ip_udp_handler as iuhm


class AdvancedCompleteUdpClient:
    def __init__(self):
        """
        初始化函数
        """
        self.selected_protocol = None
        self.selected_ip_address = None
        self.destination_port = None
        self.ip_mapping_file = "/configuration/address/address_mapping.conf"
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip_address_mapping = {}  # 从节点 id 到 ip 地址序列的一个映射
        self.selected_satellite_id = None
        self.read_address_mapping()
        self.get_port()
        self.get_protocol()
        if self.selected_protocol == dtm.Protocol.IP:
            self.handle_ip_protocol_selection()
        elif self.selected_protocol == dtm.Protocol.LIR:
            self.handle_lir_protocol_selection()

    def handle_ip_protocol_selection(self):
        """
        选择 ip 协议后对应的处理
        :return:
        """
        ip_udp_handler = iuhm.IpUdpHandler(ip_address_mapping=self.ip_address_mapping,
                                           destination_port=self.destination_port)

    def handle_lir_protocol_selection(self):
        """
        选择 lir 协议后对应的处理
        :return:
        """
        destination_node_list = [item for item in self.ip_address_mapping.keys()]
        lir_udp_handler = luhm.LirUdpHandler(destination_node_list=destination_node_list,
                                             destination_port=self.destination_port)

    def get_protocol(self):
        """
        进行用户选择的获取
        """
        answers_for_protocol = prompt(qm.QUESTION_FOR_PROTOCOL)
        if answers_for_protocol["protocol"] == "IP":
            self.selected_protocol = dtm.Protocol.IP
        elif answers_for_protocol["protocol"] == "LIR":
            self.selected_protocol = dtm.Protocol.LIR
        else:
            raise ValueError("unsupported protocol")

    def get_port(self):
        """
        获取目的端口
        :return:
        """
        answers_for_port = prompt(qm.QUESTION_FOR_DESTINATION_PORT)
        self.destination_port = int(answers_for_port["port"])

    def read_address_mapping(self):
        """
        进行 ip 地址映射的读取
        :return:
        """
        delimiter = "|"
        with open(self.ip_mapping_file, "r") as f:
            all_lines = f.readlines()
            for line in all_lines:
                # sat9|192.168.0.34/30|192.168.0.37/30
                items = line.split(delimiter)
                items[len(items) - 1] = items[len(items) - 1].rstrip("\n")
                self.ip_address_mapping[items[0]] = items[1:]

    def print_address_mapping(self):
        """
        进行 ip 地址映射的打印
        :return:
        """
        for item in self.ip_address_mapping.items():
            print(f"{item[0]}:{item[1]}", flush=True)


if __name__ == "__main__":
    complete_udp_client = AdvancedCompleteUdpClient()
