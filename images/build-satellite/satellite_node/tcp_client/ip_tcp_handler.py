from interact_module import questions as qm
from PyInquirer import prompt
from loguru import logger
import socket


class IpTcpHandler:
    def __init__(self, ip_address_mapping, destination_port):
        self.BUFFER_SIZE = 1024
        self.ip_address_mapping = ip_address_mapping
        self.destination_port = destination_port
        self.handle_unicast()

    def handle_unicast(self):
        # 选择目的 ip 地址
        selected_server_address = self.select_destination_ip()
        # 创建 tcp_socket 并设置选项
        tcp_client_socket = self.create_socket_and_set_opt()
        # 发送数据
        self.send_data(tcp_client_socket, selected_server_address)

    def create_socket_and_set_opt(self):
        """
        创建 tcp_socket 并设置选项
        :return:
        """
        tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        size_of_bf = 5
        first_eight_bytes = [0x94, 0x28, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1]
        byte_array = bytearray(first_eight_bytes * size_of_bf)
        tcp_client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        return tcp_client_socket

    def select_destination_ip(self):
        """
        选择单颗目的卫星
        :return: 选择好的卫星的编号对应的ip地址
        """
        question_for_destination_node = qm.QUESTION_FOR_DESTINATION
        question_for_destination_node[0]["choices"] = list(self.ip_address_mapping.keys())
        selected_destination_node_str = prompt(question_for_destination_node)["destination"]
        # 根据用户选择的单个目的卫星进行 ip 地址的获取
        selected_destination_ip = self.ip_address_mapping[selected_destination_node_str][0]
        selected_destination_ip = selected_destination_ip[:selected_destination_ip.find("/")]
        return selected_destination_ip

    def send_data(self, tcp_client_socket, destination_ip_address):
        # server socket address
        server_socket_address = (destination_ip_address, self.destination_port)
        # connect to the sever socket
        tcp_client_socket.connect(server_socket_address)
        # read the user input and send the message
        while True:
            # get message
            message = input("please input the message you want to send: (q to quit) ")
            if message != "q":
                # send message
                tcp_client_socket.send(message.encode("utf-8"))
            else:
                break
        tcp_client_socket.close()
