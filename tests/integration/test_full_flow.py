import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_full_flow")

async def test_boot_notification():
    uri = "ws://localhost:8000/ocpp/CP_1"
    async with websockets.connect(uri, subprotocols=['ocpp1.6']) as websocket:
        
        # 1. Send BootNotification
        boot_notification = [
            2,  # Call
            "12345",  # Unique ID
            "BootNotification",
            {
                "chargePointVendor": "TestVendor",
                "chargePointModel": "TestModel"
            }
        ]
        
        logger.info(f"Sending BootNotification: {boot_notification}")
        await websocket.send(json.dumps(boot_notification))
        
        # 2. Receive Response
        response = await websocket.recv()
        logger.info(f"Received response: {response}")
        
        response_data = json.loads(response)
        
        # 3. Assertions
        assert response_data[0] == 3  # CallResult
        assert response_data[1] == "12345"  # ID matches
        assert response_data[2]["status"] == "Accepted"
        
        logger.info("BootNotification Test Passed!")

        # 4. Send MeterValues (Notify)
        meter_values = [
            2,
            "12346",
            "MeterValues",
            {
                "connectorId": 1,
                "transactionId": 1,
                "meterValue": [
                    {
                        "timestamp": "2023-01-01T00:00:00Z",
                        "sampledValue": [
                            {"value": "10", "context": "Sample.Periodic", "format": "Raw", "measurand": "Energy.Active.Import.Register", "location": "Outlet", "unit": "Wh"}
                        ]
                    }
                ]
            }
        ]
        
        logger.info(f"Sending MeterValues: {meter_values}")
        await websocket.send(json.dumps(meter_values))
        
        # MeterValues is a Call, expects a CallResult
        response = await websocket.recv()
        logger.info(f"Received response for MeterValues: {response}")
        
        response_data = json.loads(response)
        assert response_data[0] == 3
        assert response_data[1] == "12346"
        
        logger.info("MeterValues Test Passed!")

if __name__ == "__main__":
    # Wait for services to be up (manual check usually, but here we just run)
    try:
        asyncio.run(test_boot_notification())
    except Exception as e:
        logger.error(f"Test failed: {e}")
        exit(1)
