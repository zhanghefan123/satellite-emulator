from enum import Enum


class Protocol(Enum):
    IP = 0
    LIR = 1


class TransmissionPattern(Enum):
    UNICAST = 0
    MULTICAST = 1
    MULTI_UNICAST = 2


class AttackTypes(Enum):
    ICMP_FLOOD_ATTACK = 1
    UDP_FLOOD_ATTACK = 2
    TCP_SYN_FLOOD = 3
    LAND_ATTACK = 4
    TCP_FLAGS_ATTACK = 5
    FIN_FLOOD_ATTACK = 6


class InvalidTcpFlags(Enum):
    EMPTY = 0
    FULL = 1
    SYN_AND_FIN_SET = 2
    SYN_AND_RST_SET = 3
    FIN_SET_AND_ACK_NOT_SET = 4