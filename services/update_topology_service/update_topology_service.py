import pika
import json
from config import config_reader as crm
from typing import List
from entities import normal_link as nlm
from useful_tools import multithread_executor as mem
from multiprocessing import Queue
import os


class UpdateTopologyService:
    def __init__(self, config_reader: crm.ConfigReader, links: List[nlm.NormalLink], stop_queue: Queue):
        self.links = links
        self.update_queue_name = config_reader.update_queue_name
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=config_reader.network_ip_address))
        self.channel = self.connection.channel()
        self.quit_message = "quit"
        self.delay_map = {}
        self.connection_map = {}
        self.init = True
        self.multithread_executor_temp = mem.MultithreadExecutor(max_workers=50)
        self.stop_queue = stop_queue

    def start(self):
        self.channel.queue_declare(queue=self.update_queue_name)
        for message in self.channel.consume(queue=self.update_queue_name, auto_ack=True):
            method, properties, body_in_bytes = message
            if body_in_bytes.decode("utf-8") == "quit":
                break
            else:
                self.delay_map = json.loads(body_in_bytes)
                self.update_with_linux_tc()

    def enable_or_disable_link(self):
        """
        进行链路的更新,先不考虑星间链路的更新状况，只考虑星地链路
        我们知道两个端点之后，可以按照 generate_veth_pair_for_single_link 进行生成
        可以让卫星提前产生四个接口
        satA <------> bridge1
        satA <------> bridge2
        ip link add {veth1_satA} type veth peer name {veth bridge1} # 创建一对虚拟网卡  从卫星到网桥
        ip link add {veth2_gndA} type veth peer name {veth bridge2} # 创建一对虚拟网卡  从地面站到网桥
        ip link set {veth1_satA} netns {pid_of_satA} 设置卫星一侧网卡的命名空间
        # -------------------------- 一旦出现新的地面站要连接  --------------------------
        ip link set {veth2_gndA} netns {pid_of_gndA} 设置地面站一侧网卡的命名空间
        ip link set {veth2_gndA} netns {pid_of_gndA} 设置
        # -------------------------- 一旦出现新的地面站要连接  --------------------------
        :return:
        """

        pass

    def update_single_link_by_tc(self, link: nlm.NormalLink):
        first_veth_name = f"sa{link.source_node.node_id}_index{link.source_interface_index + 1}"
        second_veth_name = f"sa{link.dest_node.node_id}_index{link.dest_interface_index + 1}"
        first_sat_pid = link.source_node.pid
        second_sat_pid = link.dest_node.pid
        current_delay_of_this_link = self.delay_map[str(link.link_id)]
        if self.init:
            first_tc_command_for_veth_first = f"ip netns exec {first_sat_pid} tc qdisc replace dev {first_veth_name} root handle 1:0 tbf rate {100}kbit burst {100}k limit {100}kbit"
            second_tc_command_for_veth_first = f"ip netns exec {first_sat_pid} tc qdisc add dev {first_veth_name} parent 1:0 handle 2:0 netem delay {current_delay_of_this_link}ms"
            first_tc_command_for_veth_second = f"ip netns exec {second_sat_pid} tc qdisc replace dev {second_veth_name} root handle 1:0 tbf rate {100}kbit burst {100}k limit {100}kbit"
            second_tc_command_for_veth_second = f"ip netns exec {second_sat_pid} tc qdisc add dev {second_veth_name} parent 1:0 handle 2:0 netem delay {current_delay_of_this_link}ms"
        else:
            first_tc_command_for_veth_first = None
            second_tc_command_for_veth_first = f"ip netns exec {first_sat_pid} tc qdisc replace dev {first_veth_name} parent 1:0 handle 2:0 netem delay {current_delay_of_this_link}ms"
            first_tc_command_for_veth_second = None
            second_tc_command_for_veth_second = f"ip netns exec {second_sat_pid} tc qdisc replace dev {second_veth_name} parent 1:0 handle 2:0 netem delay {current_delay_of_this_link}ms"
        # 进行调用
        if self.stop_queue.empty():
            try:
                if self.init:
                    os.system(first_tc_command_for_veth_first)
                    os.system(second_tc_command_for_veth_first)
                    os.system(first_tc_command_for_veth_second)
                    os.system(second_tc_command_for_veth_second)
                else:
                    os.system(second_tc_command_for_veth_first)
                    os.system(second_tc_command_for_veth_second)
            except Exception:
                pass
        else:
            pass

    def update_with_linux_tc(self):
        tasks = []
        args = []
        for link in self.links:
            tasks.append(self.update_single_link_by_tc)  # 进行 tc 更新
            args.append((link,))
        self.multithread_executor_temp.execute_with_multiple_thread(task_list=tasks, args_list=args, description="update delay", enable_tqdm=False)
        if self.init:
            self.init = False
