import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from gateway.core.config import settings, logger
from gateway.connection_manager import connection_registry
from gateway.handlers.ocpp_handler import ChargePoint
from gateway.dependencies import get_nameko_proxy, get_rabbitmq_channel, close_connections
from gateway.routers import web
import aio_pika

app = FastAPI()
app.include_router(web.router)

@app.on_event("startup")
async def startup():
    await get_nameko_proxy()
    await get_rabbitmq_channel()
    asyncio.create_task(consume_gateway_commands())

@app.on_event("shutdown")
async def shutdown():
    await close_connections()

async def consume_gateway_commands():
    channel = await get_rabbitmq_channel()
    exchange = await channel.declare_exchange(settings.GATEWAY_COMMANDS_EXCHANGE, aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("gateway_commands_queue", auto_delete=True)
    await queue.bind(exchange, routing_key="cmd.#")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                try:
                    payload = json.loads(message.body)
                    charger_id = message.routing_key.split(".")[1]
                    logger.info(f"Received command for {charger_id}: {payload}")
                    
                    ws = connection_registry.get_connection(charger_id)
                    if ws:
                        # In a real scenario, we would need a way to retrieve the ChargePoint instance 
                        # associated with this WebSocket to call .call() on it.
                        # Since ChargePoint is instantiated per connection in the websocket route,
                        # we might need to store the ChargePoint instance in the registry instead of just the WS,
                        # or have a way to access it.
                        # For this simplified implementation, we'll assume we can just send raw JSON 
                        # or we need to refactor ConnectionRegistry to store ChargePoint instances.
                        
                        # However, the ChargePoint class from mobilityhouse/ocpp wraps the websocket.
                        # If we want to send a Call message (RemoteStartTransaction), we need the ChargePoint instance.
                        
                        # Refactoring ConnectionRegistry to store ChargePoint instances is better, 
                        # but ChargePoint is created inside the websocket endpoint.
                        
                        # Let's stick to the plan: "Gateway consumes this message, looks up the WebSocket in ConnectionRegistry, and uses charge_point.call() to send the message to the hardware."
                        # To do this properly, we should store the ChargePoint instance.
                        pass
                    else:
                        logger.warning(f"Charger {charger_id} not connected")
                except Exception as e:
                    logger.error(f"Error processing gateway command: {e}")

@app.websocket("/ocpp/{charge_point_id}")
async def on_connect(websocket: WebSocket, charge_point_id: str):
    await websocket.accept()
    logger.info(f"Accepted connection from {charge_point_id}")
    
    cp = ChargePoint(charge_point_id, websocket)
    
    # We need to store the ChargePoint instance if we want to use it for remote commands
    # But ConnectionRegistry currently stores WebSocket.
    # Let's update ConnectionRegistry to store the ChargePoint instance? 
    # Or just the WebSocket and we recreate a wrapper? No, state is in ChargePoint.
    # The requirement says: "ConnectionRegistry that stores (charger_id: str, websocket: WebSocket)"
    # AND "Gateway consumes this message, looks up the WebSocket in ConnectionRegistry, and uses charge_point.call()"
    
    # If we only have the WebSocket, we can't easily use charge_point.call() because that method belongs to the instance 
    # that is running the loop.
    # Actually, mobilityhouse/ocpp ChargePoint instances are designed to run a loop.
    # If we want to send a message *while* the loop is running, we need access to that same instance.
    
    # I will deviate slightly and store the ChargePoint instance in the registry, 
    # or I will attach the ChargePoint instance to the WebSocket object if possible.
    # Let's update ConnectionRegistry to store the ChargePoint instance. 
    # Wait, the requirement explicitly said "stores (charger_id: str, websocket: WebSocket)".
    # But Rule C says "uses charge_point.call()".
    # If I store only WebSocket, I cannot access the running ChargePoint instance.
    # I will update ConnectionRegistry to store the ChargePoint instance, as it wraps the WebSocket.
    # This is a necessary technical adjustment for Rule C to work.
    
    # Actually, I'll stick to the requirement of storing WebSocket in the registry for now to match the text,
    # but I will ALSO store the ChargePoint instance in a separate map or modify the registry to support it.
    # Let's modify the registry to store the ChargePoint instance, as it contains the WebSocket.
    
    await connection_registry.connect(charge_point_id, websocket)
    
    # Hack: Attach cp to websocket so we can retrieve it later?
    websocket.charge_point = cp 
    
    try:
        await cp.start()
    except WebSocketDisconnect:
        connection_registry.disconnect(charge_point_id)
        logger.info(f"Charger {charge_point_id} disconnected")
    except Exception as e:
        logger.error(f"Error in OCPP connection: {e}")
        connection_registry.disconnect(charge_point_id)

# Re-implement consume_gateway_commands to use the attached charge_point
async def consume_gateway_commands():
    channel = await get_rabbitmq_channel()
    exchange = await channel.declare_exchange(settings.GATEWAY_COMMANDS_EXCHANGE, aio_pika.ExchangeType.TOPIC)
    queue = await channel.declare_queue("gateway_commands_queue", auto_delete=True)
    await queue.bind(exchange, routing_key="cmd.#")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                try:
                    payload = json.loads(message.body)
                    charger_id = message.routing_key.split(".")[1]
                    logger.info(f"Received command for {charger_id}: {payload}")
                    
                    ws = connection_registry.get_connection(charger_id)
                    if ws and hasattr(ws, 'charge_point'):
                        cp = ws.charge_point
                        
                        command_name = payload.get("command")
                        command_args = payload.get("args", {})
                        
                        # Use the generic handler
                        response = await cp.send_admin_command(command_name, command_args)
                        
                        # Optional: Send response back to a result queue?
                        # For now just log it
                        logger.info(f"Command {command_name} result: {response}")
                    else:
                        logger.warning(f"Charger {charger_id} not connected or CP not attached")
                except Exception as e:
                    logger.error(f"Error processing gateway command: {e}")
