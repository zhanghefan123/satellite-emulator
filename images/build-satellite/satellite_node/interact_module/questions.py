# ------------------------------- udp message client questions -------------------------------
QUESTION_FOR_PACKET_COUNT = [
    {
        "type": "input",
        "name": "count",
        "message": "Please input the number of messages you want to send: ",
        "default": "100"
    }
]

QUESTION_FOR_INTERVAL = [
    {
        "type": "input",
        "name": "interval",
        "message": "Please input the send interval",
        "default": "0.01"
    }
]

QUESTION_FOR_PROTOCOL = [
    {
        "type": "list",
        "name": "protocol",
        "message": "Please select the network protocol: ",
        "choices": ["IP", "LIR"]
    }
]

QUESTION_FOR_DESTINATION = [
    {
        "type": "list",
        "name": "destination",
        "message": "Please select the satellite you want to send data to: "
    }
]

QUESTION_FOR_DESTINATION_PORT = [
    {
        "type": "input",
        "name": "port",
        "message": "Please input the destination port: ",
        "default": "31313"
    }
]

# ip option 字段总共存在 40 个字节, 对于每一个 8 字节来说，假设我们只使用 4 字节
QUESTION_FOR_BYTES = [
    {
        "type": "list",
        "name": "size",
        "message": "Please select the available BF size (bytes): ",
        "choices": ["4", "8", "12", "16", "20"]
    }
]

QUESTION_FOR_LIR_TRANSMISSION_PATTERN = [
    {
        "type": "list",
        "name": "transmission_pattern",
        "message": "Please select the transmission pattern: ",
        "choices": ["unicast", "multicast"]
    }
]

QUESTION_FOR_IP_TRANSMISSION_PATTERN = [
    {
        "type": "list",
        "name": "transmission_pattern",
        "message": "Please select the transmission pattern: ",
        "choices": ["unicast", "multi_unicast"]
    }
]

QUESTION_FOR_NUMBER_OF_DESTINATION = [
    {
        "type": "list",
        "name": "count",
        "message": "Please select the number of destination: ",
        "choices": ["2", "3", "4"]
    }
]

# ------------------------------- udp message client questions -------------------------------

# ------------------------------- udp message server questions -------------------------------
QUESTION_FOR_SERVER_LISTEN_PORT = [
    {
        "type": "input",
        "name": "port",
        "message": "Please input the server port: ",
        "default": "31313"
    }
]
# ------------------------------- udp message server questions -------------------------------

# ------------------------------- udp video client questions -------------------------------
QUESTION_FOR_VIDEO_SELECTION = [
    {
        "type": "list",
        "name": "video",
        "message": "Please select the video you want to transmit: ",
        "choices": []
    }
]
# ------------------------------- udp video client questions -------------------------------

# ------------------------------- attack method questions -------------------------------
QUESTION_FOR_ATTACK_METHOD_SELECTION = [
    {
        "type": "list",
        "name": "method",
        "message": "Please select the attack method you want to use: ",
        "choices": [
            "icmp_flood_attack",
            "udp_flood_attack",
            "tcp_syn_flood",
            "land_attack",
            "tcp_flags_attack",
            "fin_flood_attack"
        ]
    }
]

QUESTION_FOR_NUMBER_OF_ATTACK_THREADS = [
    {
        "type": "input",
        "name": "number_of_threads",
        "message": "Please input the number of attack threads:",
        "default": "5"
    }
]

QUESTION_FOR_ATTACK_DESTINATION = [
    {
        "type": "input",
        "name": "destination",
        "message": "Please input the destination address of the victim:",
        "default": "192.168.0.14"
    }
]

QUESTION_FOR_ATTACK_TIME = [
    {
        "type": "input",
        "name": "duration",
        "message": "Please input the duration of the attack in seconds:",
        "default": "10"
    }
]

QUESTION_FOR_PACKET_SIZE = [
    {
        "type": 'input',
        "name": "packet_size",
        "message": "Please input the payload of icmp packet (in bytes): ",
        "default": "10"
    }
]
# ------------------------------- attack method questions -------------------------------
