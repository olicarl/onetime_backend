# OCPP 1.6 Implementation in CitrineOS

This document describes how OCPP 1.6 messages are implemented and executed in `citrineos-core`. The implementation is divided into two main categories based on the message initiator: Charging Station or Central System.

## 1. Messages Initiated by the Charging Station

Messages initiated by the Charging Station (e.g., `BootNotification`, `StartTransaction`, `MeterValues`) follow a flow from the WebSocket connection to the specific module handler.

### Message Flow
1.  **Reception**: The `Server` receives the raw WebSocket message.
2.  **Routing**: The `OcppRouter` module (`03_Modules/OcppRouter`) validates the message and routes it to the appropriate RabbitMQ queue based on the message action and version.
3.  **Handling**: A specific module listens to the queue and processes the message using a handler method decorated with `@AsHandler`.

### Implementation Details
Handlers for OCPP 1.6 messages are explicitly marked with `OCPPVersion.OCPP1_6`.

#### Example: StartTransaction
- **Module**: `TransactionsModule` (`03_Modules/Transactions`)
- **Handler**: `_handleOcpp16StartTransaction`
- **Decorator**: `@AsHandler(OCPPVersion.OCPP1_6, OCPP1_6_CallAction.StartTransaction)`
- **Logic**:
    1.  Receives `StartTransactionRequest`.
    2.  Authorizes the `idTag` using `TransactionService`.
    3.  Creates a transaction record in the database via `TransactionEventRepository`.
    4.  Sends `StartTransactionResponse` back to the station.

#### Example: StopTransaction
- **Module**: `TransactionsModule`
- **Handler**: `_handleOcpp16StopTransaction`
- **Decorator**: `@AsHandler(OCPPVersion.OCPP1_6, OCPP1_6_CallAction.StopTransaction)`
- **Logic**:
    1.  Receives `StopTransactionRequest`.
    2.  Validates the transaction ID and existing transaction.
    3.  Persists stop details (meter stop, reason) to the database.
    4.  Closes the transaction.

#### Example: MeterValues
- **Module**: `TransactionsModule`
- **Handler**: `_handleOcpp16MeterValues`
- **Decorator**: `@AsHandler(OCPPVersion.OCPP1_6, OCPP1_6_CallAction.MeterValues)`
- **Logic**:
    1.  Receives `MeterValuesRequest`.
    2.  Processes sampled values.
    3.  Updates the transaction with new meter data.

#### Example: Authorize
- **Module**: `EVDriverModule` (`03_Modules/EVDriver`)
- **Handler**: `_handleOCPP16Authorize`
- **Decorator**: `@AsHandler(OCPPVersion.OCPP1_6, OCPP1_6_CallAction.Authorize)`
- **Logic**:
    1.  Checks `AuthorizationRepository` for the `idTag`.
    2.  Validates expiry and status.
    3.  Returns `AuthorizeResponse` with status (Accepted, Invalid, etc.).

## 2. Messages Initiated by the Central System

Messages initiated by the Central System (e.g., `GetConfiguration`, `RemoteStartTransaction`, `Reset`) are triggered via API calls to the CitrineOS backend.

### Message Flow
1.  **API Request**: An external client sends a REST API request to CitrineOS (e.g., via Fastify routes).
2.  **Module API**: The request is handled by a module's API class (e.g., `ConfigurationOcpp16Api`).
3.  **Construction**: The module constructs the OcppRequest.
4.  **Sending**: The `MessageSender` puts the message on the RabbitMQ queue.
5.  **Delivery**: The `OcppRouter` picks up the message and sends it over the WebSocket to the station.

### Implementation Details
Methods exposed as API endpoints for sending OCPP 1.6 messages are decorated with `@AsMessageEndpoint`.

#### Example: Get Configuration
- **Module**: `ConfigurationModule` (`03_Modules/Configuration`)
- **Class**: `ConfigurationOcpp16Api`
- **Endpoint**: `getConfiguration`
- **Decorator**: `@AsMessageEndpoint(OCPP1_6_CallAction.GetConfiguration, ...)`
- **Logic**:
    1.  Accepts `GetConfigurationRequest` (list of keys).
    2.  Splits keys into batches if necessary.
    3.  Sends `Call` message to the station via `_module.sendCall`.
    4.  Returns confirmation indicating success/failure of the send operation.

#### Example: Change Configuration
- **Module**: `ConfigurationModule`
- **Class**: `ConfigurationOcpp16Api`
- **Endpoint**: `changeConfiguration`
- **Decorator**: `@AsMessageEndpoint(OCPP1_6_CallAction.ChangeConfiguration, ...)`
- **Logic**:
    1.  Accepts key-value pair to change.
    2.  Sends `ChangeConfiguration` command to the station.

#### Example: Reset
- **Module**: `ConfigurationModule`
- **Class**: `ConfigurationOcpp16Api`
- **Endpoint**: `reset`
- **Decorator**: `@AsMessageEndpoint(OCPP1_6_CallAction.Reset, ...)`
- **Logic**:
    1.  Sends `Reset` command (Soft/Hard) to the station.

## Summary

| Initiator | Flow Direction | Key Components | identification Method |
| :--- | :--- | :--- | :--- |
| **Charging Station** | Station -> Module | `OcppRouter`, `TransactionsModule`, `EVDriverModule` | `@AsHandler(OCPPVersion.OCPP1_6, ...)` |
| **Central System** | API -> Station | `ConfigurationOcpp16Api`, `MessageSender`, `WebSocket` | `@AsMessageEndpoint`, `_module.sendCall` |
