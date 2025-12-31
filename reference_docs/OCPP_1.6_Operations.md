# OCPP 1.6 Operations: Charging Station to Central System

This document outlines the technical details for operations initiated by the Charging Station (CS) towards the Central System (CSMS) based on the OCPP 1.6 specification.

## 1. Authorize

### Logic

- **Purpose**: To verify if an identifier (idTag) is authorized to start or stop a charging session.
- **Behavior**:
  - The CS SHALL only supply energy after successful authorization.
  - Can be performed locally if the idTag is in the Local Authorization List or Authorization Cache.
  - If not found locally, the CS SHALL send an `Authorize.req` to the CSMS.
  - Upon receiving `Authorize.conf`, the CS SHOULD update its Authorization Cache if implemented.
  - Typically used before `StartTransaction`, but can be used for stopping if the identifier differs from the one used to start.

### Message Structure (`Authorize.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `idTag` | IdToken (String) | 1..1 (Required) | The identifier that needs to be authorized. |

### Expected Response Logic

- The CSMS verifies the validity of the `idTag`.
- Returns an authorization status (e.g., `Accepted`, `Blocked`, `Expired`, `Invalid`, `ConcurrentTx`).
- May provide `parentIdTag` and `expiryDate`.

### Response Message Structure (`Authorize.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `idTagInfo` | IdTagInfo | 1..1 (Required) | Contains status, expiry, and parent ID. |

---

## 2. Boot Notification

### Logic

- **Purpose**: To handshake with the CSMS upon startup or reboot and negotiate configuration.
- **Behavior**:
  - Sent immediately after the CS boots or reboots.
  - The CS SHALL NOT send any other request until it receives a `BootNotification.conf` with a status of `Accepted` or `Pending`.
  - If `Accepted`, the CS synchronizes its heartbeat interval and (recommended) internal clock with the response.
  - If `Rejected`, the CS must wait the specified retry interval before trying again.

### Message Structure (`BootNotification.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `chargePointVendor` | CiString20Type | 1..1 (Required) | Identifies the vendor of the Charge Point. |
| `chargePointModel` | CiString20Type | 1..1 (Required) | Identifies the model of the Charge Point. |
| `chargePointSerialNumber` | CiString25Type | 0..1 (Optional) | Serial number of the Charge Point. |
| `chargeBoxSerialNumber` | CiString25Type | 0..1 (Optional) | Serial number of the Charge Box. |
| `firmwareVersion` | CiString50Type | 0..1 (Optional) | Firmware version of the Charge Point. |
| `iccid` | CiString20Type | 0..1 (Optional) | ICCID of the modem’s SIM card. |
| `imsi` | CiString20Type | 0..1 (Optional) | IMSI of the modem’s SIM card. |
| `meterType` | CiString25Type | 0..1 (Optional) | Type of the main electrical meter. |
| `meterSerialNumber` | CiString25Type | 0..1 (Optional) | Serial number of the main electrical meter. |

### Expected Response Logic

- The CSMS validates the Charge Point's identity.
- Returns a status (`Accepted`, `Pending`, `Rejected`).
- Provides the current time (`currentTime`) for clock synchronization.
- Defines the `heartbeat` interval (`interval`) in seconds.

### Response Message Structure (`BootNotification.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `currentTime` | DateTime | 1..1 (Required) | Central System's current time. |
| `interval` | Integer | 1..1 (Required) | Heartbeat interval in seconds. |
| `status` | RegistrationStatus | 1..1 (Required) | Registration status (Accepted, Pending, Rejected). |

---

## 3. Data Transfer

### Logic

- **Purpose**: To send information for custom functions not supported by standard OCPP.
- **Behavior**:
  - Allows exchange of vendor-specific data.
  - `vendorId` should be a known identifier (often reversed DNS).
  - if CSMS doesn't recognize `vendorId` or `messageId`, it returns an error status.

