if __name__ == "__main__":
    import sys

    sys.path.append("../")
import logging
import json
import collections
import time
from flask import Flask, request
from gevent.pywsgi import WSGIServer
from flask_cors import *
from config import config_reader as crm
from loguru import logger
from flask.logging import default_handler


class DataStructureToStoreHttpServer:
    def __init__(self):
        self.http_server = None


class FlaskVisualizer:
    app = Flask(__name__)
    data_queue = collections.deque(maxlen=10)
    tps_queue = collections.deque(maxlen=10)
    CORS(app, supports_credentials=True)

    @staticmethod
    @app.route('/', methods=['GET'])
    def index():
        return "Hello, World!"

    @staticmethod
    @app.route("/add_tps", methods=["POST"])
    def add_tps():
        data = json.loads(request.data)
        current_timestamp = data["current_time_stamp"]
        current_tps = data["tps"]
        # print(data, flush=True)
        FlaskVisualizer.tps_queue.append((current_timestamp, current_tps))
        response_data = {
            "status": "success"
        }
        response_json_str = json.dumps(response_data)
        # 进行响应数据的构建
        headers = {"Content-Type": "application/json"}
        return response_json_str, 200, headers

    @staticmethod
    @app.route('/data_add', methods=["POST"])
    def receive_data():
        # 将传入的请求参数进行解析
        data = json.loads(request.data)
        current_timestamp = data["current_time_stamp"]
        current_data_rate = data["current_data_rate"]
        current_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(float(current_timestamp))))
        FlaskVisualizer.data_queue.append((current_date, current_data_rate))
        response_data = {
            "status": "success"
        }
        response_json_str = json.dumps(response_data)
        # 进行响应数据的构建
        headers = {"Content-Type": "application/json"}
        return response_json_str, 200, headers

    @staticmethod
    @app.route("/data_get", methods=["GET"])
    def get_data():
        # 获取的总是长度为100的队列
        response_data = {
            "attack_rate": {item[0]: item[1] for item in FlaskVisualizer.data_queue},
            "tps": {item[0]: item[1] for item in FlaskVisualizer.tps_queue}
        }
        response_json_str = json.dumps(response_data)
        headers = {"Content-Type": "application/json"}
        return response_json_str, 200, headers

    def start_server(self, data_structure_to_store_http_server: DataStructureToStoreHttpServer):
        try:
            logger.success("server started")
            # 进行配置文件的解析
            config_reader = crm.ConfigReader("./resources/constellation_config.yml")
            # 获取 ip 地址
            network_ip_address = config_reader.network_ip_address
            http_server = WSGIServer((network_ip_address, 13000), FlaskVisualizer.app, log=None)
            data_structure_to_store_http_server.http_server = http_server
            http_server.serve_forever()
        except KeyboardInterrupt:
            logger.success("server stoppped")


if __name__ == "__main__":
    flask_visualizer = FlaskVisualizer()
    flask_visualizer.start_server()
