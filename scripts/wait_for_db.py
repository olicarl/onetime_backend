import socket
import time
import sys
import os

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", 5432))
timeout = 60

print(f"Waiting for database at {host}:{port}...")

start_time = time.time()
while True:
    try:
        sock = socket.create_connection((host, port), timeout=1)
        sock.close()
        print("Database is ready!")
        sys.exit(0)
    except (socket.gaierror, ConnectionRefusedError, socket.timeout, OSError):
        if time.time() - start_time > timeout:
            print(f"Error: Timed out waiting for database at {host}:{port}")
            sys.exit(1)
        print("Database not ready yet, retrying in 2 seconds...")
        time.sleep(2)
