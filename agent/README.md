# Onetime Agent

The Pi-side client that creates a secure tunnel to the Onetime Relay server.

## What it does

- Creates an **outbound WebSocket connection** from your Pi to the relay server
- Proxies HTTP requests from the relay to your local Onetime Backend
- Automatically reconnects if connection drops
- No inbound ports required on your router/firewall

## Installation

### Quick Install (Recommended)

```bash
cd /tmp
git clone https://github.com/yourusername/onetime-relay.git
cd onetime-relay/pi-agent
chmod +x install.sh
./install.sh
```

### Manual Install

1. Install dependencies:
```bash
pip3 install websockets httpx
```

2. Copy agent.py to your Pi

3. Run:
```bash
python3 agent.py --relay wss://relay.yourdomain.com/ws/connect --token YOUR_TOKEN
```

## Usage

### Command Line

```bash
python3 agent.py \
  --relay wss://relay.yourdomain.com/ws/connect \
  --token YOUR_RELAY_KEY \
  --backend http://localhost:8000
```

### Environment Variables

```bash
export RELAY_URL="wss://relay.yourdomain.com/ws/connect"
export RELAY_TOKEN="your-token-here"
export BACKEND_URL="http://localhost:8000"

python3 agent.py
```

### Systemd Service

The install script creates a systemd service. Manage it with:

```bash
sudo systemctl status onetime-agent    # Check status
sudo systemctl start onetime-agent     # Start
sudo systemctl stop onetime-agent      # Stop
sudo systemctl restart onetime-agent   # Restart
sudo journalctl -u onetime-agent -f    # View logs
```

## How it works

```
┌─────────────┐         WebSocket          ┌─────────────┐
│  Onetime    │◄───────(outbound)─────────►│   Relay     │
│   Agent     │                             │   Server    │
│   (Pi)      │                             │   (Cloud)   │
└──────┬──────┘                             └──────┬──────┘
       │ HTTP proxy                                  │ HTTPS
       ▼                                             ▼
┌─────────────┐                              ┌─────────────┐
│   Onetime   │                              │   Admin     │
│   Backend   │                              │   (Browser) │
└─────────────┘                              └─────────────┘
```

1. Pi agent connects outbound to relay WebSocket
2. Admin visits `https://user.onetimerelay.com`
3. Relay routes request through WebSocket tunnel
4. Pi agent proxies to local backend
5. Response flows back through the same path

## Security

- All connections use TLS (WSS/HTTPS)
- Relay keys are JWT tokens with expiration
- No inbound ports required on Pi
- Pi only makes outbound connections
