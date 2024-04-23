from enum import Enum
import struct


class CommandMessage:
    class CommandType(Enum):
        # 报文的类型的定义
        NORMAL_COMMAND = 1
        LENGTH_COMMAND = 2
        BLOOM_COMMAND = 3
        INIT_COMMAND = 4

        def __str__(self):
            if self == self.NORMAL_COMMAND:
                return "NORMAL_COMMAND"
            elif self == self.LENGTH_COMMAND:
                return "LENGTH_COMMAND"
            elif self == self.BLOOM_COMMAND:
                return "BLOOM_COMMAND"
            elif self == self.INIT_COMMAND:
                return "INIT_COMMAND"
            else:
                raise ValueError("unsupported message type")

    def __init__(self, message_type=CommandType.NORMAL_COMMAND, payload="hello"):
        """
        进行数据包的初始化, 只需要传入消息的类型以及消息的载荷
        :param message_type: 发送消息的类型
        :param payload: 消息的载荷
        """
        self.message_type = message_type.value
        payload_in_bytes = payload.encode(encoding="utf-8")
        self.length = len(payload_in_bytes)
        self.payload = payload_in_bytes

    def __bytes__(self):
        """
        将其转换为字节数组
        :return: 返回转换完成的字节数组
        """
        return struct.pack(f"<2I{self.length}s", self.message_type, self.length, self.payload)

    def load_bytes(self, bytes_tmp):
        """
        将传入的字节数组解析为对象的各个字段
        :param bytes_tmp: 这个消息对应的字节数组
        :return: 解析的字节的数量
        """
        self.message_type, self.length = struct.unpack("<2I", bytes_tmp[:8])
        self.payload = struct.unpack(f"<{self.length}s", bytes_tmp[8:8+self.length])[0]
        return 8 + self.length

    def __str__(self):
        """
        将数据包转换为对应的字符串
        :return: 数据包对应的字符串
        """
        return f"type:{self.message_type} | length:{self.length} | payload:{self.payload}"


if __name__ == "__main__":
    normal_message = CommandMessage(message_type=CommandMessage.CommandType.NORMAL_COMMAND, payload="hello")
    bytes_pack = bytes(normal_message)
    print(bytes_pack)
    normal_message.load_bytes(bytes_pack)
    print(bytes(normal_message))

