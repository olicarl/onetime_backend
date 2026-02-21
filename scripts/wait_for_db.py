import time
import sys
import os

def main():
    print("Waiting for database...")
    timeout = 60
    start_time = time.time()
    
    # Add project root to sys.path just in case
    sys.path.append(os.getcwd())
    
    try:
        from app.database import engine
        from sqlalchemy.exc import OperationalError
        from sqlalchemy import text
        use_engine = True
    except ImportError:
        use_engine = False
        import socket
        host = os.environ.get("POSTGRES_HOST", "db")
        port = int(os.environ.get("POSTGRES_PORT", 5432))

    while True:
        if use_engine:
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("Database is ready!")
                sys.exit(0)
            except OperationalError as e:
                if time.time() - start_time > timeout:
                    print(f"Error waiting for database: {e}")
                    sys.exit(1)
                print(f"Database not ready yet (or starting up), retrying in 2 seconds...")
                time.sleep(2)
            except Exception as e:
                if time.time() - start_time > timeout:
                    print(f"Error connecting to database: {e}")
                    sys.exit(1)
                print(f"Database error ({e}), retrying in 2 seconds...")
                time.sleep(2)
        else:
            try:
                sock = socket.create_connection((host, port), timeout=1)
                sock.close()
                print("Database is ready! (TCP socket connection successful)")
                sys.exit(0)
            except (socket.gaierror, ConnectionRefusedError, socket.timeout, OSError) as e:
                if time.time() - start_time > timeout:
                    print(f"Timeout waiting for {host}:{port}: {e}")
                    sys.exit(1)
                print(f"Database tcp socket not ready yet ({e}), retrying in 2 seconds...")
                time.sleep(2)

if __name__ == "__main__":
    main()
