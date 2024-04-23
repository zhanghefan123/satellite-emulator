if __name__ == "__main__":
    import sys

    sys.path.append("../")
import os
from PyInquirer import prompt
from interact_module import questions as qm
from interact_module import different_types as dtm
from udp_video_client import lir_udp_video_handler as luvhm
from udp_video_client import ip_udp_video_handler as iuvhm


class CompleteVideoClient:
    def __init__(self):
        self.FRAME_WIDTH = 500
        self.FRAME_HEIGHT = 500
        self.UNICAST_FRAME_TITLE = "UNICAST TRANSMITTING"
        self.FRAMES_TO_COUNT = 20
        self.videos_path = "/configuration/videos/"
        self.selected_video_path = None
        self.video_id = None
        self.ip_mapping_file = "/configuration/address/address_mapping.conf"
        self.ip_address_mapping = {}
        self.selected_protocol = None
        self.selected_satellite_id = None
        self.selected_ip_address = None
        self.destination_port = None
        self.unicast_video_socket = None
        self.read_address_mapping()
        self.get_port()
        self.get_selected_video_path()
        self.get_protocol()
        if self.selected_protocol == dtm.Protocol.IP:
            self.handle_ip_protocol_selection()
        elif self.selected_protocol == dtm.Protocol.LIR:
            self.handle_lir_protocol_selection()
        else:
            raise ValueError("unexpected protocol selection")

    def handle_ip_protocol_selection(self):
        """
        使用 ip 协议进行视频传输
        :return:
        """
        ip_udp_video_handler = iuvhm.IpUdpVideoHandler(ip_address_mapping=self.ip_address_mapping,
                                                       destination_port=self.destination_port,
                                                       selected_video_path=self.selected_video_path)

    def handle_lir_protocol_selection(self):
        """
        使用 lir 协议进行视频传输
        :return:
        """
        destination_node_list = [item for item in self.ip_address_mapping.keys()]
        lir_udp_video_handler = luvhm.LirUdpVideoHandler(destination_node_list=destination_node_list,
                                                         destination_port=self.destination_port,
                                                         selected_video_path=self.selected_video_path)

    def read_address_mapping(self):
        """
        进行 ip 地址映射的读取
        :return: None
        """
        delimiter = "|"
        with open(self.ip_mapping_file, "r") as f:
            all_lines = f.readlines()
            for line in all_lines:
                # sat9|192.168.0.34/30|192.168.0.37/30
                items = line.split(delimiter)
                items[len(items) - 1] = items[len(items) - 1].rstrip("\n")
                self.ip_address_mapping[items[0]] = items[1:]

    def get_port(self):
        """
        获取目的端口
        :return: None
        """
        answers_for_port = prompt(qm.QUESTION_FOR_DESTINATION_PORT)
        self.destination_port = int(answers_for_port["port"])

    def get_protocol(self):
        """
        选择网络层协议，可能是 IP 可能是 LIR
        :return:
        """
        answers_for_protocol = prompt(qm.QUESTION_FOR_PROTOCOL)
        if answers_for_protocol["protocol"] == "IP":
            self.selected_protocol = dtm.Protocol.IP
        elif answers_for_protocol["protocol"] == "LIR":
            self.selected_protocol = dtm.Protocol.LIR
        else:
            raise ValueError("unsupported protocol")

    def get_selected_video_path(self):
        """
        选择要进行传输的视频
        :return:
        """
        # 填充问题的choices
        videos = os.listdir(self.videos_path)
        question_for_video_selection = qm.QUESTION_FOR_VIDEO_SELECTION
        question_for_video_selection[0]["choices"] = videos
        answers_for_video_selection = prompt(question_for_video_selection)
        self.selected_video_path = f"{self.videos_path}{answers_for_video_selection['video']}"

    def log_info(self):
        """
        进行消息的打印
        :return: None
        """
        print(f"destination id: {self.selected_satellite_id}", flush=True)
        print(f"destination address: {self.selected_ip_address}", flush=True)
        print(f"selected protocol: {self.selected_protocol}", flush=True)
        print(f"selected video path:  {self.selected_video_path}", flush=True)

    # def get_destination(self):
    #     """
    #     获取用户选择的卫星，并获取相应的目的IP地址
    #     :return: None
    #     """
    #     question_for_destination = qm.QUESTION_FOR_DESTINATION
    #     question_for_destination[0]["choices"] = list(self.ip_address_mapping.keys())
    #     answers_for_destination = prompt(question_for_destination)
    #     # find ip address according to the ip address_mapping
    #     selected_destination = answers_for_destination["destination"]
    #     self.selected_satellite_id = int(selected_destination[selected_destination.find("sat") + 3:])
    #     self.selected_ip_address = self.ip_address_mapping[selected_destination][0]
    #     self.selected_ip_address = self.selected_ip_address[:self.selected_ip_address.find("/")]

    # def create_unicast_video_socket(self):
    #     """
    #     创建 video socket
    #     :return:
    #     """
    #     # 创建 udp socket
    #     self.unicast_video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     # 根据选择的协议的不同进行选项的设置
    #     if self.selected_protocol == dtm.Protocol.LIR:
    #         # 方便内核进行唯一的标识
    #         self.unicast_video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_DEBUG, 1)
    #         # 最大长度是 40 字节，size_of_bf = 5, 而 5 * 8 = 40
    #         size_of_bf = 5
    #         byte_array = bytearray([0x94, 0x28, 0x1, self.selected_satellite_id, 0x1, 0x1, 0x1, 0x1] * size_of_bf)
    #         self.unicast_video_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
    #     elif self.selected_protocol == dtm.Protocol.IP:
    #         size_of_bf = 5
    #         byte_array = bytearray([0x94, 0x28, 0x1, self.selected_satellite_id, 0x1, 0x1, 0x1, 0x1] * size_of_bf)
    #         self.unicast_video_socket.setsockopt(socket.IPPROTO_IP, socket.IP_OPTIONS, byte_array)
    #     else:
    #         raise ValueError("unsupported protocol")

    # def send_video_with_unicast_socket(self):
    #     """
    #     使用创建出来的 unicast_video_socket 进行视频流的传送
    #     :return:
    #     """
    #     # 一些展示属性
    #     fps = 0  # 帧率
    #     cnt = 0  # 当前已经是第几帧
    #     last_time = 0  # 上一次计算帧率的时间
    #     # 创建对象捕获视频文件
    #     self.video_id = cv2.VideoCapture(self.selected_video_path)
    #     # 如果还没读完
    #     while self.video_id.isOpened():
    #         # 从视频流之中读取视频帧
    #         _, video_frame = self.video_id.read()
    #         # 将视频帧进行大小的修改
    #         video_frame = imutils.resize(width=self.FRAME_WIDTH, height=self.FRAME_HEIGHT, image=video_frame)
    #         # 将视频帧按照 jpg 格式进行压缩编码
    #         encoded, buffer = cv2.imencode(".jpg", video_frame, [cv2.IMWRITE_JPEG_QUALITY, 20])
    #         # 将帧进行发送
    #         self.unicast_video_socket.sendto(buffer, (self.selected_ip_address, self.destination_port))
    #         # 同时进行发送端的展示
    #         # 1. 修改这一帧并添加文字
    #         frame_modified = cv2.putText(video_frame, f"FPS: {fps}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
    #                                      (0, 0, 255), 2)
    #         # 2. 进行这一帧的展示
    #         cv2.imshow(self.UNICAST_FRAME_TITLE, frame_modified)
    #         # 3. 注意在 imshow 一定要执行 cv2.waitKey, 相当于指定帧的持续时间, &0xFF是为了避免 linux 内的bug
    #         key = cv2.waitKey(1) & 0xFF
    #         if key == ord('q'):
    #             self.unicast_video_socket.close()
    #             print("video send complete", flush=True)
    #             break
    #         if cnt % self.FRAMES_TO_COUNT == 0:
    #             try:
    #                 fps = round(self.FRAMES_TO_COUNT / (time.time() - last_time))
    #                 last_time = time.time()
    #             except ZeroDivisionError as e:
    #                 pass
    #         cnt += 1


if __name__ == "__main__":
    complete_video_client = CompleteVideoClient()
