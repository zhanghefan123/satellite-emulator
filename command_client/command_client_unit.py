import asyncio
import socket
import PyInquirer
from interact import questions as qm
from command_client import message_format as mfm
from useful_tools import progress_bar as pbm
from loguru import logger


class CommandClientUnit:

    def __init__(self, satellites, satellites_map, server_listen_port: int):
        """
        初始化可用的卫星的列表
        :param satellites: 可用的卫星列表
        :param satellites_map: 从 container_id 到 satellite
        :param server_listen_port: 服务器监听的端口
        """
        self.satellites = satellites
        self.satellites_map = satellites_map
        self.available_node_names = []
        self.name_to_id = None
        self.server_port = server_listen_port
        self.buffer_size = 1024

    def calculate_name_to_id(self):
        self.name_to_id = {satellite.container_name: satellite.container_id for satellite in self.satellites}

    def get_available_names(self):
        """
        手机所有可以发送消息的卫星的名称
        :return:
        """
        self.available_node_names = ["all_satellites"]
        for item in self.satellites:
            self.available_node_names.append(item.container_name)

    async def set_default_params_of_bloom_filter(self,
                                                 default_bloom_filter_length: int,
                                                 default_hash_seed: int,
                                                 default_number_of_hash_funcs: int):
        """
        进行布隆过滤器的默认的参数的设置
        :param default_bloom_filter_length 默认的布隆过滤器长度
        :param default_hash_seed 默认的hash种子大小
        :param default_number_of_hash_funcs 默认的哈希函数的个数
        :return:
        """
        self.get_available_names()
        self.calculate_name_to_id()
        all_tasks = []
        payload = f"{default_bloom_filter_length}|{default_hash_seed}|{default_number_of_hash_funcs}"
        message_type = mfm.CommandMessage.CommandType.INIT_COMMAND
        for index in range(1, len(self.available_node_names)):
            satellite_name = self.available_node_names[index]
            # 进行任务的创建
            task = asyncio.create_task(self.send_message_to_single_satellite_task(satellite_name=satellite_name,
                                                                                  payload=payload,
                                                                                  message_type=message_type))
            all_tasks.append(task)
        await pbm.ProgressBar.wait_tasks_with_tqdm(all_tasks, description="set bf process")
        # 进行所有任务的遍历并输出结果
        for finished_single_task in all_tasks:
            finished_single_task_result = finished_single_task.result()
            print(finished_single_task_result, flush=True)

    def interact_with_user(self):
        """
        询问用户是否还需要进行信息的发送
        :return:
        """
        # 进行问题的修改 - 修改可选的卫星的列表
        node_selection_question = qm.NODE_SELECTION_QUESTION
        node_selection_question[0]["choices"] = self.available_node_names
        # 进行提问 - 进行某一颗节点的选择
        answers_for_node_selection = PyInquirer.prompt(node_selection_question)
        # 进行用户选择的节点的获取
        user_select_node = answers_for_node_selection["node"]
        # 进行用户选择的判断
        if user_select_node in self.available_node_names:
            logger.success(f"available to choose the node {user_select_node}")
        else:
            logger.error(f"not available to choose the node {user_select_node}")
            return
        # 用户选择的是某一个节点
        if user_select_node != "all_satellites":
            self.create_tcp_socket_and_send(user_select_node=user_select_node)
        else:
            # 用户选择向所有节点进行消息的发送
            asyncio.run(self.send_message_to_all_satellites())

    async def send_message_to_all_satellites(self):
        """
        将消息发送到所有的卫星
        :return:
        """
        while True:
            # 初始化所有的任务
            all_tasks = []
            # ----------------------- get message type ------------------------
            message_type = mfm.CommandMessage.CommandType.resolve_message_type()
            # ----------------------- get message type ------------------------

            # ---------- get user input with different type of message ----------
            if message_type in [mfm.CommandMessage.CommandType.NORMAL_COMMAND,
                                mfm.CommandMessage.CommandType.LENGTH_COMMAND]:
                answers_for_message = input("input the message (press q or quit to exit):")
                payload = answers_for_message
                if payload == "q" or payload == "quit":
                    break
            elif message_type in [mfm.CommandMessage.CommandType.BLOOM_COMMAND]:
                answers_for_bloom_params = PyInquirer.prompt(qm.BLOOM_FILTER_SETTINGS)
                bloom_filter_length = int(answers_for_bloom_params["bloom_filter_length"])
                hash_seed = int(answers_for_bloom_params["hash_seed"])
                number_of_hash_funcs = int(answers_for_bloom_params["number_of_hash_funcs"])
                payload = f"{bloom_filter_length}|{hash_seed}|{number_of_hash_funcs}"
            else:
                raise ValueError("unsupported message type")
            for index in range(1, len(self.available_node_names)):
                satellite_name = self.available_node_names[index]
                # 进行任务的创建
                task = asyncio.create_task(self.send_message_to_single_satellite_task(satellite_name=satellite_name,
                                                                                      payload=payload,
                                                                                      message_type=message_type))
                all_tasks.append(task)
            await pbm.ProgressBar.wait_tasks_with_tqdm(all_tasks, description="set bf process")
            # 进行所有任务的遍历并输出结果
            for finished_single_task in all_tasks:
                finished_single_task_result = finished_single_task.result()
                print(finished_single_task_result, flush=True)

    async def send_message_to_single_satellite_task(self,
                                                    satellite_name: str,
                                                    payload: str,
                                                    message_type: mfm.CommandMessage.CommandType):
        """
        向所有卫星进行请求的发送
        :param satellite_name 发送的卫星
        :param payload 发送的内容
        :param message_type 消息的类型
        :return: 服务器返回的消息
        """
        # 获取 ip 地址
        server_ip_address = self.satellites_map[self.name_to_id[satellite_name]].addr_connect_to_docker_zero
        # 建立 tcp 连接
        reader, writer = await asyncio.open_connection(server_ip_address, self.server_port)
        # 创建要发送的 message
        message = mfm.CommandMessage(message_type=message_type, payload=payload)
        # 进行消息的发送
        writer.write(bytes(message))
        # 等待消息的返回
        response_bytes = await reader.read(self.buffer_size)
        # 进行消息的重建
        message = mfm.CommandMessage()
        message.load_bytes(response_bytes)
        # 进行 writer 的关闭
        writer.close()
        # 进行重建完消息的返回
        return message

    def create_tcp_socket_and_send(self, user_select_node: str):
        """
        1.创建 tcp_socket 并连接
        2.利用 已经建立连接的 tcp 发送消息
        :param user_select_node: 用户选择的节点
        :return:
        """
        # 利用用户选择的节点名称，建立到这个节点的 tcp server 的连接
        connected_tcp_socket = self.create_tcp_socket(user_select_node=user_select_node)
        # 进行命令的发送
        self.send_command(tcp_socket_client=connected_tcp_socket)

    def create_tcp_socket(self, user_select_node: str):
        """
        用户选择的卫星
        :param user_select_node:
        :return: 创建好的 tcp_socket
        """
        # 根据名称进行 ip 地址的获取
        server_ip_address = self.satellites_map[self.name_to_id[user_select_node]].addr_connect_to_docker_zero
        # 创建 socket address
        server_sock_address = (server_ip_address, self.server_port)
        # 创建 tcp client socket
        tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置超时时间
        tcp_client_socket.settimeout(5)
        # 进行连接的建立 - 这个过程是阻塞的，超过5s之后就将抛出 error
        tcp_client_socket.connect(server_sock_address)
        # 返回创建好的 tcp_socket
        return tcp_client_socket

    def send_command(self, tcp_socket_client):
        """
        向服务器端进行命令的发送
        :param tcp_socket_client 已处于连接状态的 tcp 客户端
        :return: None
        """
        while True:
            # 首先询问要发送的命令的内容
            answers_for_message = input("input the message (press q or quit to exit):")
            payload = answers_for_message
            if payload == "q" or payload == "quit":
                break
            # --------------------- get message type ---------------------
            message_type = mfm.CommandMessage.CommandType.resolve_message_type()
            # --------------------- get message type ---------------------
            # ---------------------- create message ----------------------
            message = mfm.CommandMessage(message_type=message_type, payload=payload)
            # --------------------- create message ---------------------
            # -------------------- connect and send --------------------
            tcp_socket_client.send(bytes(message))
            self.recv_response(tcp_socket_client=tcp_socket_client)
            # -------------------- connect and send --------------------
        tcp_socket_client.close()

    def recv_response(self, tcp_socket_client):
        """
        服务器通常只返回很小的消息，所有我们只需要阻塞的 recv 一次即可。
        进行server_response
        :param tcp_socket_client tcp 客户端
        :return:
        """
        try:
            server_response_bytes = tcp_socket_client.recv(self.buffer_size)
            message = mfm.CommandMessage()
            message.load_bytes(server_response_bytes)
            logger.info(f"server_response: {message}")
        except Exception as e:
            logger.info(e)
