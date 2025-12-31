# OCPP 1.6 Operations: Central System to Charging Station

This document outlines the technical details for operations initiated by the Central System (CSMS) towards the Charging Station (CS) based on the OCPP 1.6 specification.

## 1. Cancel Reservation

### Logic

- **Purpose**: To cancel an existing reservation.
- **Behavior**:
  - CSMS sends `CancelReservation.req` with the `reservationId`.
  - CS checks if the reservation exists.
  - If found, it removes the reservation and returns `Accepted`.
  - If not found, it returns `Rejected`.

### Message Structure (`CancelReservation.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `reservationId` | Integer | 1..1 (Required) | Id of the reservation to cancel. |

### Expected Response Logic

- The CS attempts to find and cancel the reservation.
- Returns status `Accepted` if successful, or `Rejected` if the reservation ID was not found.

### Response Message Structure (`CancelReservation.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | CancelReservationStatus | 1..1 (Required) | Success or failure (Accepted, Rejected). |

---

## 2. Change Availability

### Logic

- **Purpose**: To change the availability of a connector or the entire Charge Point.
- **Behavior**:
  - CSMS request can be for `Operative` (available for charging) or `Inoperative` (unavailable).
  - Can apply to a specific connector (>0) or the whole Charge Point (0).
  - If a transaction is in progress, the CS should queue the change and return `Scheduled`.
  - Persistent state: `Inoperative` status should persist across reboots.

### Message Structure (`ChangeAvailability.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector ID (0 for all). |
| `type` | AvailabilityType | 1..1 (Required) | Operative or Inoperative. |

### Expected Response Logic

- The CS attempts to change the availability.
- Returns `Accepted` if changed, `Rejected` if it cannot, or `Scheduled` if busy.

### Response Message Structure (`ChangeAvailability.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | AvailabilityStatus | 1..1 (Required) | Accepted, Rejected, Scheduled. |

---

## 3. Change Configuration

### Logic

- **Purpose**: To change a configuration setting on the Charge Point.
- **Behavior**:
  - CSMS sends a key-value pair.
  - CS attempts to apply the setting.
  - If successful and effective immediately: `Accepted`.
  - If successful but requires reboot: `RebootRequired`.
  - If key not supported: `NotSupported`.
  - If validation fails: `Rejected`.

### Message Structure (`ChangeConfiguration.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `key` | CiString50Type | 1..1 (Required) | Configuration key name. |
| `value` | CiString500Type | 1..1 (Required) | New value. |

### Expected Response Logic

- The CS tries to update the configuration key.
- Returns the result status.

### Response Message Structure (`ChangeConfiguration.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | ConfigurationStatus | 1..1 (Required) | Accepted, Rejected, RebootRequired, NotSupported. |

---

## 4. Clear Cache

### Logic

- **Purpose**: To clear the local Authorization Cache.
- **Behavior**:
  - CSMS sends request.
  - CS clears its cache if implemented.

### Message Structure (`ClearCache.req`)

*No fields are defined for the request payload.*

### Expected Response Logic

- The CS clears the cache.
- Returns `Accepted` if successful (or if cache is empty), `Rejected` if it cannot.

### Response Message Structure (`ClearCache.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | ClearCacheStatus | 1..1 (Required) | Accepted, Rejected. |

---

## 5. Clear Charging Profile

### Logic

- **Purpose**: To remove installed charging profiles.
- **Behavior**:
  - Filters can be applied: `id`, `connectorId`, `chargingProfilePurpose`, `stackLevel`.
  - If parameters are missing, it acts as a wildcard removal.

### Message Structure (`ClearChargingProfile.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | 0..1 (Optional) | Specific profile ID. |
| `connectorId` | Integer | 0..1 (Optional) | Connector ID. |
| `chargingProfilePurpose` | ChargingProfilePurpose | 0..1 (Optional) | Purpose filter. |
| `stackLevel` | Integer | 0..1 (Optional) | Stack level filter. |

