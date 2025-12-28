from datetime import datetime
from app.services import mock_logic as logic
from app.services.events import event_bus, Events
from app.gateway.connection_manager import manager

class TransactionService:
    
    def __init__(self):
        # Subscribe to events
        event_bus.on(Events.METER_VALUES, self.handle_meter_values)
        event_bus.on(Events.STATUS_NOTIFICATION, self.handle_status_notification)

    async def process_boot(self, vendor, model, **kwargs):
        """
        Handle BootNotification.
        """
        is_valid = await logic.validate_charger(vendor, model)
        
        if is_valid:
            return {
                "status": "Accepted",
                "interval": 300
            }
        else:
            return {
                "status": "Rejected",
                "interval": 0
            }

    async def handle_meter_values(self, payload):
        """
        Handle MeterValues event from Gateway.
        """
        charger_id = payload.get("charger_id")
        data = payload.get("payload")
        # Logic needs to be async or run in executor if blocking
        await logic.save_meter_values(charger_id, data)
        print(f"Processed MeterValues for {charger_id}")

    async def authorize(self, id_tag, **kwargs):
        """
        Handle Authorize.
        """
        return {"id_tag_info": {"status": "Accepted", "parent_id_tag": None, "expiry_date": None}}

    async def heartbeat(self, **kwargs):
        """
        Handle Heartbeat.
        """
        return {"current_time": datetime.utcnow().isoformat()}

    async def start_transaction(self, connector_id, id_tag, meter_start, timestamp, **kwargs):
        """
        Handle StartTransaction.
        """
        return {
            "transaction_id": 12345,
            "id_tag_info": {"status": "Accepted"}
        }

    async def stop_transaction(self, meter_stop, timestamp, transaction_id, **kwargs):
        """
        Handle StopTransaction.
        """
        return {"id_tag_info": {"status": "Accepted"}}

    async def data_transfer(self, vendor_id, **kwargs):
        """
        Handle DataTransfer.
        """
        return {"status": "Accepted", "data": None}

    async def handle_status_notification(self, payload):
        print(f"StatusNotification: {payload}")

    # --- Outgoing Commands (Triggered by API, executed via Connection Manager) ---
    async def _send(self, charger_id, command, args):
        socket = manager.get_connection(charger_id)
        if not socket:
            return {"status": "Offline"}
        
        # In a real app, this would use the ChargePoint instance to call the method
        # But for now, we assume the gateway has a mechanism to send this.
        # We need to bridge this later.
        pass

# Global Instance
transaction_service = TransactionService()
