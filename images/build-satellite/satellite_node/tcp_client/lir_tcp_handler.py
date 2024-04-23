from interact_module import questions as qm
from PyInquirer import prompt
from loguru import logger
import socket
import os


class LirTcpHandler:
    def __init__(self, ip_address_mapping, destination_port):
        self.BUFFER_SIZE = 1024
        self.ip_address_mapping = ip_address_mapping
        self.destination_node_list = [item for item in ip_address_mapping.keys()]
        self.destination_port = destination_port
        self.handle_unicast()

    def handle_unicast(self):
        # 让用户选择单颗卫星 - 返回的是 id 而不是 satx
        selected_destination_node_str = self.select_destination_node()
        # 根据 id 找到对应的 ip 地址
        selected_ip_address = self.ip_address_mapping[selected_destination_node_str][0]
        selected_ip_address = selected_ip_address[:selected_ip_address.find("/")]
        # 找到 id
        selected_destination_node_id = int(
            selected_destination_node_str[selected_destination_node_str.find("sat") + 3:])
        # 创建 socket 并设置好选项
        tcp_client_socket = self.create_socket_and_set_opt(selected_destination_node_id)
        # 准备进行消息的发送
        self.send_data(tcp_client_socket, selected_ip_address)

    def select_destination_node(self):
        """
        选择单颗目的卫星
        :return: 选择好的卫星的编号
        """
        question_for_destination_node = qm.QUESTION_FOR_DESTINATION
        question_for_destination_node[0]["choices"] = self.destination_node_list
        selected_destination_node_str = prompt(question_for_destination_node)["destination"]
        return selected_destination_node_str

    def create_socket_and_set_opt(self, destination_node):
        """
        创建 socket 并设置好选项
        :param destination_node: 目的节点 id
        :return:
        """
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        size_of_bf = 5
        number_of_dest = 1
        # original code when OPTION_START_INDEX = 2
        # first_eight_bytes = [0x94, 0x28] + [number_of_dest] + destination_node_id_list + [0x1] * (8 - 3 - number_of_dest)
        # current code when OPTIONS_START_INDEX = 3
        first_eight_bytes = [0x94, 0x28] + [int(os.getenv("NODE_ID"))] + [number_of_dest] + [destination_node] + [
            0x1] * (8 - 4 - number_of_dest)
        byte_array = bytearray(first_eight_bytes * size_of_bf)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
        tcp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        return tcp_socket

    def send_data(self, tcp_client_socket, selected_ip_address):
        """
        利用创建好的 socket 进行消息的发送
        :param tcp_client_socket: tcp client socket
        :param selected_ip_address: 目的节点编号
        :return:
        """
        # # construct destination address
        # temp_addr = [str(destination_node_id)] * 4
        # # construct destination ip address
        # destination_ip_address = ".".join(temp_addr)
        # server socket address
        server_socket_address = (selected_ip_address, self.destination_port)
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