### Expected Response Logic

- The CS removes matching profiles.
- Returns `Accepted` if successful/processed, `Unknown` if id not found.

### Response Message Structure (`ClearChargingProfile.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | ClearChargingProfileStatus | 1..1 (Required) | Accepted, Unknown. |

---

## 6. Data Transfer

### Logic

- **Purpose**: To send vendor-specific data to the Charge Point.
- **Behavior**:
  - Symmetric to the CS initiated operation.
  - Requires known `vendorId`.

### Message Structure (`DataTransfer.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `vendorId` | CiString255Type | 1..1 (Required) | Vendor identifier. |
| `messageId` | CiString50Type | 0..1 (Optional) | Message identifier. |
| `data` | Text | 0..1 (Optional) | Payload data. |

### Expected Response Logic

- The CS processes the data.
- Returns status and optional response data.

### Response Message Structure (`DataTransfer.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | DataTransferStatus | 1..1 (Required) | Accepted, Rejected, UnknownMessageId, UnknownVendorId. |
| `data` | Text | 0..1 (Optional) | Response data. |

---

## 7. Get Composite Schedule

### Logic

- **Purpose**: To retrieve the calculated charging schedule for a specific connector and duration.
- **Behavior**:
  - CS calculates the expected power/current limits based on all active profiles and local limits.
  - Returns the schedule for `duration` seconds.

### Message Structure (`GetCompositeSchedule.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector ID. |
| `duration` | Integer | 1..1 (Required) | Duration in seconds. |
| `chargingRateUnit` | ChargingRateUnit | 0..1 (Optional) | A (Amps) or W (Watts). |

### Expected Response Logic

- The CS calculates the composite schedule.
- Returns `Accepted` with the schedule, or `Rejected`.

### Response Message Structure (`GetCompositeSchedule.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | GetCompositeScheduleStatus | 1..1 (Required) | Accepted, Rejected. |
| `connectorId` | Integer | 0..1 (Optional) | Connector ID. |
| `scheduleStart` | DateTime | 0..1 (Optional) | Start time of schedule. |
| `chargingSchedule` | ChargingSchedule | 0..1 (Optional) | The calculated schedule. |

---

## 8. Get Configuration

### Logic

- **Purpose**: To retrieve current configuration values.
- **Behavior**:
  - If keys are provided, CS returns only those.
  - If keys list is empty, CS returns ALL known configuration keys.
  - Unrecognized keys are returned in `unknownKey`.

### Message Structure (`GetConfiguration.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `key` | CiString50Type[] | 0..* (Optional) | List of keys. |

### Expected Response Logic

- The CS looks up values.
- Returns list of `configurationKey` (key, value, readonly) and `unknownKey`.

### Response Message Structure (`GetConfiguration.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `configurationKey` | KeyValue[] | 0..* (Optional) | List of key-value pairs. |
| `unknownKey` | CiString50Type[] | 0..* (Optional) | List of unknown keys. |

---

## 9. Get Diagnostics

### Logic

- **Purpose**: To request the Charge Point to upload diagnostics logs.
- **Behavior**:
  - CSMS provides a `location` (URL) for upload.
  - CS validates the request and availability of logs.
  - If accepted, CS responds with the filename it will use.
  - ACTUAL upload happens asynchronously, reporting status via `DiagnosticsStatusNotification`.

### Message Structure (`GetDiagnostics.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `location` | AnyURI | 1..1 (Required) | Upload URL. |
| `retries` | Integer | 0..1 (Optional) | Retry count. |
| `retryInterval` | Integer | 0..1 (Optional) | Interval between retries. |
| `startTime` | DateTime | 0..1 (Optional) | Start of log period. |
| `stopTime` | DateTime | 0..1 (Optional) | End of log period. |

### Expected Response Logic

- The CS checks if it can perform the upload.
- Returns filename if accepted.

