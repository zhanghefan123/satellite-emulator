import asyncio
from loguru import logger
from config import config_reader as crm
from docker_client import docker_client_http_impl as dchim


class RabbitMqService:

    def __init__(self, config_reader: crm.ConfigReader, docker_client: dchim.DockerClientHttpImpl):
        self.config_reader = config_reader
        self.docker_client = docker_client
        self.container_id = None

    async def start(self):
        """
        进行 rabbitmq 容器的创建和启动
        :return:
        """
        if self.container_id is None:
            service_name = "rabbitmq_server"
            task_list = []
            # 端口映射
            # ---------------------------------------------------------
            exposed_ports = {
                # f"{self.config_reader.p2p_port + (index)}/tcp": {},
                f"15672/tcp": {},
                f"5672/tcp": {}
            }
            port_bindings = {
                # f"{self.config_reader.p2p_port + (index)}/tcp": [
                #     {
                #         "HostIp": "",
                #         "HostPort": f"{self.config_reader.p2p_port + (index)}"
                #     }
                # ]
                # ,
                f"15672/tcp": [
                    {
                        "HostIp": "",
                        "HostPort": "15672"
                    }
                ],
                f"5672/tcp": [
                    {
                        "HostIp": "",
                        "HostPort": "5672"
                    }
                ],
            }
            # ---------------------------------------------------------
            task = asyncio.create_task(
                self.docker_client.create_container(image_name=self.config_reader.rabbitmq_image_name,
                                                    exposed_ports=exposed_ports,
                                                    port_bindings=port_bindings,
                                                    container_name=service_name,
                                                    special_service=True))
            task_list.append(task)
            await asyncio.wait(task_list, return_when=asyncio.ALL_COMPLETED)
            container_id = str(task_list[0].result())
            self.container_id = container_id
            task = asyncio.create_task(self.docker_client.start_container(container_id=container_id))
            task_list.clear()
            task_list.append(task)
            await asyncio.wait(task_list, return_when=asyncio.ALL_COMPLETED)
        else:
            logger.error("rabbit mq service is already running")

    async def delete(self):
        """
        进行 rabbitmq 容器的停止和删除
        :return:
        """
        if self.container_id is not None:
            task_list = []
            task = asyncio.create_task(self.docker_client.stop_container(self.container_id))
            task_list.append(task)
            await asyncio.wait(task_list, return_when=asyncio.ALL_COMPLETED)
            task_list.clear()
            task = asyncio.create_task(self.docker_client.delete_container(container_id=self.container_id))
            task_list.append(task)
            await asyncio.wait(task_list, return_when=asyncio.ALL_COMPLETED)