### Message Structure (`DataTransfer.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `vendorId` | CiString255Type | 1..1 (Required) | Identifies the vendor-specific implementation. |
| `messageId` | CiString50Type | 0..1 (Optional) | Additional identification for the message. |
| `data` | Text | 0..1 (Optional) | The payload data. |

### Expected Response Logic

- The CSMS processes the vendor-specific data.
- Returns a success or failure status (`Accepted`, `Rejected`, `UnknownMessageId`, `UnknownVendorId`).
- Can optionally return data in response.

### Response Message Structure (`DataTransfer.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | DataTransferStatus | 1..1 (Required) | Status of the data transfer. |
| `data` | Text | 0..1 (Optional) | Response data. |

---

## 4. Diagnostics Status Notification

### Logic

- **Purpose**: To inform CSMS about the status of a diagnostics upload.
- **Behavior**:
  - Sent when the status of a requested diagnostics upload changes (e.g., Uploading, Uploaded, UploadFailed).
  - Can be triggered by a `TriggerMessage`.

### Message Structure (`DiagnosticsStatusNotification.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | DiagnosticsStatus | 1..1 (Required) | Status of the diagnostics upload (Idle, Uploading, Uploaded, UploadFailed). |

### Expected Response Logic

- The CSMS acknowledges the receipt of the status update.

### Response Message Structure (`DiagnosticsStatusNotification.conf`)

*No fields are defined for the response payload.*

---

## 5. Firmware Status Notification

### Logic

- **Purpose**: To inform CSMS about the progress of a firmware update.
- **Behavior**:
  - Sent during the download and installation process initiated by `UpdateFirmware.req`.
  - States include: Downloaded, DownloadFailed, Downloading, Idle, InstallationFailed, Installing, Installed.

### Message Structure (`FirmwareStatusNotification.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `status` | FirmwareStatus | 1..1 (Required) | Progress status of the firmware installation. |

### Expected Response Logic

- The CSMS acknowledges the receipt of the status update.

### Response Message Structure (`FirmwareStatusNotification.conf`)

*No fields are defined for the response payload.*

---

## 6. Heartbeat

### Logic

- **Purpose**: To signal that the CS is still connected and online.
- **Behavior**:
  - Sent periodically based on the configured heartbeat interval.
  - Can be skipped if other messages have been sent recently (traffic dependent).
  - Response contains current time for synchronization.

### Message Structure (`Heartbeat.req`)

*No fields are defined for the request payload.*

### Expected Response Logic

- The CSMS acknowledges that the Charge Point is alive.
- Returns the current time for clock synchronization.

### Response Message Structure (`Heartbeat.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `currentTime` | DateTime | 1..1 (Required) | Central System's current time. |

---

## 7. Meter Values

### Logic

- **Purpose**: To transmit electricity meter readings to the CSMS.
- **Behavior**:
  - Sent periodically or triggered by events as configured (e.g., transaction start/stop).
  - Can contain multiple sampled values for a specific connector or the main meter (connectorId 0).
  - Should specify context (e.g., Sample.Periodic, Transaction.Begin).

### Message Structure (`MeterValues.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector ID (>0) or 0 for main meter. |
| `transactionId` | Integer | 0..1 (Optional) | Related transaction ID (if paying per transaction). |
| `meterValue` | MeterValue[] | 1..* (Required) | List of sampled meter values with timestamps. |

**MeterValue Type**:

- `timestamp`: DateTime
- `sampledValue`: List of readings (containing value, context, format, measurand, phase, location, unit).

### Expected Response Logic

- The CSMS stores the meter readings.
- Should always respond with a confirmation, even if data sanity checks fail (to prevent the CS from retrying indefinitely).

### Response Message Structure (`MeterValues.conf`)

*No fields are defined for the response payload.*

---

## 8. Start Transaction

### Logic

