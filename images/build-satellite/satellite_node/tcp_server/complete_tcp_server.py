if __name__ == "__main__":
    import sys

    sys.path.append("../")
import os
import socket
import threading
from loguru import logger
from PyInquirer import prompt
from config_sat import const_var as cvm
from interact_module import questions as qm


class CompleteTcpServer:
    def __init__(self, listening_address, listening_port):
        self.listening_address = listening_address
        self.listening_port = listening_port
        self.server_socket = None
        self.socket_address = (self.listening_address, self.listening_port)
        self.BUFFER_SIZE = 1024

    def start(self):
        try:
            # create tcp server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # set option field in tcp server
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
            # set option field in tcp server
            size_of_bf = 5
            first_eight_bytes = [0x94, 0x28] + [int(os.getenv("NODE_ID"))] + [0x1] * (8 - 3)
            byte_array = bytearray(first_eight_bytes * size_of_bf)
            self.server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
            # bind the socket to the socket address
            self.server_socket.bind(self.socket_address)
            # listen for client connections
            self.server_socket.listen()
            # accept for connections
            while True:
                client_socket, client_address = self.server_socket.accept()
                # set option field in tcp server
                size_of_bf = 5
                first_eight_bytes = [0x94, 0x28] + [int(os.getenv("NODE_ID"))] + [0x1] * (8 - 3)
                byte_array = bytearray(first_eight_bytes * size_of_bf)
                client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
                # set the flag
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
                logger.success(f"received connection from {client_address}")
                thread = threading.Thread(target=self.handle_single_client, args=(client_socket,))
                thread.start()
        except KeyboardInterrupt:
            self.server_socket.close()
            logger.success("tcp server exit successfully")

    def handle_single_client(self, client_socket:socket.socket):
        while True:
            try:
                data = client_socket.recv(self.BUFFER_SIZE)
                if not data:
                    raise Exception("client quit")
                data_str = data.decode("utf-8")
                logger.success(f"received from client {client_socket.getsockname()}:{str(data_str)}")
            except Exception as e:
                client_socket.close()
                logger.error("client quit")
                break


if __name__ == "__main__":
    # question for the listening port
    listening_port_selected = int(prompt(qm.QUESTION_FOR_SERVER_LISTEN_PORT)["port"])
    complete_tcp_server = CompleteTcpServer(cvm.INADDR_ANY, listening_port_selected)
    complete_tcp_server.start()
