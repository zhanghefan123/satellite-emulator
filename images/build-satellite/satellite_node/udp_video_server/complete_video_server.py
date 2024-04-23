if __name__ == "__main__":
    import sys

    sys.path.append("../")
import os
import cv2
import time
import socket
import numpy as np
from config_sat import const_var as cvm
from PyInquirer import prompt
from interact_module import questions as qm


class CompleteVideoServer:
    def __init__(self):
        self.BUF_SIZE = 65536
        self.UNICAST_FRAME_TITLE = f"SAT{os.getenv('NODE_ID')} RECEIVING"
        self.FRAMES_TO_COUNT = 20
        self.selected_port = None
        self.listening_ip_address = cvm.INADDR_ANY
        self.server_listening_socket = None
        self.get_port()
        self.create_server_listening_socket()
        self.receive_video_with_server_listening_socket()

    def get_port(self):
        """
        获取目的端口
        :return: None
        """
        answers_for_port = prompt(qm.QUESTION_FOR_SERVER_LISTEN_PORT)
        self.selected_port = int(answers_for_port["port"])

    def create_server_listening_socket(self):
        """
        进行视频监听 socket 的获取
        :return: None
        """
        self.server_listening_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUF_SIZE)
        self.server_listening_socket.bind((self.listening_ip_address, self.selected_port))

    def receive_video_with_server_listening_socket(self):
        """
        使用创建完成的 socket 进行监听
        :return: None
        """
        # 一些展示属性
        fps = 0  # 帧率
        cnt = 0  # 当前已经是第几帧
        last_time = 0  # 上一次计算帧率的时间
        # 死循环进行收包
        while True:
            try:
                packet, address = self.server_listening_socket.recvfrom(self.BUF_SIZE)
            except Exception as e:
                print(f"error {e}", flush=True)
                break
            if cnt == 0:
                self.server_listening_socket.settimeout(5)  # 在接收到第一个包之后，如果5s之后都没有数据，那么判定为超时
            np_data = np.fromstring(string=packet, dtype=np.uint8)
            received_video_frame = cv2.imdecode(np_data, 1)
            # 1. 修改这一帧并添加文字
            frame_modified = cv2.putText(received_video_frame, f"FPS: {fps}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                         (0, 0, 255), 2)
            # 2. 进行这一帧的展示
            cv2.imshow(self.UNICAST_FRAME_TITLE, frame_modified)
            # 3. 注意在 imshow 一定要执行 cv2.waitKey, 相当于指定帧的持续时间, &0xFF是为了避免 linux 内的bug
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.server_listening_socket.close()
                print("video receive complete", flush=True)
                break
            if cnt % self.FRAMES_TO_COUNT == 0:
                try:
                    fps = round(self.FRAMES_TO_COUNT / (time.time() - last_time))
                    last_time = time.time()
                except ZeroDivisionError as e:
                    pass
            cnt += 1


if __name__ == "__main__":
    complete_video_server = CompleteVideoServer()
