# System Architecture: The Event-Driven Monolith

This document details the new simplified architecture for the **Onetime Backend**. The system is designed as a **Modular Monolith** that runs as a single process but maintains loose coupling through an internal **In-Memory Event Bus**.

> **Design Goal**: Simplicity and stability for deployments of < 200 stations, running on low-cost hardware (e.g., Raspberry Pi).

## 1. High-Level Overview

We have removed distributed components (RabbitMQ, Nameko) in favor of Python's `asyncio` capabilities and an internal event loop.

```mermaid
graph LR
    CS[Charging Station] -- WebSocket (OCPP) --> GW_API[FastAPI Gateway]
    GW_API -- 1. Emit Event --> BUS((Event Bus))
    BUS -- 2. Trigger --> SVC[Transaction Service]
    SVC -- 3. SQL --> DB[(Postgres)]
```

### Components

1. **FastAPI Gateway**: Handles WebSocket connections and HTTP APIs.
2. **Event Bus (`pyee`)**: A lightweight in-memory pub/sub mechanism.
3. **Services**: Logic modules (Transaction, Auth, Config) that subscribe to the Event Bus and interact with the Database.
4. **Database**: PostgreSQL for persistent storage.

---

## 2. Incoming Flow: Charger → System

**Scenario**: A Charger sends `MeterValues`.

```mermaid
sequenceDiagram
    participant C as Charger
    participant H as OCPP Handler
    participant B as EventBus
    participant S as TransactionService
    participant DB as Database

    C->>H: WebSocket: MeterValues(measurands=...)
    Note over H: gateway/handlers.py
    H->>H: Validate Schema
    H->>B: emit('meter_values', payload)
    H-->>C: Immediate Response (Conf)
    
    Note over B: Async Dispatch
    B->>S: trigger on_meter_values(payload)
    Note over S: services/transactions.py
    S->>DB: INSERT INTO meter_readings...
```

### Key Benefits

- **Non-Blocking**: The WebSocket handler responds to the charger immediately after emitting the event. Database writes happen asynchronously.
- **Decoupled**: The `OCPP Handler` doesn't know about the `TransactionService`. It just announces "Hey, I got meter values!".

---

## 3. Outgoing Flow: System → Charger

**Scenario**: An Admin clicks "Remote Start" in the dashboard.

```mermaid
sequenceDiagram
    participant A as Admin (API)
    participant S as CommandService
    participant CM as ConnectionManager
    participant C as Charger

    A->>S: POST /api/remote-start/{id}
    S->>CM: get_connection(charger_id)
    alt Connection Found
        CM->>C: Send RemoteStartTransaction
        C-->>CM: Result: Accepted
        CM-->>S: Return Success
        S-->>A: 200 OK
    else Not Found
        S-->>A: 404 Offline
    end
```

### Direct Access

Since everything runs in one process, the API can directly access the `ConnectionManager` (Singleton) to find the active WebSocket and send data. No external message queue is needed to route the command.

---

## 4. Technology Stack

- **Language**: Python 3.10+
- **Web Framework**: `FastAPI` (WebSockets & HTTP)
- **OCPP Library**: `mobilityhouse/ocpp`
- **Event Bus**: `pyee` (AsyncIO EventEmitter)
- **Database**: `PostgreSQL` (+ `SQLAlchemy` / `Alembic`)
- **Runtime**: Single Docker Container

## 5. Directory Structure Plan

```text
onetime_backend/
├── app/
│   ├── gateway/
│   │   ├── connection_manager.py  # WebSocket Registry
│   │   └── ocpp_handler.py        # Protocol Translator
│   ├── services/
│   │   ├── events.py              # The shared EventBus instance
│   │   ├── transactions.py        # Logic: Start/Stop/MeterValues
│   │   └── auth.py                # Logic: Authorize tags
│   ├── main.py                    # Entrypoint (FastAPI app)
│   └── models.py                  # Database Models
├── migrations/                    # Alembic Migrations
├── tests/
├── Dockerfile
└── docker-compose.yml
```
