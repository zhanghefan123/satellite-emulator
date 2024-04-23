import os
import cv2
import time
import imutils
import socket
from PyInquirer import prompt
from interact_module import questions as qm
from interact_module import different_types as dtm
from lir_related import routes_loader as rlm


class LirUdpVideoHandler:
    def __init__(self, destination_node_list, destination_port, selected_video_path):
        """
        进行 lir 视频传输处理器的初始化
        :param destination_node_list:  目的节点列表
        :param destination_port:  目的端口
        :param selected_video_path: 用户选择的视频的全路径
        """
        self.FRAME_WIDTH = 500
        self.FRAME_HEIGHT = 500
        self.FRAMES_TO_COUNT = 20
        self.lir_routes_loader = rlm.RoutesLoader(path_of_routes_configuration_file=f"/configuration/routes/{os.getenv('NODE_TYPE')}_all.conf")
        self.lir_routes_loader.load_lir_routes()
        self.destination_node_list = destination_node_list
        self.destination_port = destination_port
        self.selected_video_path = selected_video_path
        self.transmission_pattern = None
        self.title = None
        self.get_transmission_pattern()
        self.handle_different_transmission_pattern()

    def get_transmission_pattern(self):
        """
        进行传输协议的获取
        :return:
        """
        answers_for_transmission_pattern = prompt(qm.QUESTION_FOR_LIR_TRANSMISSION_PATTERN)["transmission_pattern"]
        if answers_for_transmission_pattern == "unicast":
            self.transmission_pattern = dtm.TransmissionPattern.UNICAST
            self.title = "UNICAST TRANSMITTING"
        elif answers_for_transmission_pattern == "multicast":
            self.transmission_pattern = dtm.TransmissionPattern.MULTICAST
            self.title = "MULTICAST_TRANSMITTING"
        else:
            raise ValueError("unexpected transmission pattern")

    def handle_different_transmission_pattern(self):
        """
                进行不同传输协议的处理
                :return:
                """
        if self.transmission_pattern == dtm.TransmissionPattern.UNICAST:
            self.handle_unicast()
        elif self.transmission_pattern == dtm.TransmissionPattern.MULTICAST:
            self.handle_multicast()
        else:
            raise ValueError("unexpected transmission pattern")

    def handle_unicast(self):
        """
        处理 lir unicast
        :return:
        """
        # 让用户选择单个目的卫星
        selected_destination_node_id = self.select_destination_node()
        # 创建 unicast socket 并设置好选项
        unicast_udp_socket = self.create_socket_and_set_opt([selected_destination_node_id])
        # 准备进行消息的发送
        self.send_data(unicast_udp_socket, [selected_destination_node_id] * 4)

    def handle_multicast(self):
        """
        处理 lir multicast
        :return:
        """
        # 进行目的节点列表的选择
        destination_node_list = self.select_destination_node_ids()
        # 进行路由条目的插入
        self.insert_multicast_corresponding_routes(destination_node_list)
        # 创建 multicast socket 并设置好选项
        multicast_udp_socket = self.create_socket_and_set_opt(destination_node_list)
        # 准备进行消息的发送
        if len(destination_node_list) != 4:
            destination_node_list = destination_node_list + [250] * (4 - len(destination_node_list))
        self.send_data(multicast_udp_socket, destination_node_list)

    def insert_multicast_corresponding_routes(self, destination_node_list):
        """
        进行多播相关的路由条目的插入
        :param destination_node_list:
        :return:
        """
        primary_node = destination_node_list[0]
        for index in range(1, len(destination_node_list)):
            destination_node = destination_node_list[index]
            self.lir_routes_loader.insert_route(source=primary_node, destination=destination_node)

    def select_destination_node(self):
        """
        选择单颗目的卫星
        :return: 选择好的卫星的编号
        """
        question_for_destination_node = qm.QUESTION_FOR_DESTINATION
        question_for_destination_node[0]["choices"] = self.destination_node_list
        selected_destination_node_str = prompt(question_for_destination_node)["destination"]
        selected_destination_node_id = int(
            selected_destination_node_str[selected_destination_node_str.find("sat") + 3:])
        return selected_destination_node_id

    def select_destination_node_ids(self):
        """
        进行目的节点列表的选择
        :return:
        """
        count = int(prompt(qm.QUESTION_FOR_NUMBER_OF_DESTINATION)["count"])
        destination_node_list = []
        for index in range(count):
            current_destination_id = self.select_destination_node()
            destination_node_list.append(current_destination_id)
        return destination_node_list

    def create_socket_and_set_opt(self, destination_node_id_list):
        """
        创建 socket 并设置好选项
        :param destination_node_id_list 目的节点 id 列表
        :return:
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        size_of_bf = 5
        number_of_dest = len(destination_node_id_list)
        # original code when OPTION_START_INDEX = 2
        # first_eight_bytes = [0x94, 0x28] + [number_of_dest] + destination_node_id_list + [0x1] * (8 - 3 - number_of_dest)
        # current code when OPTIONS_START_INDEX = 3
        first_eight_bytes = [0x94, 0x28] + [int(os.getenv("NODE_ID"))] + [number_of_dest] + destination_node_id_list + [
            0x1] * (8 - 4 - number_of_dest)
        byte_array = bytearray(first_eight_bytes * size_of_bf)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        return udp_socket

    def send_data(self, udp_socket, destination_node_id_list):
        """
        进行数据的发送
        :param udp_socket 创建好的用来传输视频的 udp_socket
        :param destination_node_id_list 目的节点列表
        :return:
        """
        """
        使用创建出来的 udp_socket 进行视频流的传送
        :return:
        """
        # ----------- 一些展示属性 -----------
        fps = 0  # 帧率
        cnt = 0  # 当前已经是第几帧
        last_time = 0  # 上一次计算帧率的时间
        # ----------- 一些展示属性 -----------
        # ----------- 用 ip 地址存储目的节点列表 -----------
        destination_node_id_list = [str(item) for item in destination_node_id_list]
        lir_destination_address = ".".join(destination_node_id_list)
        # ----------- 用 ip 地址存储目的节点列表 -----------
        # 创建对象捕获视频文件
        video_id = cv2.VideoCapture(self.selected_video_path)
        # 如果还没读完
        while video_id.isOpened():
            # 从视频流之中读取视频帧
            _, video_frame = video_id.read()
            # 将视频帧进行大小的修改
            video_frame = imutils.resize(width=self.FRAME_WIDTH, height=self.FRAME_HEIGHT, image=video_frame)
            # 将视频帧按照 jpg 格式进行压缩编码
            encoded, buffer = cv2.imencode(".jpg", video_frame, [cv2.IMWRITE_JPEG_QUALITY, 20])
            # 将帧进行发送
            udp_socket.sendto(buffer, (lir_destination_address, self.destination_port))
            # 同时进行发送端的展示
            # 1. 修改这一帧并添加文字
            frame_modified = cv2.putText(video_frame, f"FPS: {fps}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                         (0, 0, 255), 2)
            # 2. 进行这一帧的展示
            cv2.imshow(self.title, frame_modified)
            # 3. 注意在 imshow 一定要执行 cv2.waitKey, 相当于指定帧的持续时间, &0xFF是为了避免 linux 内的bug
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                udp_socket.close()
                print("video send complete", flush=True)
                break
            if cnt % self.FRAMES_TO_COUNT == 0:
                try:
                    fps = round(self.FRAMES_TO_COUNT / (time.time() - last_time))
                    last_time = time.time()
                except ZeroDivisionError as e:
                    pass
            cnt += 1