- **Purpose**: To signal the start of a charging transaction.
- **Behavior**:
  - Sent when all conditions for charging are met (e.g., cable plugged, authorized).
  - Must define the `meterStart` value (Wh).
  - If a reservation was used, `reservationId` must be included.
  - CSMS responds with `transactionId` and authorization status.
  - If the auth status in response is not Accepted, the CS should stop the transaction (or fallback to configured behavior).

### Message Structure (`StartTransaction.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector used for the transaction. |
| `idTag` | IdToken | 1..1 (Required) | Identifier used to start the transaction. |
| `meterStart` | Integer | 1..1 (Required) | Meter value in Wh at start. |
| `timestamp` | DateTime | 1..1 (Required) | Start time of transaction. |
| `reservationId` | Integer | 0..1 (Optional) | ID of reservation being used. |

### Expected Response Logic

- The CSMS checks the authorization of the identifier again (as local cache might be outdated).
- Generates and returns a `transactionId` for the new session.
- Returns the `idTagInfo` with the authorization status.

### Response Message Structure (`StartTransaction.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `transactionId` | Integer | 1..1 (Required) | ID assigned to the transaction. |
| `idTagInfo` | IdTagInfo | 1..1 (Required) | Authorization status and info. |

---

## 9. Status Notification

### Logic

- **Purpose**: To report a change in status or an error condition.
- **Behavior**:
  - States: Available, Preparing, Charging, SuspendedEV, SuspendedEVSE, Finishing, Reserved, Unavailable, Faulted.
  - `errorCode` MUST be provided (use `NoError` if just a status change).
  - Sent for individual connectors (>0) or the whole Charge Point (0).

### Message Structure (`StatusNotification.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `connectorId` | Integer | 1..1 (Required) | Connector ID or 0 for main controller. |
| `status` | ChargePointStatus | 1..1 (Required) | Current status. |
| `errorCode` | ChargePointErrorCode | 1..1 (Required) | Error code (e.g., NoError, ConnectorLockFailure). |
| `info` | CiString50Type | 0..1 (Optional) | Additional info related to error. |
| `timestamp` | DateTime | 0..1 (Optional) | Time of status change. |
| `vendorId` | CiString255Type | 0..1 (Optional) | Vendor identifier. |
| `vendorErrorCode` | CiString50Type | 0..1 (Optional) | Vendor-specific error code. |

### Expected Response Logic

- The CSMS updates its internal state for the Charge Point or Connector.
- Acknowledges receipt of the notification.

### Response Message Structure (`StatusNotification.conf`)

*No fields are defined for the response payload.*

---

## 10. Stop Transaction

### Logic

- **Purpose**: To signal the end of a charging transaction.
- **Behavior**:
  - Sent when the transaction ends (cable unplugged, user stop, remote stop, fault).
  - Must include `meterStop` value and the `transactionId`.
  - Can include `transactionData` (Meter Values) for billing purposes.
  - `reason` field indicates why it stopped (e.g., Local, Remote, EVDisconnected).

### Message Structure (`StopTransaction.req`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `transactionId` | Integer | 1..1 (Required) | The ID from StartTransaction.conf. |
| `meterStop` | Integer | 1..1 (Required) | Meter value in Wh at end. |
| `timestamp` | DateTime | 1..1 (Required) | Stop time of transaction. |
| `idTag` | IdToken | 0..1 (Optional) | Identifier used to stop (if applicable). |
| `reason` | Reason | 0..1 (Optional) | Reason for stopping (default: Local). |
| `transactionData` | MeterValue[] | 0..* (Optional) | Meter values relevant for the transaction. |

### Expected Response Logic

- The CSMS processes the end of the transaction.
- Cannot prevent the transaction from stopping.
- May return `idTagInfo` (e.g., if the user needs to be re-authorized or cache updated).

### Response Message Structure (`StopTransaction.conf`)

| Field Name | Type | Cardinality | Description |
| :--- | :--- | :--- | :--- |
| `idTagInfo` | IdTagInfo | 0..1 (Optional) | Authorization status and info. |
