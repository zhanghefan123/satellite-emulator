import time
import socket
from PyInquirer import prompt
from interact_module import questions as qm


class IpUdpHandler:
    def __init__(self, ip_address_mapping, destination_port):
        """
        初始化 ip udp 处理器
        :param ip_address_mapping: 目的节点编号 ---> 目的节点 ip
        :param destination_port: 目的端口
        """
        self.ip_address_mapping = ip_address_mapping
        self.destination_port = destination_port
        self.handle_unicast()

    def handle_unicast(self):
        """
        处理 ip unicast
        :return:
        """
        # 让用户选择单个目的卫星
        selected_destination_node_id = self.select_destination_node()
        # 根据用户选择的单个目的卫星进行 ip 地址的获取
        selected_destination_ip = self.ip_address_mapping[selected_destination_node_id][0]
        selected_destination_ip = selected_destination_ip[:selected_destination_ip.find("/")]
        # 构造 socket 进行发送
        unicast_udp_socket = self.create_socket_and_set_opt()
        # 进行消息的发送
        self.send_data(unicast_udp_socket, selected_destination_ip)

    def select_destination_node(self):
        """
        选择单颗目的卫星
        :return: 选择好的卫星的编号
        """
        question_for_destination_node = qm.QUESTION_FOR_DESTINATION
        question_for_destination_node[0]["choices"] = list(self.ip_address_mapping.keys())
        selected_destination_node_str = prompt(question_for_destination_node)["destination"]
        return selected_destination_node_str

    def create_socket_and_set_opt(self):
        """
        创建 socket 并设置好选项
        :return: 创建好的并且设置好选项的 udp_socket
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        size_of_bf = 5
        first_eight_bytes = [0x94, 0x28, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1]
        byte_array = bytearray(first_eight_bytes * size_of_bf)
        # udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        return udp_socket

    def send_data(self, udp_socket, destination_ip_address):
        """
        利用创建好的 socket 进行消息的发送
        :param udp_socket: 创建好的 socket
        :param destination_ip_address: 目的节点 ip
        :return:
        """
        while True:
            message = input("please input message: ")
            if message == "time":
                current_time = time.time()
                message = f"time:{current_time}"
                udp_socket.sendto(message.encode(), (destination_ip_address, self.destination_port))
            elif message == "test":
                self.test_end_to_end_delay(udp_socket, destination_ip_address)
            else:
                udp_socket.sendto(message.encode(), (destination_ip_address, self.destination_port))

    def test_end_to_end_delay(self, udp_socket, destination_ip_address):
        """
        进行性能测试
        :return:
        """
        packet_count = int(prompt(qm.QUESTION_FOR_PACKET_COUNT)["count"])
        send_interval = float(prompt(qm.QUESTION_FOR_INTERVAL)["interval"])
        for index in range(packet_count):
            current_time = time.time()
            message = f"calc_time:{current_time}"
            udp_socket.sendto(message.encode(), (destination_ip_address, self.destination_port))
            time.sleep(send_interval)
        message = "exit"
        udp_socket.sendto(message.encode(), (destination_ip_address, self.destination_port))
