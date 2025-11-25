import json
from nameko.rpc import rpc
from nameko.events import event_handler
from services.cms import logic

from services.cms.dependencies import CommandPublisher

class CmsService:
    name = "cms_service"
    
    command_publisher = CommandPublisher()

    @rpc
    def process_boot(self, vendor, model, **kwargs):
        """
        Handle BootNotification.
        Returns a plain dictionary with snake_case keys.
        """
        is_valid = logic.validate_charger(vendor, model)
        
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

    @event_handler("gateway", "meter_values")
    def handle_meter_values(self, payload):
        """
        Handle MeterValues event from Gateway.
        """
        charger_id = payload.get("charger_id")
        data = payload.get("payload")
        logic.save_meter_values(charger_id, data)
        print(f"Processed MeterValues for {charger_id}")

    @rpc
    def authorize(self, id_tag, **kwargs):
        """
        Handle Authorize.
        """
        # Mock logic
        return {"id_tag_info": {"status": "Accepted", "parent_id_tag": None, "expiry_date": None}}

    @rpc
    def heartbeat(self, **kwargs):
        """
        Handle Heartbeat.
        """
        from datetime import datetime
        return {"current_time": datetime.utcnow().isoformat()}

    @rpc
    def start_transaction(self, connector_id, id_tag, meter_start, timestamp, **kwargs):
        """
        Handle StartTransaction.
        """
        # Mock logic: Generate transaction ID
        return {
            "transaction_id": 12345,
            "id_tag_info": {"status": "Accepted"}
        }

    @rpc
    def stop_transaction(self, meter_stop, timestamp, transaction_id, **kwargs):
        """
        Handle StopTransaction.
        """
        # Mock logic
        return {"id_tag_info": {"status": "Accepted"}}

    @rpc
    def data_transfer(self, vendor_id, **kwargs):
        """
        Handle DataTransfer.
        """
        return {"status": "Accepted", "data": None}

    @event_handler("gateway", "status_notification")
    def handle_status_notification(self, payload):
        print(f"StatusNotification: {payload}")

    @event_handler("gateway", "diagnostics_status_notification")
    def handle_diagnostics_status_notification(self, payload):
        print(f"DiagnosticsStatusNotification: {payload}")

    @event_handler("gateway", "firmware_status_notification")
    def handle_firmware_status_notification(self, payload):
        print(f"FirmwareStatusNotification: {payload}")

    # --- Chapter 5: Operations Initiated by Central System (Triggers) ---
    
    def _publish(self, charger_id, command, args):
        self.command_publisher.publish(charger_id, command, args)
        return {"status": "Published"}

    @rpc
    def trigger_remote_start(self, charger_id, id_tag, **kwargs):
        return self._publish(charger_id, "RemoteStartTransaction", {"id_tag": id_tag, **kwargs})

    @rpc
    def trigger_remote_stop(self, charger_id, transaction_id, **kwargs):
        return self._publish(charger_id, "RemoteStopTransaction", {"transaction_id": transaction_id, **kwargs})

    @rpc
    def trigger_reset(self, charger_id, type="Soft", **kwargs):
        return self._publish(charger_id, "Reset", {"type": type, **kwargs})

    @rpc
    def trigger_unlock_connector(self, charger_id, connector_id, **kwargs):
        return self._publish(charger_id, "UnlockConnector", {"connector_id": connector_id, **kwargs})

    @rpc
    def trigger_change_availability(self, charger_id, connector_id, type, **kwargs):
        return self._publish(charger_id, "ChangeAvailability", {"connector_id": connector_id, "type": type, **kwargs})

    @rpc
    def trigger_change_configuration(self, charger_id, key, value, **kwargs):
        return self._publish(charger_id, "ChangeConfiguration", {"key": key, "value": value, **kwargs})

    @rpc
    def trigger_clear_cache(self, charger_id, **kwargs):
        return self._publish(charger_id, "ClearCache", {**kwargs})

    @rpc
    def trigger_clear_charging_profile(self, charger_id, **kwargs):
        return self._publish(charger_id, "ClearChargingProfile", {**kwargs})

    @rpc
    def trigger_data_transfer(self, charger_id, vendor_id, **kwargs):
        return self._publish(charger_id, "DataTransfer", {"vendor_id": vendor_id, **kwargs})

    @rpc
    def trigger_get_composite_schedule(self, charger_id, connector_id, duration, **kwargs):
        return self._publish(charger_id, "GetCompositeSchedule", {"connector_id": connector_id, "duration": duration, **kwargs})

    @rpc
    def trigger_get_configuration(self, charger_id, **kwargs):
        return self._publish(charger_id, "GetConfiguration", {**kwargs})

    @rpc
    def trigger_get_diagnostics(self, charger_id, location, **kwargs):
        return self._publish(charger_id, "GetDiagnostics", {"location": location, **kwargs})

    @rpc
    def trigger_get_local_list_version(self, charger_id, **kwargs):
        return self._publish(charger_id, "GetLocalListVersion", {**kwargs})

    @rpc
    def trigger_reserve_now(self, charger_id, connector_id, expiry_date, id_tag, reservation_id, **kwargs):
        return self._publish(charger_id, "ReserveNow", {
            "connector_id": connector_id,
            "expiry_date": expiry_date,
            "id_tag": id_tag,
            "reservation_id": reservation_id,
            **kwargs
        })

    @rpc
    def trigger_cancel_reservation(self, charger_id, reservation_id, **kwargs):
        return self._publish(charger_id, "CancelReservation", {"reservation_id": reservation_id, **kwargs})

    @rpc
    def trigger_send_local_list(self, charger_id, list_version, update_type, **kwargs):
        return self._publish(charger_id, "SendLocalList", {"list_version": list_version, "update_type": update_type, **kwargs})

    @rpc
    def trigger_set_charging_profile(self, charger_id, connector_id, cs_charging_profiles, **kwargs):
        return self._publish(charger_id, "SetChargingProfile", {"connector_id": connector_id, "cs_charging_profiles": cs_charging_profiles, **kwargs})

    @rpc
    def trigger_trigger_message(self, charger_id, requested_message, **kwargs):
        return self._publish(charger_id, "TriggerMessage", {"requested_message": requested_message, **kwargs})

    @rpc
    def trigger_update_firmware(self, charger_id, location, retrieve_date, **kwargs):
        return self._publish(charger_id, "UpdateFirmware", {"location": location, "retrieve_date": retrieve_date, **kwargs})

