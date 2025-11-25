import os
import logging

class Settings:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    NAMEKO_RPC_EXCHANGE = os.getenv("NAMEKO_RPC_EXCHANGE", "nameko-rpc")
    GATEWAY_COMMANDS_EXCHANGE = "gateway_commands"

settings = Settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")