### Response Message Structure (`GetDiagnostics.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `fileName` | CiString255Type | 0..1 (Optional) | Name of file to be uploaded. |

---

## 10. Get Local List Version

### Logic

- **Purpose**: To check if the local authorization list is in sync.
- **Behavior**:
  - CS returns the current version of its local list.
  - 0 means empty list. -1 means not supported.

### Message Structure (`GetLocalListVersion.req`)

*No fields are defined for the request payload.*

### Expected Response Logic

- The CS checks its list version.

### Response Message Structure (`GetLocalListVersion.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `listVersion` | Integer | 1..1 (Required) | Current version number. |

---

## 11. Remote Start Transaction

### Logic

- **Purpose**: To instruct the CS to start a transaction for a user (e.g., from mobile app).
- **Behavior**:
  - If `AuthorizeRemoteTxRequests` is true: CS must authorize the `idTag` first (Local or with Authorize.req).
  - If false: CS starts immediately.
  - If successful, CS sends `StartTransaction.req`.
  - Can include a specific `chargingProfile` for the transaction.

### Message Structure (`RemoteStartTransaction.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 0..1 (Optional) | Specific connector. |
| `idTag` | IdToken | 1..1 (Required) | User identifier. |
| `chargingProfile` | ChargingProfile | 0..1 (Optional) | Profile for this tx. |

### Expected Response Logic

- The CS validates if it can start.
- Returns `Accepted` if it will attempt to start, `Rejected` otherwise.

### Response Message Structure (`RemoteStartTransaction.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | RemoteStartStopStatus | 1..1 (Required) | Accepted, Rejected. |

---

## 12. Remote Stop Transaction

### Logic

- **Purpose**: To currently stop an ongoing transaction.
- **Behavior**:
  - CS logic is same as extensive local stop (unlocks cable etc.).
  - Triggers a `StopTransaction.req` from the CS.

### Message Structure (`RemoteStopTransaction.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `transactionId` | Integer | 1..1 (Required) | ID of the transaction to stop. |

### Expected Response Logic

- The CS checks if the transaction ID exists and is active.
- Returns `Accepted` or `Rejected`.

### Response Message Structure (`RemoteStopTransaction.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | RemoteStartStopStatus | 1..1 (Required) | Accepted, Rejected. |

---

## 13. Reserve Now

### Logic

- **Purpose**: To reserve a connector for a specific user.
- **Behavior**:
  - If connector is Available, CS locks it (or virtually reserves it) for the `idTag`.
  - Expires at `expiryDate`.
  - If `reservationId` matches existing, update it.
  - If connector 0, CS keeps at least one connector available.

### Message Structure (`ReserveNow.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector to reserve. |
| `expiryDate` | DateTime | 1..1 (Required) | Expiration time. |
| `idTag` | IdToken | 1..1 (Required) | User ID. |
| `parentIdTag` | IdToken | 0..1 (Optional) | Parent ID. |
| `reservationId` | Integer | 1..1 (Required) | Unique reservation ID. |

### Expected Response Logic

- The CS tries to apply the reservation.
- Returns `Accepted`, `Faulted`, `Occupied`, `Rejected`, or `Unavailable`.

### Response Message Structure (`ReserveNow.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | ReservationStatus | 1..1 (Required) | Result status. |

---

## 14. Reset

### Logic

- **Purpose**: To restart the Charge Point.
- **Behavior**:
  - `Soft`: Graceful shutdown, stop transactions, restart software.
  - `Hard`: Immediate hardware restart (transactions might not stop gracefully).
  - CS should send `StopTransaction` before resetting if possible.

### Message Structure (`Reset.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `type` | ResetType | 1..1 (Required) | Hard or Soft. |

### Expected Response Logic

- The CS acknowledges the request.
- Returns `Accepted` if it will perform the reset, `Rejected` otherwise.

### Response Message Structure (`Reset.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | ResetStatus | 1..1 (Required) | Accepted, Rejected. |

