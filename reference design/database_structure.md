# Database Structure

This document outlines the database tables and models found in the `citrineos-core` project.

## Models

### Tenant
- **Table Name**: `Tenant`
- **Description**: Represents a tenant in the system.
- **Columns**:
  - `id` (INTEGER, PK): Unique identifier.
  - `name` (STRING): Tenant name.
  - `url` (STRING): Tenant URL.
  - `partyId` (STRING): OCPI Party ID.
  - `countryCode` (STRING): OCPI Country Code.
  - `serverProfileOCPI` (JSONB): OCPI Server Profile.
- **Relationships**:
  - HasMany: TenantPartner, Authorization, Boot, Certificate, ChargingStation, Transaction, etc.

### TenantPartner
- **Table Name**: `TenantPartner`
- **Description**: Represents a partner tenant (e.g., eMSP) for roaming.
- **Columns**:
  - `partyId` (STRING): OCPI Party ID.
  - `countryCode` (STRING): OCPI Country Code.
  - `partnerProfileOCPI` (JSONB): OCPI Partner Profile.
- **Relationships**:
  - HasMany: Authorization.

### Authorization
- **Table Name**: `AuthorizationData`
- **Description**: Contains authorization data for identifying tokens.
- **Columns**:
  - `idToken` (STRING): The identifier token.
  - `idTokenType` (STRING): Type of the token (e.g., ISO14443).
  - `status` (STRING): Authorization status.
  - `cacheExpiryDateTime` (DATE): When the cache expires.
  - `groupAuthorizationId` (INTEGER, FK): Reference to a group authorization.
  - `tenantPartnerId` (INTEGER, FK): Reference to the tenant partner.
- **Relationships**:
  - BelongsTo: TenantPartner, Authorization (Group).

### ChargingStation
- **Table Name**: `ChargingStation`
- **Description**: Represents a physical charging station.
- **Columns**:
  - `id` (STRING, PK): Station ID.
  - `isOnline` (BOOLEAN): Online status.
  - `protocol` (STRING): OCPP Version.
  - `locationId` (INTEGER, FK): Reference to the location.
  - `coordinates` (GEOMETRY): GPS coordinates.
- **Relationships**:
  - BelongsTo: Location.
  - HasMany: Evse, Connector, Transaction, StatusNotification.

### Transaction
- **Table Name**: `Transactions`
- **Description**: Represents a charging transaction.
- **Columns**:
  - `transactionId` (STRING): Unique transaction ID from the station.
  - `stationId` (STRING, FK): Reference to the station.
  - `evseId` (INTEGER, FK): Reference to the EVSE.
  - `connectorId` (INTEGER, FK): Reference to the connector.
  - `authorizationId` (INTEGER, FK): Reference to the authorization used.
  - `isActive` (BOOLEAN): Whether the transaction is active.
  - `startTime` (DATE): Start time.
  - `endTime` (DATE): End time.
  - `totalKwh` (DECIMAL): Total energy consumed.
  - `totalCost` (DECIMAL): Total cost.
- **Relationships**:
  - BelongsTo: ChargingStation, Evse, Connector, Authorization, Tariff, Location.
  - HasMany: MeterValue, TransactionEvent.

### Location
- **Table Name**: `Location`
- **Description**: Represents a physical location containing charging stations.
- **Columns**:
  - `name` (STRING): Location name.
  - `address` (STRING): Address.
  - `city` (STRING): City.
  - `postalCode` (STRING): Postal code.
  - `country` (STRING): Country.
  - `coordinates` (GEOMETRY): GPS coordinates.
  - `facilities` (JSONB): List of facilities.
- **Relationships**:
  - HasMany: ChargingStation.

### Evse
- **Table Name**: `Evse`
- **Description**: Represents an Electric Vehicle Supply Equipment.
- **Columns**:
  - `stationId` (STRING, FK): Station ID.
  - `evseId` (STRING): EVSE ID (eMI3 compliant).
  - `evseTypeId` (INTEGER): Internal ID.
  - `physicalReference` (STRING): Physical reference.
- **Relationships**:
  - BelongsTo: ChargingStation.
  - HasMany: Connector.

### Connector
- **Table Name**: `Connector`
- **Description**: Represents a connector on an EVSE.
- **Columns**:
  - `stationId` (STRING, FK): Station ID.
  - `evseId` (INTEGER, FK): EVSE ID.
  - `connectorId` (INTEGER): Connector ID (OCPP 1.6).
  - `status` (STRING): Current status.
  - `type` (STRING): Connector type (e.g., Type 2).
  - `format` (STRING): Connector format (Socket/Cable).
  - `powerType` (STRING): Power type (AC/DC).
- **Relationships**:
  - BelongsTo: ChargingStation, Evse.
  - HasMany: Tariff.

### ChargingProfile
- **Table Name**: `ChargingProfile`
- **Description**: Represents a charging profile for smart charging.
- **Columns**:
  - `id` (INTEGER): Profile ID.
  - `stationId` (STRING): Station ID.
  - `stackLevel` (INTEGER): Stack level.
  - `chargingProfilePurpose` (STRING): Purpose (e.g., TxProfile).
  - `chargingProfileKind` (STRING): Kind (e.g., Absolute).
  - `validFrom` (DATE): Start validity.
  - `validTo` (DATE): End validity.
- **Relationships**:
  - BelongsTo: Transaction.
  - HasMany: ChargingSchedule.

