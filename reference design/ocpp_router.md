# OCPP Router Documentation

The `OcppRouter` module is the central communication hub of the `citrineos-core` system. It manages the WebSocket connections with Charging Stations, validates incoming messages, and routes them to the appropriate system modules via the message broker (RabbitMQ).

## Core Responsibilities

1.  **Connection Management**: Managing WebSocket connection lifecycle (connect/disconnect).
2.  **Message Routing**: Directing messages between Charging Stations and internal modules.
3.  **Validation**: Schema validation of incoming OCPP messages (Call, CallResult, CallError).
4.  **State Management**: Tracking the online/offline state of charging stations and message states (Request/Response).

## Architecture

The `MessageRouterImpl` class extends `AbstractMessageRouter` and implements `IMessageRouter`. It is designed to be the single entry point for all OCPP traffic.

### Key Components

*   **`IMessageHandler`**: Handles the underlying transport connection (e.g., RabbitMQ receiver for internal traffic, WebSocket handler for external traffic). *Note: In this specific module structure, the actual WebSocket server logic seems to be abstracted or handled by the `Server` module which delegates to this Router.*
*   **`IMessageSender`**: Sends routed messages to internal queues (RabbitMQSender).
*   **`WebhookDispatcher`**: Dispatches webhook events for connection status and message logging.
*   **`ICache`**: Uses Redis (or in-memory) to lock transactions and prevent concurrent calls.
*   **`CircuitBreaker`**: Protects the system from cascading failures during broker disconnection.

## Functionality Breakdown

### 1. Connection Registration (`registerConnection`)
When a new WebSocket connection is established:
-   **Webhook Dispatch**: Notices subscribers about the new connection.
-   **Queue Subscription**: Subscribes to unique request/response queues for that specific station connection.
-   **State Update**: Updates the `ChargingStation` status in the database to `online` and records the negotiated `OCPPVersion`.

### 2. Message Processing (`onMessage`)
The core loop for handling incoming raw WebSocket messages:
1.  **Parsing**: Parses the JSON message.
2.  **Type Identification**: Identifies the message type (Call, CallResult, CallError).
3.  **Handling**:
    -   **`_onCall`**:
        -   Maps protocol-specific actions to internal enums.
        -   Checks `_onCallIsAllowed` (blacklist/whitelist check).
        -   **Validation**: Validates payload against JSON schemas (`_validateCall`).
        -   **Locking**: Sets a cache lock to ensure sequential processing for the same message ID.
        -   **Routing**: Calls `_routeCall` to forward the message to the message broker.
    -   **`_onCallResult`**:
        -   Retrieves the original request context from cache.
        -   Validates the message ID match.
        -   Routes the result to the module that initiated the call.
    -   **`_onCallError`**:
        -   Similar context retrieval and routing for errors.

### 3. Outbound Call (`sendCall`)
Used when the system initiates a message (e.g., `GetConfiguration`):
1.  **Check**: Verifies if the station is allowed to receive calls (e.g., checking `BootStatus`).
2.  **Lock**: Sets a transaction lock in cache (`action:correlationId`).
3.  **Send**: Uses `_sendMessage` to push the payload to the network hook (WebSocket output).

### 4. Routing Logic
The `OcppRouter` doesn't process business logic itself. It wraps messages into a standard `IMessage` envelope and pushes them to specific RabbitMQ exchanges based on:
-   **Identifier**: Tenant and Station ID.
-   **Event Group**: Grouping of related messages (though mostly `General` is used here).
-   **Origin**: Marking the message as coming from `ChargingStation`.

## Database Interactions

The router interacts with the database primarily for connection state management:
-   **`LocationRepository`**:
    -   `setChargingStationIsOnlineAndOCPPVersion`: Updates station online status and protocol version.
    -   `readChargingStationByStationId`: Reads station details (used during deregistration).
-   **`SubscriptionRepository`**: (Implementation present but usage seemingly focused on subscriptions).

## Error Handling

-   **Schema Violations**: Returns `FormatViolation` `CallError` immediately if validation fails.
-   **Internal Errors**: catches exceptions during routing and returns `InternalError`.
-   **Timeouts**: Can detect missing contexts for results/errors, implying timeouts.

## Security & Reliability

-   **OIDC Integration**: Can attach Bearer tokens to callback hook requests.
-   **Circuit Breaker**: Detects broker failures and implements exponential backoff for reconnection to prevent flooding.
