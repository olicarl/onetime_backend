# Onetime Backend (OCPP 1.6 CSMS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

A scalable, modular backend for an EV Charging Station Management System (CSMS) built with a **Simplified Monolithic Architecture**. This project implements the **OCPP 1.6 JSON** protocol, designed for reliability and ease of deployment.

## 🎯 Purpose

The goal of this project is to provide a **Home Assistant-style backend** for multi-family home parking lots where many charging stations are installed. It is designed to run on any Linux computer (e.g., Raspberry Pi) and focuses on simplicity, low resource usage, and ease of maintenance.

**Key Advantages:**

- **Offline Capability**: Not reliant on a stable internet connection for authentication or charging sessions.
- **Cost-Effective**: No recurring costs; one-time hardware cost (e.g., Raspberry Pi).
- **Easy Setup**: Simple one-time setup process.
- **Simplified Security**: Operated behind a router, removing the need for complex security configurations.
- **High Stability**: Optimized for typical installations of fewer than 200 charging points.
- **Billing Integration**: Server can send invoices directly to tenants or forward 15-minute energy consumption intervals to ZEV billing solutions (Zusammenschluss zum Eigenverbrauch).

**Target Audience:**

- **Electricians & Installers**: Designed to be easily installed and commissioned by professionals without deep IT knowledge.

## 🚀 Features

- **OCPP 1.6 JSON Support**: Full WebSocket handling using `mobilityhouse/ocpp`.
- **Monolithic Architecture**:
  - **Single Process**: Runs as a single, lightweight FastAPI application.
  - **In-Memory Event Bus**: Decoupled internal communication using `pyee` instead of complex message brokers.
- **Simplicity**: No RabbitMQ or microservices overhead. Just Docker + Postgres.
- **Dockerized**: specific container for the application and database.
- **Extensible**: Modular logic layer for adding new features easily.

### Future Features

- **Remote Access**: Home Assistant-style access over a server for remote setup and management.

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Frameworks**:
  - [FastAPI](https://fastapi.tiangolo.com/) (WebSockets & API)
  - [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
- **Protocol**: [OCPP 1.6](https://github.com/mobilityhouse/ocpp)
- **Event Bus**: [pyee](https://github.com/jfhbrook/pyee) (Internal Events)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Infrastructure**: Docker, Docker Compose

## 📂 Project Structure

```text
onetime_backend/
├── app/
│   ├── gateway/            # Protocol Handling (WebSockets)
│   ├── services/           # Business Logic (Transactions, Auth)
│   ├── main.py             # Application Entrypoint
│   └── models.py           # Database Models
├── tests/                  # Integration and Unit Tests
├── docker-compose.yml      # Infrastructure
├── Makefile                # Shortcut commands
└── architecture.md         # Detailed System Design
```

## 🏁 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.10+](https://www.python.org/) (for local development/testing)
- [Make](https://www.gnu.org/software/make/) (optional, but recommended)

### Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/onetime_backend.git
    cd onetime_backend
    ```

2. **Start the infrastructure**

    ```bash
    make up
    # OR
    docker-compose up -d
    ```

3. **Check logs**

    ```bash
    docker-compose logs -f
    ```

### Running Tests

To verify the system is working correctly, run the integration tests. These simulate a Charging Station connecting to the Gateway and performing a full boot flow.

```bash
make test
# OR
python3 tests/integration/test_full_flow.py
```

## 🤝 Contributing

We welcome contributions from the community! Whether it's fixing bugs, adding new OCPP features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines

- **Code Style**: Please follow PEP 8 guidelines.
- **Testing**: Ensure you add tests for any new features. Run `make test` before submitting.
- **Documentation**: Update `architecture.md` or this `README.md` if you change architectural details.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
