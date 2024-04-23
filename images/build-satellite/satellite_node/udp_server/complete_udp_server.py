if __name__ == "__main__":
    import sys

    sys.path.append("../")
import time
import socket
from PyInquirer import prompt
from interact_module import questions as qm


class CompleteUdpServer:
    def __init__(self):
        """
        初始化函数
        """
        self.selected_port = None
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.get_port()
        self.bind_and_receive_data()

    def get_port(self):
        """
        获取目的端口
        :return:
        """
        answers_for_port = prompt(qm.QUESTION_FOR_SERVER_LISTEN_PORT)
        self.selected_port = int(answers_for_port["port"])

    def bind_and_receive_data(self):
        all_interface_address = "0.0.0.0"
        self.udp_socket.bind((all_interface_address, self.selected_port))
        total = 0
        while True:
            data, address = self.udp_socket.recvfrom(1024)
            end = time.time()
            data = data.decode()
            if data.startswith("time:"):
                _, time_data = data.split(":")
                start = float(time_data)
                print(f"{(end - start) * 1000 * 1000}微秒", flush=True)
            elif data.startswith("calc_time"):
                _, time_data = data.split(":")
                start = float(time_data)
                total += (end - start) * 1000 * 1000
            elif data == "exit":
                print(f"total {total} 微秒", flush=True)
                break
            else:
                print(data, flush=True)


if __name__ == "__main__":
    complete_udp_server = CompleteUdpServer()
