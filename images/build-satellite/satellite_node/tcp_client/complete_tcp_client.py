if __name__ == "__main__":
    import sys

    sys.path.append("../")
from PyInquirer import prompt
from interact_module import questions as qm
from interact_module import different_types as dtm
from tcp_client import ip_tcp_handler as ithm
from tcp_client import lir_tcp_handler as lthm


class CompleteTcpClient:
    def __init__(self):
        self.tcp_client_socket = None
        self.server_port = None
        self.selected_protocol = None
        self.ip_mapping_file = "/configuration/address/address_mapping.conf"
        self.ip_address_mapping = {}
        self.read_address_mapping()
        self.get_port()
        self.get_protocol()
        if self.selected_protocol == dtm.Protocol.IP:
            self.handle_ip_protocol_selection()
        elif self.selected_protocol == dtm.Protocol.LIR:
            self.handle_lir_protocol_selection()
        else:
            raise ValueError("unexpected protocol")

    def handle_ip_protocol_selection(self):
        ip_tcp_handler = ithm.IpTcpHandler(ip_address_mapping=self.ip_address_mapping,
                                           destination_port=self.server_port)

    def handle_lir_protocol_selection(self):
        lthm_handler = lthm.LirTcpHandler(ip_address_mapping=self.ip_address_mapping,
                                          destination_port=self.server_port)

    def get_port(self):
        """
        获取目的端口
        :return:
        """
        answers_for_port = prompt(qm.QUESTION_FOR_DESTINATION_PORT)
        self.server_port = int(answers_for_port["port"])

    def get_protocol(self):
        """
        获取用户选择的网络曾协议
        :return:
        """
        answers_for_protocol = prompt(qm.QUESTION_FOR_PROTOCOL)
        if answers_for_protocol["protocol"] == "IP":
            self.selected_protocol = dtm.Protocol.IP
        elif answers_for_protocol["protocol"] == "LIR":
            self.selected_protocol = dtm.Protocol.LIR
        else:
            raise ValueError("unsupported protocol")

    def read_address_mapping(self):
        """
        进行 ip 地址映射的读取
        :return:
        """
        delimiter = "|"
        with open(self.ip_mapping_file, "r") as f:
            all_lines = f.readlines()
            for line in all_lines:
                # sat9|192.168.0.34/30|192.168.0.37/30
                items = line.split(delimiter)
                items[len(items) - 1] = items[len(items) - 1].rstrip("\n")
                self.ip_address_mapping[items[0]] = items[1:]


if __name__ == "__main__":
    complete_tcp_client = CompleteTcpClient()
