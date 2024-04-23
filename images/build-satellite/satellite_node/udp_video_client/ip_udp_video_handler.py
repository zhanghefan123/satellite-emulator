import cv2
import imutils
import time
from PyInquirer import prompt
from interact_module import questions as qm
from interact_module import different_types as dtm
import socket
import multiprocessing


class IpUdpVideoHandler:
    def __init__(self, ip_address_mapping, destination_port, selected_video_path):
        """
        初始化 ip udp 处理起i
        :param ip_address_mapping: 目的接口编号 ---> 目的节点 ip
        :param destination_port: 目的端口
        :param selected_video_path: 选择的要传输的视频的路径
        """
        self.FRAME_WIDTH = 500
        self.FRAME_HEIGHT = 500
        self.FRAMES_TO_COUNT = 20
        self.title = None
        self.ip_address_mapping = ip_address_mapping
        self.destination_port = destination_port
        self.selected_video_path = selected_video_path
        self.transmission_pattern = None
        self.get_transmission_pattern()
        self.handle_different_transmission_pattern()

    def get_transmission_pattern(self):
        """
        进行传输协议的获取
        :return:
        """
        answers_for_transmission_pattern = prompt(qm.QUESTION_FOR_IP_TRANSMISSION_PATTERN)["transmission_pattern"]
        if answers_for_transmission_pattern == "unicast":
            self.transmission_pattern = dtm.TransmissionPattern.UNICAST
            self.title = "UNICAST TRANSMITTING"
        elif answers_for_transmission_pattern == "multi_unicast":
            self.transmission_pattern = dtm.TransmissionPattern.MULTI_UNICAST
            self.title = "MUTLI UNICAST TRANSMITTING"
        else:
            raise ValueError("unexpected transmission pattern")

    def handle_different_transmission_pattern(self):
        """
        进行不同传输协议的处理
        :return:
        """
        if self.transmission_pattern == dtm.TransmissionPattern.UNICAST:
            self.handle_unicast()
        elif self.transmission_pattern == dtm.TransmissionPattern.MULTI_UNICAST:
            self.handle_multi_unicast()
        else:
            raise ValueError("unexpected transmission pattern")

    def handle_unicast(self):
        # 让用户选择单个目的卫星
        selected_destination_node_id = self.select_destination_node_id()
        # 根据用户选择的单个目的卫星进行 ip 地址的获取
        selected_destination_ip = self.ip_address_mapping[selected_destination_node_id][0]
        selected_destination_ip = selected_destination_ip[:selected_destination_ip.find("/")]
        # 构造 socket
        unicast_udp_video_socket = self.create_socket_and_set_opt()
        # 单播传送的时候肯定需要设置
        display_video = True
        # 利用构造好的 socket 进行发送
        self.single_process_send_data(unicast_udp_video_socket, selected_destination_ip, display_video)

    def handle_multi_unicast(self):
        # 让用户进行目的节点列表的选择
        destination_node_list = self.select_destination_node_ids()
        # 通过目的节点编号列表进行目的ip 列表的获取
        destination_ip_list = [self.ip_address_mapping[item][0] for item in destination_node_list]
        destination_ip_list = [item[:item.find("/")] for item in destination_ip_list]
        # 计数器 - 只有第一个需要视频展示
        count = 0
        # 遍历所有的目的ip并进行进程的创建
        for destination_ip in destination_ip_list:
            # 构造 socket
            unicast_udp_video_socket = self.create_socket_and_set_opt()
            display_video = True
            title = f"{destination_node_list[count]} TRANSMITTING"
            multiprocessing.Process(target=self.single_process_send_data,
                                    args=(unicast_udp_video_socket,
                                          destination_ip,
                                          display_video,
                                          title)).start()
            count += 1

    def select_destination_node_id(self):
        """
        选择单颗目的卫星
        :return: 选择好的卫星的编号
        """
        question_for_destination_node = qm.QUESTION_FOR_DESTINATION
        question_for_destination_node[0]["choices"] = list(self.ip_address_mapping.keys())
        selected_destination_node_str = prompt(question_for_destination_node)["destination"]
        return selected_destination_node_str

    def select_destination_node_ids(self):
        """
        进行目的节点列表的选择
        :return:
        """
        count = int(prompt(qm.QUESTION_FOR_NUMBER_OF_DESTINATION)["count"])
        destination_node_list = []
        for index in range(count):
            current_destination_id = self.select_destination_node_id()
            destination_node_list.append(current_destination_id)
        return destination_node_list

    def create_socket_and_set_opt(self):
        """
        创建 socket 并设置好选项
        :return: 创建好的并且设置好选项的 udp_socket
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        size_of_bf = 5
        first_eight_bytes = [0x94, 0x28, 0x1, 0x1, 0x1, 0x1, 0x1, 0x1]
        byte_array = bytearray(first_eight_bytes * size_of_bf)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
        return udp_socket

    def single_process_send_data(self, udp_socket, destination_ip, display_video, title):
        """
        进行数据的发送
        :param udp_socket 创建好的用来传输视频的 udp_socket
        :param destination_ip 单个目的节点ip
        :param display_video 是否进行视频图像的展示
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
            udp_socket.sendto(buffer, (destination_ip, self.destination_port))
            # 同时进行发送端的展示
            # 1. 修改这一帧并添加文字
            if display_video:
                frame_modified = cv2.putText(video_frame, f"FPS: {fps}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                             (0, 0, 255), 2)
                # 2. 进行这一帧的展示
                cv2.imshow(title, frame_modified)
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
