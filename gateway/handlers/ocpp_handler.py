import json
from datetime import datetime
from ocpp.v16 import ChargePoint as v16ChargePoint
from ocpp.v16 import call
from ocpp.v16 import call_result
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.routing import on
from gateway.dependencies import get_nameko_proxy, get_rabbitmq_channel
from gateway.core.config import settings, logger
import aio_pika

class ChargePoint(v16ChargePoint):
    async def _send_event(self, event_name: str, payload: dict):
        channel = await get_rabbitmq_channel()
        exchange = await channel.get_exchange("cms.events", ensure=False) # Assuming exchange exists or created elsewhere
        # If exchange creation is needed, we should do it in dependencies or main startup
        # For now, let's assume we publish to the default exchange or a specific topic exchange
        
        # Actually, the requirement says "publish an event to the cms.events exchange"
        # We'll use a topic exchange for events
        exchange = await channel.declare_exchange("cms.events", aio_pika.ExchangeType.TOPIC)
        
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        routing_key = event_name
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published event {event_name} to cms.events with routing key {routing_key}")

    @on(Action.BootNotification)
    async def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        logger.info(f"Received BootNotification from {self.id}")
        
        rpc = await get_nameko_proxy()
        # Call Nameko service 'cms_service' method 'process_boot'
        # Note: Nameko service name will be defined in the service file. Let's assume 'cms_service'.
        response = await rpc.cms_service.process_boot(
            vendor=charge_point_vendor,
            model=charge_point_model,
            **kwargs
        )
        
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=response.get("interval", 300),
            status=response.get("status", RegistrationStatus.accepted)
        )

    @on(Action.MeterValues)
    async def on_meter_values(self, **kwargs):
        logger.info(f"Received MeterValues from {self.id}")
        
        payload = {
            "charger_id": self.id,
            "payload": kwargs
        }
        
        # Publish to RabbitMQ
        await self._send_event("meter_values", payload)
        
    @on(Action.Authorize)
    async def on_authorize(self, id_tag: str, **kwargs):
        logger.info(f"Received Authorize for {id_tag} from {self.id}")
        rpc = await get_nameko_proxy()
        # RPC Call: Critical for auth
        response = await rpc.cms_service.authorize(id_tag=id_tag, **kwargs)
        return call_result.AuthorizePayload(
            id_tag_info=response.get("id_tag_info", {"status": "Invalid"})
        )

    @on(Action.Heartbeat)
    async def on_heartbeat(self, **kwargs):
        logger.info(f"Received Heartbeat from {self.id}")
        rpc = await get_nameko_proxy()
        # RPC Call: Sync time
        response = await rpc.cms_service.heartbeat(**kwargs)
        return call_result.HeartbeatPayload(
            current_time=response.get("current_time", datetime.utcnow().isoformat())
        )

    @on(Action.StartTransaction)
    async def on_start_transaction(self, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        logger.info(f"Received StartTransaction from {self.id}")
        rpc = await get_nameko_proxy()
        # RPC Call: Critical for billing
        response = await rpc.cms_service.start_transaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=timestamp,
            **kwargs
        )
        return call_result.StartTransactionPayload(
            transaction_id=response.get("transaction_id", 0),
            id_tag_info=response.get("id_tag_info", {"status": "Invalid"})
        )

    @on(Action.StopTransaction)
    async def on_stop_transaction(self, meter_stop: int, timestamp: str, transaction_id: int, **kwargs):
        logger.info(f"Received StopTransaction from {self.id}")
        rpc = await get_nameko_proxy()
        # RPC Call: Critical for billing
        response = await rpc.cms_service.stop_transaction(
            meter_stop=meter_stop,
            timestamp=timestamp,
            transaction_id=transaction_id,
            **kwargs
        )
        return call_result.StopTransactionPayload(
            id_tag_info=response.get("id_tag_info") # Optional
        )

    @on(Action.StatusNotification)
    async def on_status_notification(self, connector_id: int, error_code: str, status: str, **kwargs):
        logger.info(f"Received StatusNotification from {self.id}: {status}")
        payload = {
            "charger_id": self.id,
            "connector_id": connector_id,
            "error_code": error_code,
            "status": status,
            "payload": kwargs
        }
        # Event: Fire and forget
        await self._send_event("status_notification", payload)
        return call_result.StatusNotificationPayload()

    @on(Action.DataTransfer)
    async def on_data_transfer(self, vendor_id: str, **kwargs):
        logger.info(f"Received DataTransfer from {self.id}")
        rpc = await get_nameko_proxy()
        # RPC Call: Might need logic response
        response = await rpc.cms_service.data_transfer(vendor_id=vendor_id, **kwargs)
        return call_result.DataTransferPayload(
            status=response.get("status", "Rejected"),
            data=response.get("data")
        )

    @on(Action.DiagnosticsStatusNotification)
    async def on_diagnostics_status_notification(self, status: str, **kwargs):
        logger.info(f"Received DiagnosticsStatusNotification from {self.id}: {status}")
        payload = {
            "charger_id": self.id,
            "status": status,
            "payload": kwargs
        }
        # Event
        await self._send_event("diagnostics_status_notification", payload)
        return call_result.DiagnosticsStatusNotificationPayload()

    @on(Action.FirmwareStatusNotification)
    async def on_firmware_status_notification(self, status: str, **kwargs):
        logger.info(f"Received FirmwareStatusNotification from {self.id}: {status}")
        payload = {
            "charger_id": self.id,
            "status": status,
            "payload": kwargs
        }
        # Event
        await self._send_event("firmware_status_notification", payload)
        return call_result.FirmwareStatusNotificationPayload()

    async def send_admin_command(self, command_name: str, command_args: dict):
        """
        Generic handler to send any Chapter 5 command to the Charger.
        """
        try:
            # Dynamically get the Call class from ocpp.v16.call
            # e.g. "RemoteStartTransaction" -> call.RemoteStartTransaction
            if not hasattr(call, command_name):
                logger.error(f"Unknown command: {command_name}")
                return {"status": "Rejected", "error": "Unknown command"}

            command_class = getattr(call, command_name)
            
            # Instantiate the message
            # Note: The library validates the arguments against the schema
            request = command_class(**command_args)
            
            logger.info(f"Sending {command_name} to {self.id}: {command_args}")
            
            # Send and await response
            response = await self.call(request)
            
            logger.info(f"Received response for {command_name} from {self.id}: {response}")
            
            # Return the response as a dict
            # The response is a Payload object, we need to convert it to dict
            # The library's Payload objects usually have __dict__ or we can use vars()
            # But they are dataclasses or similar.
            # Let's try to return it as is, or convert to dict.
            # Nameko/RabbitMQ expects JSON serializable.
            
            # Helper to convert payload to dict
            response_dict = {}
            for k, v in response.__dict__.items():
                if not k.startswith("_"):
                    response_dict[k] = v
            
            return response_dict

        except Exception as e:
            logger.error(f"Error sending {command_name} to {self.id}: {e}")
            return {"status": "Error", "error": str(e)}
