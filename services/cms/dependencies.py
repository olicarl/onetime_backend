from nameko.extensions import DependencyProvider
from kombu import Exchange, Queue, Connection
import json

class CommandPublisher(DependencyProvider):
    def setup(self):
        self.exchange = Exchange("gateway_commands", type="topic", durable=True)

    def get_dependency(self, worker_ctx):
        return CommandPublisherWrapper(self.container.config['AMQP_URI'], self.exchange)

class CommandPublisherWrapper:
    def __init__(self, amqp_uri, exchange):
        self.amqp_uri = amqp_uri
        self.exchange = exchange

    def publish(self, charger_id, command, args):
        payload = {
            "command": command,
            "args": args
        }
        routing_key = f"cmd.{charger_id}"
        
        with Connection(self.amqp_uri) as conn:
            producer = conn.Producer(serializer='json')
            producer.publish(
                payload,
                exchange=self.exchange,
                routing_key=routing_key,
                declare=[self.exchange]
            )
            print(f"Published to {routing_key}: {payload}")
