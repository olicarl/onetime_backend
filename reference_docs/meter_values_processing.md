# Meter Values Processing Logic

This document describes in detail how MeterValues messages from charging stations are processed and stored in the OnceTime Backend.

## Overview

The system processes `MeterValues` messages received via the OCPP 1.6 protocol. These values are used for real-time monitoring, billing calculation, and enforcing prepaid limits.

## Entry Point

When a `MeterValues` message arrives at the OCPP gateway, it is handled by the `ChargePoint.on_meter_values` method in `app/gateway/handlers/ocpp_handler.py`. This method forwards the payload to the `TransactionService`.

## Processing Logic

The core logic resides in `TransactionService.handle_meter_values` within `app/services/transactions.py`.

### 1. Data Parsing
The service extracts the following from the OCPP payload:
- `connector_id`
- `transaction_id`
- `meter_value`: A list of meter value sets, each containing a `timestamp` and a list of `sampled_value` objects.

### 2. Storage Criteria
A meter reading is recorded in the database **only if a `transaction_id` is provided** in the payload. Readings without a transaction ID (e.g., periodic clock-aligned readings when idle) are currently logged but not stored in the `meter_readings` table.

### 3. Database Storage
For each `sampled_value`, a new record is created in the `meter_readings` table with the following fields:

| Field | Description | Type |
|-------|-------------|------|
| `transaction_id` | Foreign key to the active `ChargingSession` | Integer |
| `timestamp` | The time the sample was taken | DateTime |
| `measurand` | The type of value measured (Default: `Energy.Active.Import.Register`) | String |
| `value` | The actual measurement | String |
| `unit` | The unit of measurement (e.g., `Wh`, `W`, `V`, `A`) | String |
| `phase` | The electrical phase (if applicable) | String |
| `context` | The context of the measurement (e.g., `Sample.Periodic`, `Transaction.End`) | String |

## Prepaid Billing Enforcement

The `handle_meter_values` service also implements real-time enforcement for prepaid users:

1. **Energy Calculation**: It looks for the latest sampled value where `measurand` is `"Energy.Active.Import.Register"`.
2. **Consumption Tracking**: It calculates total consumption for the session:
   `consumed_kwh = (latest_meter_value - session.meter_start) / 1000.0`
3. **Limit Check**: If the system is in **Prepaid Mode**, it compares `consumed_kwh` against the Renter's `prepaid_balance_kwh`.
4. **Remote Stop**: If the consumption reaches or exceeds the available balance, the system automatically triggers a `RemoteStopTransactionRequest` to the charging station to terminate the session immediately.

## Data Persistence

Readings are stored in the `meter_readings` table and are linked to `charging_sessions` via the `transaction_id`. This allows for historical analysis of energy usage patterns for every charging session.
