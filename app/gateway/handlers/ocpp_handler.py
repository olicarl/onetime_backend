import json
from datetime import datetime
from ocpp.v16 import ChargePoint as v16ChargePoint
from ocpp.v16 import call
from ocpp.v16 import call_result
from ocpp.v16.enums import Action, RegistrationStatus
from ocpp.routing import on
from app.config import settings, logger
from app.services.events import event_bus, Events
from app.services.station_service import station_service
from app.services.authorization_service import authorization_service
from app.services.transactions import transaction_service
from app.services.logging_service import logging_service

class ChargePoint(v16ChargePoint):
    
    async def route_message(self, raw_msg):
        try:
            msg = json.loads(raw_msg)
            msg_type = msg[0]
            action = "Unknown"
            payload = {}
            type_str = "UNKNOWN"
            
            if msg_type == 2: # CALL
                type_str = "CALL"
                action = msg[2]
                payload = msg[3]
            elif msg_type == 3: # CALLRESULT
                type_str = "CALLRESULT"
                action = "Response" 
                payload = msg[2]
            elif msg_type == 4: # CALLERROR
                type_str = "CALLERROR"
                action = "Error"
                payload = {"code": msg[2], "description": msg[3], "details": msg[4]}
                
            await logging_service.log_message(
                station_id=self.id,
                direction="Incoming",
                message_type=type_str,
                action=action,
                payload=payload
            )
        except Exception as e:
            logger.error(f"Error logging incoming message: {e}")
            
        await super().route_message(raw_msg)

    async def call(self, payload, suppress=False):
        try:
            # payload is the Request object e.g. Call(unique_id, action, payload)
            # Actually ocpp lib 'call' takes the *Operation* object (e.g. RemoteStartTransaction), 
            # and wraps it in a Call object internally. 
            # Wait, looking at ocpp lib:
            # await self.call(call.RemoteStartTransaction(...))
            # The argument 'payload' IS the operation object (which has 'action' attribute)
            
            action = getattr(payload, 'action', 'Unknown')
            # Extract data
            data = {}
            if hasattr(payload, '__dict__'):
                 data = {k: v for k, v in payload.__dict__.items() if not k.startswith('_')}
            
            await logging_service.log_message(
                station_id=self.id,
                direction="Outgoing",
                message_type="CALL",
                action=action,
                payload=data
            )
        except Exception as e:
            logger.error(f"Error logging outgoing message: {e}")
            
        return await super().call(payload, suppress)

    @on(Action.boot_notification)
    async def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        logger.info(f"Received BootNotification from {self.id}")
        
        response = await station_service.process_boot(
            charger_id=self.id,
            vendor=charge_point_vendor,
            model=charge_point_model,
            **kwargs
        )
        
        return call_result.BootNotification(
            current_time=response.get("current_time"),
            interval=response.get("interval", 300),
            status=response.get("status", RegistrationStatus.accepted)
        )

    @on(Action.meter_values)
    async def on_meter_values(self, connector_id: int = None, transaction_id: int = None, **kwargs):
        logger.info(f"Received MeterValues from {self.id}")
        
        # Async background processing
        await transaction_service.handle_meter_values(
            charger_id=self.id,
            payload={
                "connector_id": connector_id,
                "transaction_id": transaction_id,
                "meter_value": kwargs.get("meter_value")
            }
        )
        
        return call_result.MeterValues()
        
    @on(Action.authorize)
    async def on_authorize(self, id_tag: str, **kwargs):
        logger.info(f"Received Authorize for {id_tag} from {self.id}")
        response = await authorization_service.authorize(id_tag=id_tag, **kwargs)
        return call_result.Authorize(
            id_tag_info=response.get("id_tag_info")
        )

    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        logger.info(f"Received Heartbeat from {self.id}")
        response = await station_service.heartbeat(charger_id=self.id, **kwargs)
        return call_result.Heartbeat(
            current_time=response.get("current_time", datetime.utcnow().isoformat())
        )

    @on(Action.start_transaction)
    async def on_start_transaction(self, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        logger.info(f"Received StartTransaction from {self.id}")
        response = await transaction_service.start_transaction(
            charger_id=self.id,
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=timestamp,
            **kwargs
        )
        return call_result.StartTransaction(
            transaction_id=response.get("transaction_id", 0),
            id_tag_info=response.get("id_tag_info")
        )

    @on(Action.stop_transaction)
    async def on_stop_transaction(self, meter_stop: int, timestamp: str, transaction_id: int, **kwargs):
        logger.info(f"Received StopTransaction from {self.id}")
        response = await transaction_service.stop_transaction(
            charger_id=self.id,
            meter_stop=meter_stop,
            timestamp=timestamp,
            transaction_id=transaction_id,
            **kwargs
        )
        return call_result.StopTransaction(
            id_tag_info=response.get("id_tag_info")
        )

    @on(Action.status_notification)
    async def on_status_notification(self, connector_id: int, error_code: str, status: str, **kwargs):
        logger.info(f"Received StatusNotification from {self.id}: {status}")
        await station_service.handle_status_notification(
            charger_id=self.id,
            connector_id=connector_id,
            status=status,
            error_code=error_code,
            **kwargs
        )
        return call_result.StatusNotification()

    @on(Action.data_transfer)
    async def on_data_transfer(self, vendor_id: str, **kwargs):
        logger.info(f"Received DataTransfer from {self.id}")
        response = await transaction_service.data_transfer(vendor_id=vendor_id, **kwargs)
        return call_result.DataTransfer(
            status=response.get("status", "Rejected"),
            data=response.get("data")
        )

    @on(Action.log_status_notification)
    async def on_log_status_notification(self, status: str, request_id: int, **kwargs):
        logger.info(f"Received LogStatusNotification from {self.id}: {status}")
        await transaction_service.log_status_notification(status, request_id, **kwargs)
        return call_result.LogStatusNotification()

    @on(Action.security_event_notification)
    async def on_security_event_notification(self, type: str, timestamp: str, **kwargs):
        logger.info(f"Received SecurityEventNotification from {self.id}: {type}")
        await transaction_service.security_event_notification(type, timestamp, **kwargs)
        return call_result.SecurityEventNotification()

    @on(Action.sign_certificate)
    async def on_sign_certificate(self, csr: str, **kwargs):
        logger.info(f"Received SignCertificate from {self.id}")
        response = await transaction_service.sign_certificate(csr, **kwargs)
        return call_result.SignCertificate(
            status=response.get("status", "Accepted")
        )

    @on(Action.signed_firmware_status_notification)
    async def on_signed_firmware_status_notification(self, status: str, request_id: int, **kwargs):
        logger.info(f"Received SignedFirmwareStatusNotification from {self.id}: {status}")
        await transaction_service.signed_firmware_status_notification(status, request_id, **kwargs)
        return call_result.SignedFirmwareStatusNotification()

    # --- Outgoing Calls (Central System -> Charge Point) ---

    async def remote_start_transaction(self, id_tag: str, connector_id: int = None, charging_profile: dict = None):
        request = call.RemoteStartTransaction(id_tag=id_tag, connector_id=connector_id, charging_profile=charging_profile)
        return await self.call(request)

    async def remote_stop_transaction(self, transaction_id: int):
        request = call.RemoteStopTransaction(transaction_id=transaction_id)
        return await self.call(request)

    async def reset(self, type: str):
        request = call.Reset(type=type)
        return await self.call(request)

    async def unlock_connector(self, connector_id: int):
        request = call.UnlockConnector(connector_id=connector_id)
        return await self.call(request)

    async def change_configuration(self, key: str, value: str):
        request = call.ChangeConfiguration(key=key, value=value)
        return await self.call(request)

    async def get_configuration(self, keys: list = None):
        request = call.GetConfiguration(key=keys)
        return await self.call(request)

    async def clear_cache(self):
        request = call.ClearCache()
        return await self.call(request)

    async def change_availability(self, connector_id: int, type: str):
        request = call.ChangeAvailability(connector_id=connector_id, type=type)
        return await self.call(request)

    async def get_diagnostics(self, location: str, **kwargs):
        request = call.GetDiagnostics(location=location, **kwargs)
        return await self.call(request)

    async def update_firmware(self, location: str, retrieve_date: str, **kwargs):
        request = call.UpdateFirmware(location=location, retrieve_date=retrieve_date, **kwargs)
        return await self.call(request)

    async def reserve_now(self, connector_id: int, expiry_date: str, id_tag: str, reservation_id: int, **kwargs):
        request = call.ReserveNow(connector_id=connector_id, expiry_date=expiry_date, id_tag=id_tag, reservation_id=reservation_id, **kwargs)
        return await self.call(request)

    async def cancel_reservation(self, reservation_id: int):
        request = call.CancelReservation(reservation_id=reservation_id)
        return await self.call(request)

    async def set_charging_profile(self, connector_id: int, cs_charging_profiles: dict):
        request = call.SetChargingProfile(connector_id=connector_id, cs_charging_profiles=cs_charging_profiles)
        return await self.call(request)

    async def get_composite_schedule(self, connector_id: int, duration: int, **kwargs):
        request = call.GetCompositeSchedule(connector_id=connector_id, duration=duration, **kwargs)
        return await self.call(request)

    async def clear_charging_profile(self, **kwargs):
        request = call.ClearChargingProfile(**kwargs)
        return await self.call(request)

    async def trigger_message(self, requested_message: str, connector_id: int = None):
        request = call.TriggerMessage(requested_message=requested_message, connector_id=connector_id)
        return await self.call(request)

    async def get_local_list_version(self):
        request = call.GetLocalListVersion()
        return await self.call(request)

    async def send_local_list(self, list_version: int, update_type: str, local_authorization_list: list = None):
        request = call.SendLocalList(list_version=list_version, update_type=update_type, local_authorization_list=local_authorization_list or [])
        return await self.call(request)

    # Generic Fallback
    async def send_admin_command(self, command_name: str, command_args: dict):
        """
        Generic handler to send any Chapter 5 command to the Charger.
        """
        try:
            # Check if we have a specific method first (snake_case)
            # e.g. RemoteStartTransaction -> remote_start_transaction
            import re
            method_name = re.sub(r'(?<!^)(?=[A-Z])', '_', command_name).lower()
            
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                logger.info(f"Using specific method {method_name} for {command_name}")
                response = await method(**command_args)
            else: 
                # Fallback to generic reflection
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
