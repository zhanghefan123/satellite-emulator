import os
from netlink_client import netlink_client as ncm


class NetToIdMapper:
    def __init__(self, netlink_client: ncm.NetlinkClient):
        """
        初始化绑定模块
        :param netlink_client:
        """
        self.netlink_client = netlink_client

    def bind_net_to_satellite_id(self):
        """
        将内核网络命名空间和相应的卫星的id进行绑定
        :return:
        """
        self.netlink_client.send_netlink_data(os.getenv('NODE_ID'), ncm.NetlinkMessageType.CMD_BIND_NET_TO_SAT_NAME)

    def start(self):
        """
        启动
        :return:
        """
        self.bind_net_to_satellite_id()
