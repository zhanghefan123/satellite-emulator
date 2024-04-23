from pyroute2.netlink import NLM_F_REQUEST, genlmsg
from pyroute2.netlink.generic import GenericNetlinkSocket
from PyInquirer import prompt

if __name__ == "__main__":
    import sys

    sys.path.append("../")
from satellite_node_useful_tools import logger as lm

QUESTIONS_FOR_NETLINK_COMMAND = [
    {
        "type": "list",
        "name": "command",
        "message": "Please select the command: ",
        "choices": ["insert route", "calculate length", "search route", "find net interface"]
    }
]
QUESTIONS_FOR_SOURCE_AND_DEST = [
    {
        "type": "input",
        "name": "source",
        "message": "Please input the source id: "
    },
    {
        "type": "input",
        "name": "destination",
        "message": "Please input the destination id: "
    }
]
QUESTIONS_FOR_CMD_CALCULATE_LENGTH = [
    {
        "type": "input",
        "name": "message",
        "message": "Please input the message you want to calculate: "
    }
]
QUESTIONS_FOR_CMD_FIND_DEV_BY_INDEX = [
    {
        "type": "input",
        "name": "interface",
        "message": "Please input the ifindex of the network interface: "
    }
]
CMD_UNSPEC = 0
CMD_REQ = 1


class NetlinkMessageType:
    CMD_UNSPEC = 0
    CMD_INSERT_ROUTES = 1  # 进行路由的插入
    CMD_CALCULATE_LENGTH = 2  # 进行长度的计算
    CMD_SEARCH_ROUTES = 3  # 进行路由条目的搜索
    CMD_FIND_DEV_BY_INDEX = 4  # 通过 ifindex 进行接口的名称的查找
    # CMD_CONSTRUCT_INTERFACE_TABLE = 5  # 进行接口表的创建
    CMD_BIND_NET_TO_SAT_NAME = 5  # 将网络命名空间和卫星名称进行绑定
    CMD_SET_BLOOM_FILTER_ATTRS = 6  # 设置布隆过滤器的属性
    CMD_CONSTRUCT_NEW_INTERFACE_TABLE = 7


# 消息的组成
class NetlinkMessageFormat(genlmsg):
    nla_map = (
        ('RLINK_ATTR_UNSPEC', 'none'),
        ('RLINK_ATTR_DATA', 'asciiz'),
        ('RLINK_ATTR_LEN', 'uint32'),
    )


class NetlinkClient(GenericNetlinkSocket):

    def __init__(self):
        super().__init__()
        self.logger = lm.Logger().get_logger()
        self.bind("EXMPL_GENL", NetlinkMessageFormat)

    def send_netlink_data(self, data: str, message_type: int):
        """
        进行数据的发送
        :param data: 要发送的数据
        :param message_type: 发送的消息的类型
        :return:
        """
        msg = NetlinkMessageFormat()
        msg["cmd"] = message_type
        msg["version"] = 1
        msg["attrs"] = [("RLINK_ATTR_DATA", data)]
        kernel_response = self.nlm_request(msg, self.prid, msg_flags=NLM_F_REQUEST)
        self.logger.success("-------RECEIVE KERNEL RESPONSE--------")
        data_part = kernel_response[0]
        self.logger.info(data_part.get_attr('RLINK_ATTR_LEN'))
        self.logger.info(data_part.get_attr('RLINK_ATTR_DATA'))
        self.logger.success("-------RECEIVE KERNEL RESPONSE--------")

    @classmethod
    def get_selected_command(cls):
        """
        进行命令用户命令的获取
        :return: 返回用户选择的命令类型 类型一般为 (NetlinkMessageType)
        """
        selected_command_answer = prompt(QUESTIONS_FOR_NETLINK_COMMAND)["command"]
        if selected_command_answer == "insert route":
            selected_command = NetlinkMessageType.CMD_INSERT_ROUTES
        elif selected_command_answer == "calculate length":
            selected_command = NetlinkMessageType.CMD_CALCULATE_LENGTH
        elif selected_command_answer == "search route":
            selected_command = NetlinkMessageType.CMD_SEARCH_ROUTES
        elif selected_command_answer == "find net interface":
            selected_command = NetlinkMessageType.CMD_FIND_DEV_BY_INDEX
        else:
            raise ValueError("unsupported command")
        return selected_command

    def handle_different_command(self, command):
        """
        :param command 用户选择的命令
        进行各种命令的处理
        :return:
        """
        if command == NetlinkMessageType.CMD_INSERT_ROUTES:
            # 如果用户选择的命令是 CMD_INSERT_ROUTES
            raise ValueError("current unsupported command")
        elif command == NetlinkMessageType.CMD_CALCULATE_LENGTH:
            # 如果用户选择的命令是 CMD_CALCULATE_LENGTH
            user_message = prompt(QUESTIONS_FOR_CMD_CALCULATE_LENGTH)["message"]
            self.send_netlink_data(user_message, message_type=command)
        elif command == NetlinkMessageType.CMD_SEARCH_ROUTES:
            # 如果用户选择的命令是 CMD_SEARCH_ROUTES
            source_and_dest = prompt(QUESTIONS_FOR_SOURCE_AND_DEST)
            source = int(source_and_dest["source"])
            destination = int(source_and_dest["destination"])
            self.send_netlink_data(f"{source},{destination}", message_type=command)
        elif command == NetlinkMessageType.CMD_FIND_DEV_BY_INDEX:
            # 如果用户选择的命令是 CMD_FIND_DEV_BY_INDEX
            interface = prompt(QUESTIONS_FOR_CMD_FIND_DEV_BY_INDEX)["interface"]
            self.send_netlink_data(f"{interface}", message_type=command)
        else:
            raise ValueError("current unsupported command")


if __name__ == "__main__":
    user_selected_command = NetlinkClient.get_selected_command()
    netlink_client = None
    try:
        netlink_client = NetlinkClient()
        netlink_client.handle_different_command(command=user_selected_command)
    except Exception as e:
        netlink_client.logger.error(e)
    finally:
        if netlink_client is not None:
            netlink_client.close()
