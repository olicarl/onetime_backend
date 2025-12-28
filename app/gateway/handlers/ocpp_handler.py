import json
from datetime import datetime
from ocpp.v16 import ChargePoint as v16ChargePoint
from ocpp.v16 import call
from ocpp.v16 import call_result
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.routing import on
from app.config import settings, logger
from app.services.events import event_bus, Events
from app.services.transactions import transaction_service

class ChargePoint(v16ChargePoint):
    
    @on(Action.BootNotification)
    async def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        logger.info(f"Received BootNotification from {self.id}")
        
        # Direct Async Call
        response = await transaction_service.process_boot(
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
        
        # Emit Event
        event_bus.emit(Events.METER_VALUES, payload)
        
        return call_result.MeterValuesPayload()
        
    @on(Action.Authorize)
    async def on_authorize(self, id_tag: str, **kwargs):
        logger.info(f"Received Authorize for {id_tag} from {self.id}")
        response = await transaction_service.authorize(id_tag=id_tag, **kwargs)
        return call_result.AuthorizePayload(
            id_tag_info=response.get("id_tag_info", {"status": "Invalid"})
        )

    @on(Action.Heartbeat)
    async def on_heartbeat(self, **kwargs):
        logger.info(f"Received Heartbeat from {self.id}")
        response = await transaction_service.heartbeat(**kwargs)
        return call_result.HeartbeatPayload(
            current_time=response.get("current_time", datetime.utcnow().isoformat())
        )

    @on(Action.StartTransaction)
    async def on_start_transaction(self, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        logger.info(f"Received StartTransaction from {self.id}")
        response = await transaction_service.start_transaction(
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
        response = await transaction_service.stop_transaction(
            meter_stop=meter_stop,
            timestamp=timestamp,
            transaction_id=transaction_id,
            **kwargs
        )
        return call_result.StopTransactionPayload(
            id_tag_info=response.get("id_tag_info")
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
        event_bus.emit(Events.STATUS_NOTIFICATION, payload)
        return call_result.StatusNotificationPayload()

    @on(Action.DataTransfer)
    async def on_data_transfer(self, vendor_id: str, **kwargs):
        logger.info(f"Received DataTransfer from {self.id}")
        response = await transaction_service.data_transfer(vendor_id=vendor_id, **kwargs)
        return call_result.DataTransferPayload(
            status=response.get("status", "Rejected"),
            data=response.get("data")
        )

    # Simplified: No diagnostics/firmware handlers for now to keep it small, 
    # but structure allows adding them easily with event_bus.emit

    async def send_admin_command(self, command_name: str, command_args: dict):
        """
        Generic handler to send any Chapter 5 command to the Charger.
        """
        try:
            if not hasattr(call, command_name):
                logger.error(f"Unknown command: {command_name}")
                return {"status": "Rejected", "error": "Unknown command"}

            command_class = getattr(call, command_name)
            request = command_class(**command_args)
            
            logger.info(f"Sending {command_name} to {self.id}: {command_args}")
            response = await self.call(request)
            logger.info(f"Received response for {command_name} from {self.id}: {response}")
            
            # Convert response to dict
            response_dict = {}
            for k, v in response.__dict__.items():
                if not k.startswith("_"):
                    response_dict[k] = v
            
            return response_dict

        except Exception as e:
            logger.error(f"Error sending {command_name} to {self.id}: {e}")
            return {"status": "Error", "error": str(e)}
