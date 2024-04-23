import socket
import netifaces


class Tools:
    @classmethod
    def get_local_ip_address(cls):
        # ip_address_list = []
        # # 拿到所有的接口的 IP 地址
        # for index, intf in enumerate(netifaces.interfaces()):
        #     if index > 0:
        #         interface_addr = netifaces.ifaddresses(intf)[netifaces.AF_INET][0]["addr"]
        #         ip_address_list.append(interface_addr)
        # print(ip_address_list)
        # return ip_address_list[0]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))  # 连接到 google dns 查询 ip 地址
            return sock.getsockname()[0]  # getsockname 返回本地套接字地址

    @classmethod
    def raw_socket_creator(cls, upper_layer_protocol: int):
        created_raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, upper_layer_protocol)
        created_raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        return created_raw_socket


if __name__ == "__main__":
    Tools.get_local_ip_address()
