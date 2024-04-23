import yaml
import datetime
from entities import entity as em
from entities import constellation_type as ctm
from const_vars import const_vars as cvm


class ConfigReader:

    def __init__(self, *params):
        """
        能实现多参数重载
        :param params: 传入的参数
        :exception TypeError
        """
        self.num_of_orbit = None          # 轨道数量
        self.sat_per_orbit = None         # 每轨道卫星数量
        self.network_ip_address = None    # ip 地址
        self.update_queue_name = None     # rabbitmq 队列名称
        self.ground_infos = None          # 地面站的名称以及位置
        self.calculation_interval = None  # 计算的间隔
        self.speed_rate = None            # 时间的倍率 1s 相当于实际的多少秒
        self.constellation_start_time = None  # 星座开始的时间 年|月|日|时|分|秒
        self.constellation_type = None

        self.max_generated_subnet = None  # 最大生成子网数量
        self.base_network_address = None
        self.satellite_image_name = None
        self.ground_image_name = None
        self.number_of_satellites = None
        self.base_url = None
        self.listening_port = None

        self.number_of_cm_node = None
        self.chain_image_name = None
        self.rabbitmq_image_name = None
        self.abs_of_prepare = None
        self.abs_of_crypto_config = None
        self.abs_of_testdata = None
        self.abs_of_chainconfig = None
        self.abs_of_build_config = None
        self.abs_of_multi_node = None
        self.abs_of_cmc_dir = None
        self.abs_of_frr_configuration = None
        self.abs_of_routes_configuration = None
        self.abs_of_address_configuration = None
        self.abs_of_lir_configuration = None
        self.abs_of_videos_storage = None

        self.default_bloom_filter_length = None
        self.default_hash_seed = None
        self.default_number_of_hash_funcs = None

        self.p2p_port = None
        self.rpc_port = None

        self.topology_cn_node = None
        self.generate_leo_or_chain = None
        self.start_frr = None
        self.lir_enabled = None

        self.node_type = None
        self.node_prefix = None

        if len(params) <= 2:
            self.load(*params)
        else:
            raise TypeError(f"accept parameters 0 1 2, however {len(params)} params are given")

    def load(self, configuration_file_path: str = "resources/constellation_config.yml",
             selected_config: str = "default"):
        """
        进行配置文件的加载
        :param configuration_file_path 配置文件的路径
        :param selected_config 选择的配置
        :exception yaml.parser.ParserError | ValueError | TypeError
        :return:
        """
        with open(file=configuration_file_path, mode='r', encoding="utf-8") as f:
            selected_config_data = yaml.load(stream=f, Loader=yaml.FullLoader).get(selected_config, None)
        if selected_config_data is not None:
            self.num_of_orbit = int(selected_config_data.get("num_of_orbit", None))
            self.sat_per_orbit = int(selected_config_data.get("sat_per_orbit", None))
            self.network_ip_address = selected_config_data.get("network_ip_address", None)
            self.update_queue_name = selected_config_data.get("update_queue_name", None)
            self.ground_infos = selected_config_data.get("ground_infos", None)
            self.calculation_interval = int(selected_config_data.get("calculation_interval", None))
            self.speed_rate = int(selected_config_data.get("speed_rate", None))
            self.constellation_start_time = selected_config_data.get("constellation_start_time", None)
            self.constellation_type = selected_config_data.get("constellation_type", None)
            self.resolve_constellation_start_time()
            self.resolve_constellation_type()

            self.max_generated_subnet = int(selected_config_data.get("max_generated_subnet", None))
            self.base_network_address = selected_config_data.get("base_network_address", None)
            self.satellite_image_name = selected_config_data.get("satellite_image_name", None)
            self.ground_image_name = selected_config_data.get("ground_image_name", None)
            self.number_of_satellites = self.num_of_orbit * self.sat_per_orbit
            self.base_url = selected_config_data.get("base_url", None)
            self.listening_port = int(selected_config_data.get("listening_port", None))

            self.number_of_cm_node = self.num_of_orbit * self.sat_per_orbit
            self.chain_image_name = selected_config_data.get("chain_image_name", None)
            self.rabbitmq_image_name = selected_config_data.get("rabbitmq_image_name", None)
            self.abs_of_prepare = selected_config_data.get("abs_of_prepare", None)
            self.abs_of_crypto_config = selected_config_data.get("abs_of_crypto_config", None)
            self.abs_of_testdata = selected_config_data.get("abs_of_testdata", None)
            self.abs_of_chainconfig = selected_config_data.get("abs_of_chainconfig", None)
            self.abs_of_build_config = selected_config_data.get("abs_of_build_config", None)
            self.abs_of_multi_node = selected_config_data.get("abs_of_multi_node", None)
            self.abs_of_cmc_dir = selected_config_data.get("abs_of_cmc_dir", None)
            self.abs_of_frr_configuration = selected_config_data.get("abs_of_frr_configuration", None)
            self.abs_of_routes_configuration = selected_config_data.get("abs_of_routes_configuration", None)
            self.abs_of_address_configuration = selected_config_data.get("abs_of_address_configuration", None)
            self.abs_of_lir_configuration = selected_config_data.get("abs_of_lir_configuration", None)
            self.abs_of_videos_storage = selected_config_data.get("abs_of_videos_storage", None)

            self.default_bloom_filter_length = int(selected_config_data.get("default_bloom_filter_length", None))
            self.default_hash_seed = int(selected_config_data.get("default_hash_seed", None))
            self.default_number_of_hash_funcs = int(selected_config_data.get("default_number_of_hash_funcs", None))

            self.p2p_port = int(selected_config_data.get("p2p_port", None))
            self.rpc_port = int(selected_config_data.get("rpc_port", None))

            self.topology_cn_node = int(selected_config_data.get("topology_cn_node", None))
            self.generate_leo_or_chain = selected_config_data.get("generate_leo_or_chain", None)
            self.start_frr = int(selected_config_data.get("start_frr", None))
            self.lir_enabled = int(selected_config_data.get("lir_enabled", None))
            self.resolve_node_type_and_prefix()

            if not all([self.num_of_orbit, self.sat_per_orbit, self.network_ip_address,
                        self.update_queue_name, self.ground_infos, self.calculation_interval, self.speed_rate,
                        self.constellation_start_time, self.constellation_type, self.node_type,
                        self.max_generated_subnet, self.base_network_address,
                        self.satellite_image_name, self.ground_image_name,
                        self.number_of_satellites, self.base_url, self.listening_port,
                        self.number_of_cm_node, self.chain_image_name, self.rabbitmq_image_name,
                        self.abs_of_prepare, self.abs_of_crypto_config, self.abs_of_testdata,
                        self.abs_of_chainconfig, self.abs_of_build_config, self.abs_of_multi_node,
                        self.abs_of_cmc_dir, self.abs_of_frr_configuration, self.abs_of_routes_configuration,
                        self.abs_of_address_configuration,
                        self.abs_of_lir_configuration, self.abs_of_videos_storage,
                        self.default_bloom_filter_length, self.default_hash_seed, self.default_number_of_hash_funcs,
                        self.p2p_port, self.rpc_port,
                        self.topology_cn_node, self.generate_leo_or_chain]):
                raise ValueError(f"not all parameter get its value: {str(self)}")
        else:
            raise ValueError(f'cannot find selected config "{selected_config}"')

    def resolve_constellation_start_time(self):
        year, month, date, hour, minute, second = self.constellation_start_time.split("|")
        self.constellation_start_time = datetime.datetime(int(year), int(month), int(date), int(hour), int(minute), int(second))

    def resolve_constellation_type(self):
        if self.constellation_type == "WALKER_STAR":
            self.constellation_type = ctm.ConstellationType.WALKER_STAR_CONSTELLATION
        elif self.constellation_type == "WALKER_DELTA":
            self.constellation_type = ctm.ConstellationType.WALKER_DELTA_CONSTELLATION
        else:
            raise ValueError("unsupported constellation type")

    def resolve_node_type_and_prefix(self):
        if self.generate_leo_or_chain == "leo":
            self.node_type = em.EntityType.SATELLITE_NODE
            self.node_prefix = cvm.SATELLITE_NODE_PREFIX
        elif self.generate_leo_or_chain == "chain":
            self.node_type = em.EntityType.CONSENSUS_NODE
            self.node_prefix = cvm.CONSENSUS_NODE_PREFIX
        else:
            raise ValueError("unsupported generate")

    def __str__(self):
        """
        :return: 配置对象的字符串表示
        """
        format_str = f"""
        -----------------[configuration]----------------
        num_of_orbit: {self.num_of_orbit}
        sat_per_orbit: {self.sat_per_orbit}
        network_ip_address: {self.network_ip_address}
        update_queue_name: {self.update_queue_name}
        ground_infos: {self.ground_infos}
        calculation_interval: {self.calculation_interval}
        speed_rate: {self.speed_rate}
        constellation_start_time: {self.constellation_start_time}
        constellation_type: {self.constellation_type}
        
        max_generated_subnet: {self.max_generated_subnet}
        base_network_address: {self.base_network_address}
        satellite_image_name: {self.satellite_image_name}
        ground_image_name: {self.ground_image_name}
        number_of_satellites: {self.number_of_satellites}
        base_url: {self.base_url}
        listening_port: {self.listening_port}
        
        number_of_cm_node: {self.number_of_cm_node}
        chain_image_name: {self.chain_image_name}
        rabbitmq_image_name: {self.rabbitmq_image_name}
        abs_of_prepare: {self.abs_of_prepare}
        abs_of_crypto_config: {self.abs_of_crypto_config}
        abs_of_testdata: {self.abs_of_testdata}
        abs_of_chainconfig: {self.abs_of_chainconfig}
        abs_of_build_config: {self.abs_of_build_config}
        abs_of_multi_node: {self.abs_of_multi_node}
        abs_of_cmc_dir: {self.abs_of_cmc_dir}
        abs_of_frr_configuration: {self.abs_of_frr_configuration}
        abs_of_routes_configuration: {self.abs_of_routes_configuration}
        abs_of_address_configuration: {self.abs_of_address_configuration}
        abs_of_lir_configuration: {self.abs_of_lir_configuration}
        abs_of_videos_storage: {self.abs_of_videos_storage}
        
        default_bloom_filter_length: {self.default_bloom_filter_length}
        default_hash_seed: {self.default_hash_seed}
        default_number_of_hash_funcs: {self.default_number_of_hash_funcs}
        
        p2p_port: {self.p2p_port}
        rpc_port: {self.rpc_port}
        
        topology_cn_node: {self.topology_cn_node}
        generate_leo_or_chain: {self.generate_leo_or_chain}
        start_frr: {self.start_frr}
        lir_enabled: {self.lir_enabled}
        
        node_type: {self.node_type}
        -----------------[configuration]----------------
        """
        return format_str


if __name__ == "__main__":
    docker_client_config = ConfigReader("../resources/constellation_config.yml")
    print(docker_client_config)
