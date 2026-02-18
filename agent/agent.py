"""
Onetime Agent - Pi-side client for connecting to Onetime Relay

This runs on the Raspberry Pi and creates an outbound WebSocket connection
to the relay server, then proxies HTTP requests to the local Onetime Backend.
"""
import asyncio
import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Optional

import websockets
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("onetime-agent")

class OnetimeAgent:
    """Agent that connects Pi to relay server"""
    
    def __init__(self, relay_url: str, token: str, backend_url: str = "http://localhost:8000"):
        self.relay_url = relay_url
        self.token = token
        self.backend_url = backend_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_delay = 300  # 5 minutes
        self.running = False
        self.http_client = httpx.AsyncClient(
            base_url=backend_url,
            timeout=30.0,
            follow_redirects=True
        )
    
    async def connect(self):
        """Connect to relay server via WebSocket"""
        ws_url = f"{self.relay_url}?token={self.token}"
        logger.info(f"Connecting to relay at {self.relay_url}")
        
        try:
            self.ws = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10
            )
            logger.info("Connected to relay server")
            self.reconnect_delay = 5  # Reset reconnect delay
            return True
        except Exception as e:
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
                # Respond to keepalive
                await self.ws.send(json.dumps({"type": "pong"}))
                
            elif msg_type == "http_request":
                # Proxy HTTP request to local backend
                await self.handle_http_request(data)
                
            elif msg_type == "error":
                logger.error(f"Error from relay: {data.get('message')}")
                
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_http_request(self, request_data: dict):
        """Proxy HTTP request to local backend and return response"""
        request_id = request_data.get("request_id")
        method = request_data.get("method", "GET")
        path = request_data.get("path", "/")
        headers = request_data.get("headers", {})
        body = request_data.get("body")
        
        logger.debug(f"Proxying {method} {path}")
        
        try:
            # Build request
            request_kwargs = {
                "method": method,
                "url": path,
                "headers": headers
            }
            
            if body:
                request_kwargs["content"] = body.encode('utf-8') if isinstance(body, str) else body
            
            # Send to local backend
            response = await self.http_client.request(**request_kwargs)
            
            # Build response data
            response_headers = dict(response.headers)
            response_body = response.text
            
            response_data = {
                "type": "http_response",
                "request_id": request_id,
                "status_code": response.status_code,
                "headers": response_headers,
                "body": response_body
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
        
        # Send response back to relay
        try:
            await self.ws.send(json.dumps(response_data))
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        while self.running:
            try:
                # Connect to relay
                if not await self.connect():
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                    continue
                
                # Message loop
                async for message in self.ws:
                    await self.handle_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, reconnecting...")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            
            # Reconnect delay
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        if self.ws:
            await self.ws.close()
        await self.http_client.aclose()
        logger.info("Agent stopped")


def main():
    parser = argparse.ArgumentParser(description="Onetime Agent - Connect Pi to Onetime Relay")
    parser.add_argument("--relay", required=True, help="Relay WebSocket URL (wss://relay.example.com/ws/connect)")
    parser.add_argument("--token", required=True, help="Relay key/token")
    parser.add_argument("--backend", default="http://localhost:8000", help="Local backend URL")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Get from environment if not provided
    relay_url = args.relay or os.getenv("RELAY_URL")
    token = args.token or os.getenv("RELAY_TOKEN")
    backend_url = args.backend or os.getenv("BACKEND_URL", "http://localhost:8000")
    
    if not relay_url or not token:
        print("Error: --relay and --token are required (or set RELAY_URL and RELAY_TOKEN env vars)")
        sys.exit(1)
    
    agent = OnetimeAgent(relay_url, token, backend_url)
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(agent.stop())


if __name__ == "__main__":
    main()
