import asyncio
import logging
import websockets
from datetime import datetime
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
from ocpp.v16.enums import RegistrationStatus, AuthorizationStatus, ChargePointStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_flow")

class SimulatedChargePoint(cp):
    
    async def boot(self):
        request = call.BootNotification(
            charge_point_model="TestModel",
            charge_point_vendor="TestVendor"
        )
        response = await self.call(request)
        logger.info(f"BootNotification: {response}")
        return response

    async def heartbeat(self):
        request = call.Heartbeat()
        response = await self.call(request)
        logger.info(f"Heartbeat: {response}")
        return response

    async def status_notification(self, connector_id, status, error_code="NoError"):
        request = call.StatusNotification(
            connector_id=connector_id,
            error_code=error_code,
            status=status
        )
        response = await self.call(request)
        logger.info(f"StatusNotification ({status}): {response}")
        return response

    async def authorize(self, id_tag):
        request = call.Authorize(id_tag=id_tag)
        response = await self.call(request)
        logger.info(f"Authorize: {response}")
        return response

    async def start_transaction(self, connector_id, id_tag, meter_start, timestamp):
        request = call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=timestamp
        )
        response = await self.call(request)
        logger.info(f"StartTransaction: {response}")
        return response

    async def meter_values(self, connector_id, transaction_id, value_wh):
        # Construct MeterValue payload
        # Simple sample
        request = call.MeterValues(
            connector_id=connector_id,
            transaction_id=transaction_id,
            meter_value=[{
                "timestamp": datetime.utcnow().isoformat(),
                "sampledValue": [
                    {"value": str(value_wh), "context": "Sample.Periodic", "format": "Raw", "measurand": "Energy.Active.Import.Register", "unit": "Wh"}
                ]
            }]
        )
        response = await self.call(request)
        logger.info(f"MeterValues: {response}")
        return response

    async def stop_transaction(self, transaction_id, meter_stop, timestamp, id_tag, reason="Local"):
        request = call.StopTransaction(
            meter_stop=meter_stop,
            timestamp=timestamp,
            transaction_id=transaction_id,
            reason=reason,
            id_tag=id_tag
        )
        response = await self.call(request)
        logger.info(f"StopTransaction: {response}")
        return response

async def run_test_flow():
    # URL should match the backend config
    server_url = "ws://localhost:8000/ocpp/CP_TEST_001" 
    
    try:
        async with websockets.connect(server_url, subprotocols=["ocpp1.6"]) as ws:
            charge_point = SimulatedChargePoint("CP_TEST_001", ws)
            
            # Start the background task to listen for messages
            listen_task = asyncio.create_task(charge_point.start())
            
            # --- Test Flow ---
            
            # 1. Boot Verification
            logger.info("--- Step 1: Boot ---")
            boot_resp = await charge_point.boot()
            assert boot_resp.status == RegistrationStatus.accepted
            
            # 2. Heartbeat
            logger.info("--- Step 2: Heartbeat ---")
            await charge_point.heartbeat()
            
            # 3. Status Available
            logger.info("--- Step 3: Status Available ---")
            await charge_point.status_notification(1, ChargePointStatus.available)
            
            # 4. Authorize
            logger.info("--- Step 4: Authorize ---")
            # Note: Token must exist in DB for this to be Accepted. 
            auth_resp = await charge_point.authorize("DEADBEEF")
            
            # 5. Start Transaction
            logger.info("--- Step 5: Start Transaction ---")
            await charge_point.status_notification(1, ChargePointStatus.preparing)
            
            start_resp = await charge_point.start_transaction(
                connector_id=1,
                id_tag="DEADBEEF",
                meter_start=0,
                timestamp=datetime.utcnow().isoformat()
            )
            transaction_id = start_resp.transaction_id
            
            if transaction_id > 0:
                await charge_point.status_notification(1, ChargePointStatus.charging)
                
                # 6. Meter Values
                logger.info("--- Step 6: Meter Values ---")
                await asyncio.sleep(1)
                await charge_point.meter_values(1, transaction_id, 100)
                await asyncio.sleep(1)
                await charge_point.meter_values(1, transaction_id, 200)
                
                # 7. Stop Transaction
                logger.info("--- Step 7: Stop Transaction ---")
                await charge_point.status_notification(1, ChargePointStatus.finishing)
                stop_resp = await charge_point.stop_transaction(
                    transaction_id=transaction_id,
                    meter_stop=250,
                    timestamp=datetime.utcnow().isoformat(),
                    id_tag="DEADBEEF"
                )
                
                await charge_point.status_notification(1, ChargePointStatus.available)
            else:
                logger.error("Transaction failed to start (likely auth failed)")

            # Clean up
            listen_task.cancel()
            logger.info("--- Test Flow Complete ---")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_test_flow())
