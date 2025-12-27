# Central System Initiated OCPP 1.6 Messages

This document details the business logic and implementation for OCPP 1.6 messages initiated by the Central System (CitrineOS), typically via REST API calls.

## 1. RemoteStartTransaction

**Module**: `EVDriverModule`
**API Class**: `EVDriverOcpp16Api`
**Endpoint**: `remoteStartTransaction`

### Business Logic
1.  **API Request**: Accepts `RemoteStartTransactionRequest` (includes `idTag`, `connectorId`, `chargingProfile`).
2.  **Broadcast/Unicast**: Sends the `RemoteStartTransaction` Call to the specified station(s).
3.  **Return**: Returns the confirmation status of the sent message (Success/Failure of delivery).

### Database Interactions
-   **Validation**: None explicit in the API layer; relies on `OcppRouter` to look up the station connection.

## 2. RemoteStopTransaction

**Module**: `EVDriverModule`
**API Class**: `EVDriverOcpp16Api`
**Endpoint**: `remoteStopTransaction`

### Business Logic
1.  **API Request**: Accepts `RemoteStopTransactionRequest` (`transactionId`).
2.  **Action**: Sends `RemoteStopTransaction` command to station.
3.  **Return**: Confirmation of delivery.

### Database Interactions
-   none directly.

## 3. UnlockConnector

**Module**: `EVDriverModule`
**API Class**: `EVDriverOcpp16Api`
**Endpoint**: `unlockConnector`

### Business Logic
1.  **API Request**: Accepts `UnlockConnectorRequest` (`connectorId`).
2.  **Action**: Sends `UnlockConnector` command.
3.  **Return**: Confirmation of delivery.

## 4. GetConfiguration

**Module**: `ConfigurationModule`
**API Class**: `ConfigurationOcpp16Api`
**Endpoint**: `getConfiguration`

### Business Logic
1.  **Station Lookup**: Verifies the charging station exists in `LocationRepository`.
2.  **Max Keys Logic**:
    -   Reads `GetConfigurationMaxKeys` from `ChangeConfigurationRepository` (or defaults to max integer).
    -   If the requested keys exceed specific limits, it splits the request into multiple batches.
3.  **Batch Sending**: Sends multiple `GetConfiguration` calls if necessary.
4.  **Aggregation**: Collects success/failure for each batch.

### Database Interactions
-   **Read**: `ChargingStation` (Validation)
-   **Read**: `ChangeConfiguration` (Key: `GetConfigurationMaxKeys`)

## 5. ChangeConfiguration

**Module**: `ConfigurationModule`
**API Class**: `ConfigurationOcpp16Api`
**Endpoint**: `changeConfiguration`

### Business Logic
1.  **Station Lookup**: Verifies station existence.
2.  **Action**: Sends `ChangeConfiguration` (`key`, `value`) to the station.

### Database Interactions
-   **Read**: `ChargingStation`

## 6. TriggerMessage

**Module**: `ConfigurationModule`
**API Class**: `ConfigurationOcpp16Api`
**Endpoint**: `triggerMessage`

### Business Logic
1.  **Validation**: Checks if `connectorId` > 0 if provided.
2.  **Action**: Sends `TriggerMessage` (`requestedMessage`, `connectorId`) to station.

## 7. Reset

**Module**: `ConfigurationModule`
**API Class**: `ConfigurationOcpp16Api`
**Endpoint**: `reset`

### Business Logic
1.  **Action**: Sends `Reset` (`type`: `Soft` or `Hard`) to station.

## 8. ChangeAvailability

**Module**: `ConfigurationModule`
**API Class**: `ConfigurationOcpp16Api`
**Endpoint**: `changeAvailability`

### Business Logic
1.  **Action**: Sends `ChangeAvailability` (`connectorId`, `type`: `Operative` / `Inoperative`).

## 9. UpdateFirmware

**Module**: `ConfigurationModule`
**API Class**: `ConfigurationOcpp16Api`
**Endpoint**: `updateFirmware`

### Business Logic
1.  **Action**: Sends `UpdateFirmware` (`location`, `retries`, `retrieveDate`, `retryInterval`).

## Summary

| Message | Module | Validation Logic |
| :--- | :--- | :--- |
| `RemoteStartTransaction` | EVDriver | Basic |
| `RemoteStopTransaction` | EVDriver | Basic |
| `UnlockConnector` | EVDriver | Basic |
| `GetConfiguration` | Configuration | Station Existence, Batching based on `MaxKeys` |
| `ChangeConfiguration` | Configuration | Station Existence |
| `TriggerMessage` | Configuration | Connector ID format |
| `Reset` | Configuration | Basic |
| `ChangeAvailability` | Configuration | Basic |
| `UpdateFirmware` | Configuration | Basic |
