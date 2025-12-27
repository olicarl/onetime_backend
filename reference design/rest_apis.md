# CitrineOS REST API Reference

This document details the REST APIs available in `citrineos-core`. These APIs are divided into **Data APIs** (CRUD operations on system resources) and **Message APIs** (triggering OCPP messages to charging stations).

## Endpoint Structure
All endpoints typically follow a structure defined by the module's configuration data, but generally follow:
`POST /<module_prefix>/<namespace_or_message>`

## 1. Certificates Module

**Data API** (`CertificatesDataApi`)

| Method | Endpoint | Description | Query Params | Body |
| :--- | :--- | :--- | :--- | :--- |
| `PUT` | `/certificates/tls` | Update TLS certificates for a websocket server. | `id` (Server ID) | `TlsCertificatesRequest` |
| `POST` | `/certificates/chain` | Generate a certificate chain (Root, SubCA, Leaf). | `tenantId` | `GenerateCertificateChainRequest` |
| `PUT` | `/certificates/root` | Install a Root Certificate on a station. | - | `InstallRootCertificateRequest` |

## 2. Configuration Module

**Data API** (`ConfigurationDataApi`)

| Method | Endpoint | Description | Query Params | Body |
| :--- | :--- | :--- | :--- | :--- |
| `PUT` | `/configuration/boot` | Create or update the Boot Config for a station. | `tenantId`, `stationId` | `BootNotificationResponse` |
| `GET` | `/configuration/boot` | Get the Boot Config for a station. | `tenantId`, `stationId` | - |
| `DELETE` | `/configuration/boot` | Delete the Boot Config for a station. | `tenantId`, `stationId` | - |
| `POST` | `/configuration/k` | Update Charging Station Password. | `tenantId`, `callbackUrl` | `UpdateChargingStationPasswordRequest` |
| `GET` | `/configuration/network` | Get Network Profiles. | `stationId`, `tenantId` | - |
| `DELETE` | `/configuration/network` | Delete Network Profiles. | `stationId`, `tenantId`, `configSlot` | - |

**Message API (OCPP 1.6)** (`ConfigurationOcpp16Api`)

| Method | Endpoint | Description | Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/configuration/getConfiguration` | Trigger `GetConfiguration`. | `GetConfigurationRequest` |
| `POST` | `/configuration/changeConfiguration` | Trigger `ChangeConfiguration`. | `ChangeConfigurationRequest` |
| `POST` | `/configuration/triggerMessage` | Trigger `TriggerMessage`. | `TriggerMessageRequest` |
| `POST` | `/configuration/reset` | Trigger `Reset`. | `ResetRequest` |
| `POST` | `/configuration/changeAvailability` | Trigger `ChangeAvailability`. | `ChangeAvailabilityRequest` |
| `POST` | `/configuration/updateFirmware` | Trigger `UpdateFirmware`. | `UpdateFirmwareRequest` |

## 3. EV Driver Module

**Data API** (`EVDriverDataApi`)

| Method | Endpoint | Description | Query Params | Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/evdriver/locallist` | Get Local Authorization List Version. | `tenantId`, `stationId` | - |

**Message API (OCPP 1.6)** (`EVDriverOcpp16Api`)

| Method | Endpoint | Description | Body |
| :--- | :--- | :--- | :--- |
| `POST` | `/evdriver/remoteStartTransaction` | Trigger `RemoteStartTransaction`. | `RemoteStartTransactionRequest` |
| `POST` | `/evdriver/remoteStopTransaction` | Trigger `RemoteStopTransaction`. | `RemoteStopTransactionRequest` |
| `POST` | `/evdriver/unlockConnector` | Trigger `UnlockConnector`. | `UnlockConnectorRequest` |

## 4. Monitoring Module

**Data API** (`MonitoringDataApi`)

| Method | Endpoint | Description | Query Params | Body |
| :--- | :--- | :--- | :--- | :--- |
| `PUT` | `/monitoring/variables` | Create or update Device Model variables. | `tenantId`, `stationId`, `setOnCharger` | `ReportDataType` |
| `GET` | `/monitoring/variables` | Get Device Model variables. | `tenantId`, `stationId`, `component`, `variable` | - |
| `DELETE` | `/monitoring/variables` | Delete Device Model variables. | `tenantId`, `stationId`, ... | - |

## 5. Transactions Module

**Data API** (`TransactionsDataApi`)

| Method | Endpoint | Description | Query Params | Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/transactions` | Get a specific transaction. | `tenantId`, `stationId`, `transactionId` | - |
| `PUT` | `/transactions/tariffs` | Create or update a Tariff. | `tenantId` | `UpsertTariffRequest` |
| `GET` | `/transactions/tariffs` | Get Tariffs. | `tenantId` | - |
| `DELETE` | `/transactions/tariffs` | Delete Tariffs. | `tenantId` | - |

## Notes
-   **Namespace Mapping**: Endpoints often map to specific namespaces defined in `@citrineos/base`.
-   **Method**: While many message triggers use `POST` (RPC style), Data APIs use proper REST verbs (`GET`, `PUT`, `DELETE`).
-   **Prefixes**: The URL prefixes (e.g., `/configuration`) are configurable via `system-config` but default to the module names.
