"""
Relay Client - WebSocket client to connect to Onetime Relay
"""
import asyncio
import json
import logging
from typing import Optional
import httpx
import websockets
from datetime import datetime

logger = logging.getLogger("relay_agent")


class RelayClient:
    """WebSocket client for relay connection"""
    
    def __init__(self, relay_url: str, token: str, local_backend_url: str = "http://localhost:8000"):
        self.relay_url = relay_url
        self.token = token
        self.local_backend_url = local_backend_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_delay = 5
        self.max_reconnect_delay = 300
        self.running = False
        self.connected = False
        self.last_error: Optional[str] = None
        self.connected_at: Optional[datetime] = None
        self.http_client = httpx.AsyncClient(
            base_url=local_backend_url,
            timeout=30.0,
            follow_redirects=True
        )
    
    async def connect(self) -> bool:
        """Connect to relay server"""
        ws_url = f"{self.relay_url}?token={self.token}"
        logger.info(f"Connecting to relay at {self.relay_url}")
        
        try:
            self.ws = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            self.connected_at = datetime.utcnow()
            self.last_error = None
            logger.info("Connected to relay server")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def handle_message(self, message: str):
        """Handle incoming message from relay"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "connected":
                logger.info(f"Tunnel established: {data.get('message')}")
                
            elif msg_type == "ping":
                await self.ws.send(json.dumps({"type": "pong"}))
                
            elif msg_type == "http_request":
                await self.handle_http_request(data)
                
            elif msg_type == "error":
                logger.error(f"Error from relay: {data.get('message')}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_http_request(self, request_data: dict):
        """Proxy HTTP request to local backend"""
        import uuid
        request_id = request_data.get("request_id", str(uuid.uuid4()))
        method = request_data.get("method", "GET")
        path = request_data.get("path", "/")
        headers = request_data.get("headers", {})
        body = request_data.get("body")
        
        logger.debug(f"Proxying {method} {path}")
        
        try:
            request_kwargs = {
                "method": method,
                "url": path,
                "headers": headers
            }
            
            if body:
                request_kwargs["content"] = body.encode('utf-8') if isinstance(body, str) else body
            
            response = await self.http_client.request(**request_kwargs)
            
            response_data = {
                "type": "http_response",
                "request_id": request_id,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }
            
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            response_data = {
                "type": "http_response",
                "request_id": request_id,
                "status_code": 502,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Backend unreachable", "details": str(e)})
            }
        
        try:
            await self.ws.send(json.dumps(response_data))
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        while self.running:
            try:
                if not await self.connect():
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                    continue
                
                self.reconnect_delay = 5
                
                async for message in self.ws:
                    if not self.running:
                        break
                    await self.handle_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, reconnecting...")
                self.connected = False
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self.last_error = str(e)
                self.connected = False
            
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    async def stop(self):
        """Stop the client"""
        self.running = False
        self.connected = False
        if self.ws:
            await self.ws.close()
        await self.http_client.aclose()
        logger.info("Relay client stopped")
    
    def get_status(self) -> dict:
        """Get current connection status"""
        return {
            "connected": self.connected,
            "running": self.running,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_error": self.last_error,
            "relay_url": self.relay_url
        }
