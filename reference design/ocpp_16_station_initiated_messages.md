# Station Initiated OCPP 1.6 Messages

This document details the business logic and database interactions for OCPP 1.6 messages initiated by the Charging Station, as implemented in `citrineos-core`.

## 1. BootNotification

**Module**: `ConfigurationModule`
**Handler**: `_handleOcpp16BootNotification`

### Business Logic
1.  **Response Creation**: Generates a `BootNotificationResponse`. Checks the cache for existing boot status.
2.  **Charging Station Creation/Update**: Creates or updates the `ChargingStation` entity with details from the request (Vendor, Model, Serial Numbers, Firmware Version, ICCID, IMSI).
3.  **Status Caching**: Caches the boot status (Accepted/Pending/Rejected).
4.  **Boot Config Update**: Updates the `Boot` configuration entity with the latest response details.
5.  **Configuration Sync**:
    - If status is `Accepted`, it triggers a synchronization process.
    - Sends all pending `ChangeConfiguration` requests (retrieved from `ChangeConfiguration` repository).
    - Request a `GetConfiguration` from the station to sync generic configuration keys.

### Database Interactions
-   **Created/Updated**: `ChargingStation` (Table: `ChargingStations`)
-   **Updated**: `Boot` (Table: `Boots`)
-   **Read**: `ChangeConfiguration` (Table: `ChangeConfigurations`)
-   **Read**: `ChargingStation` (via repository)

## 2. Heartbeat

**Module**: `ConfigurationModule`
**Handler**: `_handle16Heartbeat`

### Business Logic
1.  **Time Sync**: Simply responds with the current server time (`currentTime`) in ISO format.
2.  **Logging**: Debug logs the receipt and response.

### Database Interactions
-   None explicitly in the handler. (Note: `ChargingStation` online status might be updated by the `OcppRouter` on connection/message receipt, but not in this specific handler logic).

## 3. Authorize

**Module**: `EVDriverModule`
**Handler**: `_handleOCPP16Authorize`

### Business Logic
1.  **Lookup**: detailed search for the `idTag` in the `Authorization` repository.
2.  **Validation**:
    -   If no authorization is found, returns `Invalid`.
    -   If multiple are found, returns `Invalid` (too ambiguous).
    -   Checks `status` (Accepted, Blocked, Expired, etc.).
    -   Checks `cacheExpiryDateTime` against current time.
3.  **Parent IdTag**: If the authorization has a `groupAuthorizationId`, fetches the parent authorization to populate `parentIdTag`.
4.  **External Authorization**: Passes the authorization through any configured `IAuthorizer` implementations (e.g., `RealTimeAuthorizer`).

### Database Interactions
-   **Read**: `Authorization` (Table: `Authorizations`)

## 4. StatusNotification

**Module**: `TransactionsModule`
**Handler**: `_handleOcpp16StatusNotification`

### Business Logic
1.  **Process Notification**: Delegates to `StatusNotificationService`.
2.  **Connector Update**: Updates the status of the specified `Connector` (and potentially `Evse`) in the database.
3.  **Error Logging**: Can log errors if associated components/connectors are not found, though `citrineos-core` often creates them on the fly if `autoRegister` logic is enabled in services (logic specific to `StatusNotificationService`).

### Database Interactions
-   **Updated**: `Connector` (Table: `Connectors`)
-   **Updated**: `Evse` (Table: `Evses`) - implicitly via status propagation.
-   **Read**: `ChargingStation`, `Component`, `Variable` (to map status to 2.0.1 style device model if utilized internally).

## 5. StartTransaction

**Module**: `TransactionsModule`
**Handler**: `_handleOcpp16StartTransaction`

### Business Logic
1.  **Authorization**: Re-authorizes the `idTag` using `TransactionService` to ensure it is valid for starting a transaction.
2.  **Transaction Creation**: Creates a new `Transaction` record.
    -   Associated with `StationId` and `idTag`.
    -   Records `meterStart`, `timestamp`.
3.  **Reservation Handling**: If a `reservationId` is provided, it deactivates the corresponding reservation.
4.  **Response**: Returns the generated `transactionId` and `idTagInfo` status.

### Database Interactions
-   **Created**: `Transaction` (Table: `Transactions`)
-   **Created**: `TransactionEvent` (Table: `TransactionEvents` - internally mapped 1.6 start to event).
-   **Updated**: `Reservation` (Table: `Reservations`) - sets `isActive` to false.

## 6. StopTransaction

**Module**: `TransactionsModule`
**Handler**: `_handleOcpp16StopTransaction`

### Business Logic
1.  **Authorization Lookup**: Checks the `idTag` (if present) to validate who stopped it.
2.  **Transaction Lookup**: Finds the active transaction by `transactionId` and `stationId`.
3.  **Close Transaction**:
    -   Creates a "Stop" event record (via `events` logic or direct update).
    -   Calculates `totalKwh` based on `meterStop` - `meterStart`.
    -   Updates `Transaction` with `isActive = false`, `endTime`, and `stoppedReason`.
4.  **Meter Values**: Processes any transaction data (meter values) included in the request.

### Database Interactions
-   **Updated**: `Transaction` (Table: `Transactions`)
-   **Created**: `TransactionEvent` (Table: `TransactionEvents` - stop event).
-   **Created**: `MeterValue` (Table: `MeterValues`) - for transaction data.

## 7. MeterValues

**Module**: `TransactionsModule`
**Handler**: `_handleOcpp16MeterValues`

### Business Logic
1.  **Validation**: checks if `transactionId` is present (usually required for association, though station-wide meter values exist).
2.  **Processing**: Iterates through `meterValue` array.
3.  **Persistence**: Creates `MeterValue` entities associated with the transaction.
4.  **Updates**: Updates the `Transaction` 's last known meter value / active energy import if applicable.

### Database Interactions
-   **Created**: `MeterValue` (Table: `MeterValues`)
-   **Updated**: `Transaction` (Table: `Transactions` - potentially updating current usage stats).
