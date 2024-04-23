from services.message_queue_service import rabbitmq_service as rsm
from docker_client import docker_client_http_impl as dchim
from config import config_reader as crm
import asyncio


def start_rabbitmq_service():
    config_reader = crm.ConfigReader()
    docker_client = dchim.DockerClientHttpImpl(config_reader.base_url)
    rabbit_mq_service = rsm.RabbitMqService(config_reader, docker_client)
    asyncio.run(rabbit_mq_service.start())


if __name__ == "__main__":
    start_rabbitmq_service()