### Boot
- **Table Name**: `BootConfig`
- **Description**: Stores boot configuration and status for a station.
- **Columns**:
  - `id` (STRING, PK): Station ID.
  - `lastBootTime` (DATE): Last boot timestamp.
  - `status` (STRING): Boot status (Accepted/Rejected).
  - `heartbeatInterval` (INTEGER): Heartbeat interval.

### TransactionEvent
- **Table Name**: `TransactionEventRequest`
- **Description**: Records events related to a transaction.
- **Columns**:
  - `stationId` (STRING): Station ID.
  - `eventType` (STRING): Event type (Started, Updated, Ended).
  - `timestamp` (DATE): Event timestamp.
  - `triggerReason` (STRING): Reason for the event.
  - `seqNo` (INTEGER): Sequence number.
  - `transactionInfo` (JSON): specific transaction info.
- **Relationships**:
  - BelongsTo: Transaction, EvseType.
  - HasMany: MeterValue.

### MeterValue
- **Table Name**: `MeterValue`
- **Description**: Represents meter readings.
- **Columns**:
  - `timestamp` (DATE): Reading timestamp.
  - `sampledValue` (JSONB): The value(s).
- **Relationships**:
  - BelongsTo: TransactionEvent, Transaction, Tariff.

### Variable
- **Table Name**: `VariableType`
- **Description**: Represents a variable in the device model.
- **Columns**:
  - `name` (STRING): Variable name.
  - `instance` (STRING): Variable instance.
- **Relationships**:
  - BelongsToMany: Component.

### Component
- **Table Name**: `ComponentType`
- **Description**: Represents a component in the device model.
- **Columns**:
  - `name` (STRING): Component name.
  - `instance` (STRING): Component instance.
- **Relationships**:
  - BelongsToMany: Variable.
  - BelongsTo: EvseType.

### Tariff
- **Table Name**: `Tariff`
- **Description**: Pricing information.
- **Columns**:
  - `currency` (STRING): Currency code.
  - `pricePerKwh` (DECIMAL): Price per kWh.
  - `pricePerMin` (DECIMAL): Price per minute.
  - `pricePerSession` (DECIMAL): Price per session.
- **Relationships**:
  - BelongsTo: Connector.

### Subscription
- **Table Name**: `Subscription`
- **Description**: Callback subscriptions.
- **Columns**:
  - `stationId` (STRING): Target station ID.
  - `url` (STRING): Callback URL.
  - `onConnect` (BOOLEAN): Trigger on connect.
  - `onClose` (BOOLEAN): Trigger on close.

### MessageInfo
- **Table Name**: `MessageInfoType`
- **Description**: Display messages for the station.
- **Columns**:
  - `priority` (STRING): Message priority.
  - `state` (STRING): Message state.
  - `message` (JSON): The message content.
- **Relationships**:
  - BelongsTo: Component (Display).

### SecurityEvent
- **Table Name**: `SecurityEventNotificationRequest`
- **Description**: Log of security events.
- **Columns**:
  - `stationId` (STRING): Station ID.
  - `type` (STRING): Event type.
  - `techInfo` (STRING): Technical info.

### Reservation
- **Table Name**: `ReserveNowRequest`
- **Description**: Reservations of EVSEs.
- **Columns**:
  - `id` (INTEGER): Reservation ID.
  - `stationId` (STRING): Station ID.
  - `expiryDateTime` (DATE): Expiry time.
  - `idToken` (JSONB): Token used for reservation.
- **Relationships**:
  - BelongsTo: EvseType.

### ChargingStationSecurityInfo
- **Table Name**: `ChargingStationSecurityInfo`
- **Description**: Security info for a station.
- **Columns**:
  - `stationId` (STRING): Station ID.
  - `publicKeyFileId` (STRING): ID of the public key file.

### ChangeConfiguration
- **Table Name**: `ChangeConfiguration`
- **Description**: Configuration changes for a station.
- **Columns**:
  - `stationId` (STRING): Station ID.
  - `key` (STRING): Configuration key.
  - `value` (STRING): Configuration value.
  - `readonly` (BOOLEAN): Is read-only.

### Certificate
- **Table Name**: `Certificate`
- **Description**: Stored certificates.
- **Columns**:
  - `serialNumber` (BIGINT): Serial number.
  - `issuerName` (STRING): Issuer name.
  - `validBefore` (DATE): Expiry date.
  - `certificateFileId` (STRING): File ID for the certificate.
  - `privateKeyFileId` (STRING): File ID for the private key.

### InstalledCertificate
- **Table Name**: `InstalledCertificate`
- **Description**: Certificates installed on a station.
- **Columns**:
  - `stationId` (STRING, FK): Station ID.
  - `hashAlgorithm` (STRING): Hash algorithm.
  - `certificateType` (STRING): Type of certificate.
- **Relationships**:
  - BelongsTo: ChargingStation.

### ChargingStationSequence
- **Table Name**: `ChargingStationSequence`
- **Description**: Sequences for station messages.
- **Columns**:
  - `stationId` (STRING, FK): Station ID.
  - `type` (STRING): Sequence type.
  - `value` (BIGINT): Sequence value.

### LocalListAuthorization
- **Table Name**: `LocalListAuthorization`
- **Description**: Snapshot of authorization on a local list.
- **Columns**:
  - `idToken` (STRING): ID Token.
  - `status` (STRING): Status.
  - `authorizationId` (INTEGER, FK): Original authorization ID.
- **Relationships**:
  - BelongsTo: Authorization.