---

## 15. Send Local List

### Logic

- **Purpose**: To update the Local Authorization List.
- **Behavior**:
  - `Full`: Replace entire list.
  - `Differential`: Update changes only.
  - CS validates the integrity of the update.

### Message Structure (`SendLocalList.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `listVersion` | Integer | 1..1 (Required) | New version number. |
| `localAuthorizationList` | AuthorizationData[] | 0..* (Optional) | List items. |
| `updateType` | UpdateType | 1..1 (Required) | Full or Differential. |

### Expected Response Logic

- The CS applies the update.
- Returns `Accepted`, `Failed`, `NotSupported`, or `VersionMismatch`.

### Response Message Structure (`SendLocalList.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | UpdateStatus | 1..1 (Required) | Result status. |

---

## 16. Set Charging Profile

### Logic

- **Purpose**: To set a charging schedule/limit.
- **Behavior**:
  - Used for Smart Charging.
  - Can set profiles for TxProfile (transaction specific), ChargePointMaxProfile (entire charger), or TxDefaultProfile (default for new tx).
  - Replaces existing matching profiles (same id or stack/purpose).

### Message Structure (`SetChargingProfile.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector ID (0 for all). |
| `csChargingProfiles` | ChargingProfile | 1..1 (Required) | The profile data. |

### Expected Response Logic

- The CS validates and stores the profile.
- Returns `Accepted`, `Rejected`, or `NotSupported`.

### Response Message Structure (`SetChargingProfile.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | ChargingProfileStatus | 1..1 (Required) | Result status. |

---

## 17. Trigger Message

### Logic

- **Purpose**: To request the CS to send a specific message (e.g., StatusNotification, MeterValues).
- **Behavior**:
  - Useful for resynchronizing state or forcing a heartbeat.
  - "Requested message is leading": if connectorId not relevant, ignore it.

### Message Structure (`TriggerMessage.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `requestedMessage` | MessageTrigger | 1..1 (Required) | BootNotification, DiagnosticsStatusNotification, FirmwareStatusNotification, Heartbeat, MeterValues, StatusNotification. |
| `connectorId` | Integer | 0..1 (Optional) | Connector ID. |

### Expected Response Logic

- CS checks if it can send the message.
- Returns `Accepted` or `Rejected`/`NotImplemented`.
- **Note**: The actual message is sent separately AFTER the confirmation.

### Response Message Structure (`TriggerMessage.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | TriggerMessageStatus | 1..1 (Required) | Accepted, Rejected, NotImplemented. |

---

## 18. Unlock Connector

### Logic

- **Purpose**: To force unlock the connector cable.
- **Behavior**:
  - Used for help-desk support if cable is stuck.
  - Not for stopping transactions (but if tx is active, CS SHOULD stop it first).

### Message Structure (`UnlockConnector.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector to unlock. |

### Expected Response Logic

- The CS attempts to unlock.
- Returns `Unlocked`, `UnlockFailed`, or `NotSupported`.

### Response Message Structure (`UnlockConnector.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | UnlockStatus | 1..1 (Required) | Result status. |

---

## 19. Update Firmware

### Logic

- **Purpose**: To instruct the CS to download and install new firmware.
- **Behavior**:
  - CSMS provides URL and retrieve date.
  - CS downloads firmware (reporting status via `FirmwareStatusNotification`).
  - CS installs and reboots.

### Message Structure (`UpdateFirmware.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `location` | AnyURI | 1..1 (Required) | Download URL. |
| `retries` | Integer | 0..1 (Optional) | Retry count. |
| `retrieveDate` | DateTime | 1..1 (Required) | When to start. |
| `retryInterval` | Integer | 0..1 (Optional) | Retry interval. |

### Expected Response Logic

- CS accepts the instruction.
- Only checks parameter validity (not the firmware itself yet).

### Response Message Structure (`UpdateFirmware.conf`)

*No fields are defined for the response payload.*
