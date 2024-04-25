import struct
from scapy.all import rdpcap
from scapy.layers.inet import IP, UDP


class AppLayer:
    def __init__(self):
        self.information = None
        self.length_in_bytes = None


class UdpLayer:
    def __init__(self):
        self.size_of_source_port = 2
        self.size_of_destination_port = 2
        self.size_of_current_and_upper_layer_length = 2
        self.size_of_checksum = 2
        self.total_header_size = sum(
            [self.size_of_source_port, self.size_of_destination_port,
             self.size_of_current_and_upper_layer_length, self.size_of_checksum]
        )
        self.source_port = None
        self.destination_port = None
        self.current_and_upper_layer_length = None
        self.checksum = None


class LirPacket:
    # current size  11
    def __init__(self):
        self.size_of_version_and_useless = 1
        self.size_of_protocol = 1
        self.size_of_id = 2
        self.size_of_header_length = 2
        self.size_of_total_length = 2
        self.size_of_frag_off = 2
        self.size_of_check_sum = 2
        self.size_of_source = 2
        self.size_of_destination = 2
        self.size_of_option = 4
        self.total_header_size = sum([self.size_of_version_and_useless,
                                      self.size_of_protocol,
                                      self.size_of_id,
                                      self.size_of_header_length,
                                      self.size_of_total_length,
                                      self.size_of_frag_off,
                                      self.size_of_check_sum,
                                      self.size_of_source,
                                      self.size_of_destination,
                                      self.size_of_option])
        self.version_and_useless = None
        self.protocol = None
        self.id = None
        self.header_length = None
        self.total_length = None
        self.frag_off = None
        self.checksum = None
        self.option = None
        self.source = None
        self.destination = None
        self.udp_layer = UdpLayer()  # 等待进行填充
        self.app_layer = AppLayer()

    def fill_the_network_layer_fields(self, field_values):
        (self.version_and_useless, self.protocol, self.id, self.header_length,
         self.total_length, self.frag_off,
         self.checksum, self.source, self.destination, *self.option) = field_values

    def fill_the_udp_layer_fields(self, field_values):
        (self.udp_layer.source_port, self.udp_layer.destination_port,
         self.udp_layer.current_and_upper_layer_length, self.udp_layer.checksum) = field_values

    def fill_the_app_layer(self, bytes):
        self.app_layer.length_in_bytes = len(bytes)
        self.app_layer.information = str(bytes, encoding="utf-8")

    def __str__(self):
        result = f"""
-------------------------------------------------------------------------- network layer  --------------------------------------------------------------------------
version_and_useless: {self.version_and_useless} bytes: {self.size_of_version_and_useless},
protocol: {self.protocol} bytes: {self.size_of_protocol},
header_length: {self.header_length} bytes: {self.size_of_header_length}
total_length: {self.total_length} bytes: {self.size_of_total_length}
frag_off: {self.frag_off} bytes: {self.size_of_frag_off}
check_sum: {self.checksum} bytes: {self.size_of_check_sum}
option: {self.option} bytes: {self.size_of_option}
source: {self.source} bytes: {self.size_of_source}
destination: {self.destination} bytes: {self.size_of_destination}
-------------------------------------------------------------------------- network layer  --------------------------------------------------------------------------
---------------------------------------------------------------------------- udp layer  ----------------------------------------------------------------------------
source_port: {self.udp_layer.source_port} bytes: {self.udp_layer.size_of_source_port}
destination_port: {self.udp_layer.destination_port} bytes: {self.udp_layer.size_of_destination_port}
current_and_upper_layer_length: {self.udp_layer.current_and_upper_layer_length} bytes: {self.udp_layer.size_of_current_and_upper_layer_length}
check_sum: {self.udp_layer.checksum} bytes: {self.udp_layer.size_of_checksum}
---------------------------------------------------------------------------- udp layer  ----------------------------------------------------------------------------
---------------------------------------------------------------------------- app layer  ----------------------------------------------------------------------------
information: {self.app_layer.information} bytes: {self.app_layer.length_in_bytes} 
---------------------------------------------------------------------------- app layer  ----------------------------------------------------------------------------
        """
        return result


class ICING:
    def __init__(self):
        self.size_of_single_hop = 42
        self.icing_part = None


class PcapAnalyzer:
    LIR_VERSION = 5

    def __init__(self, pcap_file_path: str):
        """
        :param pcap_file_path pcap 路径
        """
        self.pcap_file_path = pcap_file_path
        self.pcap_object = rdpcap(self.pcap_file_path)

    def analyze_all_packets(self):
        for packet in self.pcap_object:
            # MAC 层的 protocol 字段为
            if packet.haslayer(IP):
                network_part_of_packet = packet["IP"]
                version = network_part_of_packet.version
                source_ip_address = network_part_of_packet.src
                destination_ip_address = network_part_of_packet.dst
                # 如果 version 字段为 5 说明是 Lir Version
                if version == PcapAnalyzer.LIR_VERSION:
                    self.analyze_lir_packet(bytes(network_part_of_packet))

    def analyze_lir_packet(self, lir_packet_in_bytes):
        """
        进行 lir_packet 的分析
        """
        analyzed_lir_packet = LirPacket()
        result_of_lir_layer = struct.unpack(">2b7H4b", lir_packet_in_bytes[:analyzed_lir_packet.total_header_size])
        analyzed_lir_packet.fill_the_network_layer_fields(result_of_lir_layer)
        print(lir_packet_in_bytes[:analyzed_lir_packet.total_header_size])
        print(analyzed_lir_packet.total_header_size)
        icing = lir_packet_in_bytes[analyzed_lir_packet.total_header_size: (analyzed_lir_packet.total_header_size + 126)]
        print(icing)
        udp_in_bytes = lir_packet_in_bytes[analyzed_lir_packet.total_header_size + 126: (analyzed_lir_packet.total_header_size + 134)]
        result_of_udp_layer = struct.unpack(">HHHH", udp_in_bytes)
        analyzed_lir_packet.fill_the_udp_layer_fields(result_of_udp_layer)
        app_in_bytes = lir_packet_in_bytes[(analyzed_lir_packet.total_header_size + 134):]
        print(app_in_bytes)
        analyzed_lir_packet.fill_the_app_layer(app_in_bytes)
        print(analyzed_lir_packet)


if __name__ == "__main__":
    pcap_analyzer_tmp = PcapAnalyzer(pcap_file_path="lir_packet.pcapng")
    pcap_analyzer_tmp.analyze_all_packets()
