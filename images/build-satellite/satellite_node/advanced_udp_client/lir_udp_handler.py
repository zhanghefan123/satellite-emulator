from interact_module import different_types as dtm
from interact_module import questions as qm
from PyInquirer import prompt
from lir_related import routes_loader as rlm
import socket
import time
import os


class LirUdpHandler:
    def __init__(self, destination_node_list, destination_port):
        """
        初始化 lir udp 处理器
        :param destination_node_list: 目的节点列表
        :param destination_port: 目的端口
        """
        self.destination_node_list = destination_node_list
        self.destination_port = destination_port
        self.transmission_pattern = None
        self.lir_routes_loader = rlm.RoutesLoader(path_of_routes_configuration_file=f"/configuration/routes/{os.getenv('NODE_TYPE')}_all.conf")
        self.lir_routes_loader.load_lir_routes()
        self.get_transmission_pattern()
        self.handle_different_transmission_pattern()

    def get_transmission_pattern(self):
        """
        进行传输协议的获取
        :return:
        """
        answers_for_transmission_pattern = prompt(qm.QUESTION_FOR_LIR_TRANSMISSION_PATTERN)["transmission_pattern"]
        if answers_for_transmission_pattern == "unicast":
            self.transmission_pattern = dtm.TransmissionPattern.UNICAST
        elif answers_for_transmission_pattern == "multicast":
            self.transmission_pattern = dtm.TransmissionPattern.MULTICAST
        else:
            raise ValueError("unexpected transmission pattern")

    def handle_different_transmission_pattern(self):
        """
        进行不同传输协议的处理
        :return:
        """
        if self.transmission_pattern == dtm.TransmissionPattern.UNICAST:
            self.handle_unicast()
        elif self.transmission_pattern == dtm.TransmissionPattern.MULTICAST:
            self.handle_multicast()
        else:
            raise ValueError("unexpected transmission pattern")

    def handle_unicast(self):
        """
        处理 lir unicast
        :return:
        """
        # 让用户选择单个目的卫星
        selected_destination_node_id = self.select_destination_node()
        # 创建 unicast socket 并设置好选项
        unicast_udp_socket = self.create_socket_and_set_opt([selected_destination_node_id])
        # 准备进行消息的发送
        self.send_data(unicast_udp_socket, [selected_destination_node_id] * 4)

    def handle_multicast(self):
        """
        处理 lir multicast
        :return:
        """
        # 进行目的节点列表的选择
        destination_node_list = self.select_destination_node_ids()
        # 需要进行路由条目的插入
        self.insert_multicast_corresponding_routes(destination_node_list)
        # 创建 multicast socket 并设置好选项
        multicast_udp_socket = self.create_socket_and_set_opt(destination_node_list)
        # 准备进行消息的发送
        if len(destination_node_list) != 4:
            destination_node_list = destination_node_list + [250] * (4 - len(destination_node_list))
        self.send_data(multicast_udp_socket, destination_node_list)

    def insert_multicast_corresponding_routes(self, destination_node_list):
        """
        进行多播相关的路由的插入 [假设目的节点是 B,C,D, 源节点是 A], 那么我们需要插入
        A->B B->C B->D
        :return:
        """
        primary_node = destination_node_list[0]
        for index in range(1, len(destination_node_list)):
            destination_node = destination_node_list[index]
            self.lir_routes_loader.insert_route(source=primary_node, destination=destination_node)

    def select_destination_node(self):
        """
        选择单颗目的卫星
        :return: 选择好的卫星的编号
        """
        question_for_destination_node = qm.QUESTION_FOR_DESTINATION
        question_for_destination_node[0]["choices"] = self.destination_node_list
        selected_destination_node_str = prompt(question_for_destination_node)["destination"]
        selected_destination_node_id = int(
            selected_destination_node_str[selected_destination_node_str.find("sat") + 3:])
        return selected_destination_node_id

    def select_destination_node_ids(self):
        """
        进行目的节点列表的选择
        :return:
        """
        count = int(prompt(qm.QUESTION_FOR_NUMBER_OF_DESTINATION)["count"])
        destination_node_list = []
        for index in range(count):
            current_destination_id = self.select_destination_node()
            destination_node_list.append(current_destination_id)
        return destination_node_list

    def create_socket_and_set_opt(self, destination_node_id_list):
        """
        创建 socket 并设置好选项
        :param destination_node_id_list 目的节点 id 列表
        :return:
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        size_of_bf = 5
        number_of_dest = len(destination_node_id_list)
        # original code when OPTION_START_INDEX = 2
        # first_eight_bytes = [0x94, 0x28] + [number_of_dest] + destination_node_id_list + [0x1] * (8 - 3 - number_of_dest)
        # current code when OPTIONS_START_INDEX = 3
        first_eight_bytes = [0x94, 0x28] + [int(os.getenv("NODE_ID"))] + [number_of_dest] + destination_node_id_list + [0x0] * (
                    8 - 4 - number_of_dest)
        remained_thirty_two_bytes = [0x0] * 32
        byte_array = bytearray(first_eight_bytes + remained_thirty_two_bytes)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        return udp_socket

    def send_data(self, udp_socket, destination_node_id_list):
        """
        利用创建好的 socket 进行消息的发送
        :param udp_socket: 创建好的 udp_socket, 可能是 unicast 也可能是 mutlicast
        :param destination_node_id_list: 目的节点id列表
        :return:
        """
        destination_node_id_list = [str(item) for item in destination_node_id_list]
        lir_destination_address = ".".join(destination_node_id_list)
        while True:
            message = input("please input message: ")
            if message == "time":
                current_time = time.time()
                message = f"time:{current_time}"
                udp_socket.sendto(message.encode(), (lir_destination_address, self.destination_port))
            elif message == "test":
                self.test_end_to_end_delay(udp_socket, lir_destination_address)
            else:
                udp_socket.sendto(message.encode(), (lir_destination_address, self.destination_port))

    def test_end_to_end_delay(self, udp_socket, lir_destination_address):
        """
        进行性能测试
        :return:
        """
        packet_count = int(prompt(qm.QUESTION_FOR_PACKET_COUNT)["count"])
        send_interval = float(prompt(qm.QUESTION_FOR_INTERVAL)["interval"])
        for index in range(packet_count):
            current_time = time.time()
            message = f"calc_time:{current_time}"
            udp_socket.sendto(message.encode(), (lir_destination_address, self.destination_port))
            time.sleep(send_interval)
        message = "exit"
        udp_socket.sendto(message.encode(), (lir_destination_address, self.destination_port))
