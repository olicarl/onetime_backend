# System Architecture

This document describes the architecture, technology stack, and software components used in the `citrineos-core` project.

## Architecture Pattern
The system follows a **Modular Monolith** architecture, designed to be deployed as either a single monolithic service or distributed microservices.
- **Core Server**: The `Server` module acts as the central entry point (`Server/src/index.ts`).
- **Dynamic Module Loading**: Modules (e.g., Transactions, Configuration) are loaded at runtime based on the `APP_NAME` environment variable. This allows running all modules in one process (`APP_NAME=all`) or segregating them into different containers.

## Technology Stack

### Core
- **Language**: TypeScript (v5.8.2)
- **Runtime**: Node.js (>=22.11.0)
- **Web Framework**: Fastify (v5.1.0) - Chosen for high performance and low overhead.

### Data & Persistence
- **Database**: PostgreSQL (v16 with PostGIS 3.5).
- **ORM**: Sequelize (with `sequelize-typescript` decorators).
- **Migrations**: Sequelize CLI.
- **Cache**: Redis (optional, supports clustering) or In-Memory (default for local dev).

### Messaging & Event Architecture
- **Message Broker**: RabbitMQ.
- **Pattern**: Asynchronous event-driven communication between modules.

### Interfaces & Validation
- **Protocol**: OCPP 2.0.1 and OCPP 1.6 (via mappers).
- **Validation**:
    - **AJV**: For JSON Schema validation (OCPP messages).
    - **Zod**: For internal data structures.
- **API Documentation**: Swagger/OpenAPI.

### Infrastructure & Operations
- **Containerization**: Docker & Docker Compose.
- **File Storage**: MinIO (S3 compatible) for large asset storage.
- **CMS**: Directus (Headless CMS for admin/content management).
- **GraphQL**: Hasura (Instant GraphQL API over PostgreSQL).

## Software Components / Modules
The system is divided into functional modules:

| Module | Description |
| :--- | :--- |
| **00_Base** | Core interfaces, DTOs, and shared utilities. |
| **01_Data** | Database models (Sequelize), repositories, and migrations. |
| **02_Util** | Shared utilities (Logging, Auth, Cache, Message Broker implementations). |
| **03_Modules/Certificates** | Management of charging station certificates (ISO 15118). |
| **03_Modules/Configuration** | Get/Set configuration variables for stations. |
| **03_Modules/EVDriver** | Authorization and authentication of EV drivers. |
| **03_Modules/Monitoring** | Monitoring of station variables and events. |
| **03_Modules/OcppRouter** | Routes incoming OCPP messages to appropriate modules. |
| **03_Modules/Reporting** | Security events and reporting logic. |
| **03_Modules/SmartCharging** | Smart charging profiles and schedules. |
| **03_Modules/Transactions** | Handling of transaction events and meter values. |
| **03_Modules/Tenant** | Multi-tenancy support. |
