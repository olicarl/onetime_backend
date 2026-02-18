#!/bin/bash
# Onetime Agent Service Installer for Raspberry Pi

set -e

SERVICE_NAME="onetime-agent"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
INSTALL_DIR="/opt/onetime-agent"

echo "Installing Onetime Agent..."

# Create install directory
sudo mkdir -p $INSTALL_DIR

# Copy agent files
sudo cp agent.py $INSTALL_DIR/
sudo cp requirements.txt $INSTALL_DIR/

# Install Python dependencies
pip3 install --user -r requirements.txt

# Get relay token
if [ -z "$RELAY_TOKEN" ]; then
    read -p "Enter your relay token: " RELAY_TOKEN
fi

read -p "Enter relay URL (default: wss://relay.yourdomain.com/ws/connect): " RELAY_URL
RELAY_URL=${RELAY_URL:-"wss://relay.yourdomain.com/ws/connect"}

read -p "Enter local backend URL (default: http://localhost:8000): " BACKEND_URL
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}

# Create systemd service
cat << EOF | sudo tee $SERVICE_FILE
[Unit]
Description=Onetime Agent - Remote Access Tunnel
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="RELAY_URL=$RELAY_URL"
Environment="RELAY_TOKEN=$RELAY_TOKEN"
Environment="BACKEND_URL=$BACKEND_URL"
ExecStart=/usr/bin/python3 $INSTALL_DIR/agent.py --relay \${RELAY_URL} --token \${RELAY_TOKEN} --backend \${BACKEND_URL}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Onetime Agent installed and started!"
echo "Check status with: sudo systemctl status $SERVICE_NAME"
echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
