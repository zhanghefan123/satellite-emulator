import os
from command_server import message_format as mfm
from netlink_client import netlink_client as ncm


class DifferentMessageHandler:
    def __init__(self, client_socket, netlink_client: ncm.NetlinkClient, starter):
        """
        初始化不同函数
        :param client_socket: 向用户返回消息所使用到的 socket
        :param netlink_client: netlink client
        """
        self.client_socket = client_socket
        self.netlink_client = netlink_client
        self.starter = starter

    def handle_message(self, message: mfm.CommandMessage):
        """
        进行消息的处理
        :param message: 要进行处理的消息
        :return:
        """
        message_type = message.message_type
        if message_type == mfm.CommandMessage.CommandType.NORMAL_COMMAND.value:
            self.handle_normal_message(message)
        elif message_type == mfm.CommandMessage.CommandType.LENGTH_COMMAND.value:
            self.handle_length_message(message)
        elif message_type == mfm.CommandMessage.CommandType.BLOOM_COMMAND.value:
            self.handle_bloom_message(message)
        elif message_type == mfm.CommandMessage.CommandType.INIT_COMMAND.value:
            self.handle_init_command(message)
        else:
            raise ValueError("unsupported type")

    def handle_normal_message(self, message: mfm.CommandMessage):
        """
        进行普通消息的处理
        :param message: 要进行处理的消息
        :return:
        """
        server_response_message = mfm.CommandMessage(message_type=mfm.CommandMessage.CommandType.NORMAL_COMMAND,
                                                     payload=str(message.payload, encoding="utf-8"))
        self.client_socket.send(bytes(server_response_message))

    def handle_length_message(self, message: mfm.CommandMessage):
        """
        进行长度消息的处理
        :param message: 要进行处理的消息
        :return:
        """
        server_response_message = mfm.CommandMessage(message_type=mfm.CommandMessage.CommandType.LENGTH_COMMAND,
                                                     payload=f"client send string length: {str(message.length)}")
        self.client_socket.send(bytes(server_response_message))

    def handle_bloom_message(self, message: mfm.CommandMessage):
        """
        进行布隆过滤器消息的处理
        :param message:
        :return:
        """
        delimiter = "|"
        payload_str = str(message.payload, encoding="utf-8")
        bloom_filter_length, hash_seed, number_of_hash_funcs = payload_str.split(delimiter)
        bloom_filter_length = int(bloom_filter_length)
        hash_seed = int(hash_seed)
        number_of_hash_funcs = int(number_of_hash_funcs)
        # 这里需要向内核进行设置
        self.netlink_client.send_netlink_data(data=f"{bloom_filter_length},{hash_seed},{number_of_hash_funcs}",
                                              message_type=ncm.NetlinkMessageType.CMD_SET_BLOOM_FILTER_ATTRS)
        # 然后向宿主机进行消息的返回
        server_response_message = mfm.CommandMessage(message_type=mfm.CommandMessage.CommandType.BLOOM_COMMAND,
                                                     payload=f"bloom_filter_length: {bloom_filter_length},"
                                                             f"hash_seed: {hash_seed},"
                                                             f"number_of_hash_funcs: {number_of_hash_funcs}")
        self.client_socket.send(bytes(server_response_message))

    def create_frr_related_structure(self):
        """
        create frr related structure
        :return:
        """
        if os.getenv("LIR_ENABLED") == "1":
            print("FRR LIR_ENABLED", flush=True)
            # 1.进行新接口表的创建
            self.starter.new_interface_table_generator.start()
            # 2.进行路由表的创建 (注意路由表创建的时候需要先有接口表)
            self.starter.routing_table_generator.start()
            # 3.进行绑定的创建
            self.starter.net_to_id_mapper.start()
        else:
            print("LIR NOT ENABLED", flush=True)

    def handle_init_command(self, message: mfm.CommandMessage):
        """
        Handle initialization
        :param message:
        :return:
        """
        self.handle_bloom_message(message)
        # 1.进行接口表的创建
        # self.starter.interface_table_generator.start()
        # ------------------ lir 相关数据结构的创建 ------------------
        self.create_frr_related_structure()
        # ------------------ lir 相关数据结构的创建 ------------------
        # 4.进行 frr 路由软件的启动
        # 根据环境变量判断是否进行启动
        self.starter.start_frr()
        # 5.进行默认路由的删除
        self.starter.delete_default_route()
