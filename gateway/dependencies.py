import aio_pika
from aio_nameko_proxy import AioNamekoProxy
from gateway.core.config import settings

# Global instances
nameko_proxy: AioNamekoProxy = None
rabbitmq_connection: aio_pika.Connection = None
rabbitmq_channel: aio_pika.Channel = None

async def get_nameko_proxy() -> AioNamekoProxy:
    global nameko_proxy
    if not nameko_proxy:
        nameko_proxy = AioNamekoProxy(
            amqp_uri=settings.RABBITMQ_URL,
            rpc_exchange=settings.NAMEKO_RPC_EXCHANGE
        )
        await nameko_proxy.start()
    return nameko_proxy

async def get_rabbitmq_channel() -> aio_pika.Channel:
    global rabbitmq_connection, rabbitmq_channel
    if not rabbitmq_connection:
        rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        rabbitmq_channel = await rabbitmq_connection.channel()
    return rabbitmq_channel

async def close_connections():
    global nameko_proxy, rabbitmq_connection
    if nameko_proxy:
        await nameko_proxy.stop()
    if rabbitmq_connection:
        await rabbitmq_connection.close()
