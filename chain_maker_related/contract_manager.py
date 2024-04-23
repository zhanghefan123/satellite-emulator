import os
from useful_tools import work_dir_manager as wdmm
from loguru import logger


class ContractRelatedCommand:
    CONTRACT_CREATION_COMMAND = r'''client contract user create --contract-name=fact --runtime-type=WASMER --byte-code-path=./testdata/claim-wasm-demo/rust-fact-2.0.0.wasm --version=1.0 --sdk-conf-path=./testdata/sdk_config.yml --admin-key-file-paths=./testdata/crypto-config/wx-org1.chainmaker.org/user/admin1/admin1.sign.key,./testdata/crypto-config/wx-org2.chainmaker.org/user/admin1/admin1.sign.key,./testdata/crypto-config/wx-org3.chainmaker.org/user/admin1/admin1.sign.key --admin-crt-file-paths=./testdata/crypto-config/wx-org1.chainmaker.org/user/admin1/admin1.sign.crt,./testdata/crypto-config/wx-org2.chainmaker.org/user/admin1/admin1.sign.crt,./testdata/crypto-config/wx-org3.chainmaker.org/user/admin1/admin1.sign.crt --sync-result=true --params="{}"'''

    CONTRACT_INVOCATION_COMMAND = r"""client contract user invoke --contract-name=fact --method=save --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_name\":\"name007\",\"file_hash\":\"ab3456df5799b87c77e7f88\",\"time\":\"6543234\"}" --sync-result=true"""

    CONTRACT_SEARCH_COMMAND = r'''client contract user get --contract-name=fact --method=find_by_file_hash --sdk-conf-path=./testdata/sdk_config.yml --params="{\"file_hash\":\"ab3456df5799b87c77e7f88\"}"'''


class ContractManager:
    def __init__(self, cmc_exe_dir: str, my_logger: logger):
        """
        进行 contractManager 的初始化
        :param cmc_exe_dir: cmc 可执行文件所在目录的绝对路径
        :param my_logger: 日志
        """
        self.cmc_exe_dir = cmc_exe_dir
        self.my_logger = my_logger

    def create_contract(self):
        """
        调用 cmc 可执行文件进行合约的创建
        """
        # 这是一个上下文管理器，在 with 块之中的工作目录被切换为 self.config_reader.abs_of_cmc_dir
        with wdmm.WorkDirManager(change_dir=self.cmc_exe_dir):
            # execute command
            print(os.getcwd())
            print(f"./cmc {ContractRelatedCommand.CONTRACT_CREATION_COMMAND}")
            r = os.popen(f"./cmc {ContractRelatedCommand.CONTRACT_CREATION_COMMAND}")
            text = r.read()
            r.close()
            self.my_logger.success(text)

    def invoke_contract(self):
        """
        调用 cmc 可执行文件进行合约的调用
        """
        # 这是一个上下文管理器，在 with 块之中的工作目录被切换为 self.config_reader.abs_of_cmc_dir
        with wdmm.WorkDirManager(change_dir=self.cmc_exe_dir):
            # execute command
            print(f"./cmc {ContractRelatedCommand.CONTRACT_INVOCATION_COMMAND}")
            r = os.popen(f"./cmc {ContractRelatedCommand.CONTRACT_INVOCATION_COMMAND}")
            text = r.read()
            r.close()
            self.my_logger.success(text)

    def search_contract(self):
        """
        调用 cmc 可执行文件进行合约的查询
        """
        # 这是一个上下文管理器，在 with 块之中的工作目录被切换为 self.config_reader.abs_of_cmc_dir
        with wdmm.WorkDirManager(change_dir=self.cmc_exe_dir):
            # execute command
            r = os.popen(f"./cmc {ContractRelatedCommand.CONTRACT_SEARCH_COMMAND}")
            text = r.read()
            r.close()
            self.my_logger.success(text)
