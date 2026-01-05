# Onetime Backend (OCPP 1.6 CSMS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/managed%20by-uv-purple)](https://github.com/astral-sh/uv)
[![Docker](https://img.shields.io/badge/docker%20compose-v2-blue.svg)](https://docs.docker.com/compose/)

A scalable, modular backend for an EV Charging Station Management System (CSMS) built with a **Simplified Monolithic Architecture**. This project implements the **OCPP 1.6 JSON** protocol, designed for reliability and ease of deployment.

## 🎯 Purpose

The goal of this project is to provide a **Home Assistant-style backend** for multi-family home parking lots where many charging stations are installed. It is designed to run on any Linux computer (e.g., Raspberry Pi) and focuses on simplicity, low resource usage, and ease of maintenance.

**Key Advantages:**

- **Offline Capability**: Not reliant on a stable internet connection for authentication or charging sessions.
- **Cost-Effective**: No recurring costs; one-time hardware cost (e.g., Raspberry Pi).
- **Easy Setup**: Simple one-time setup process.
- **Simplified Security**: Operated behind a router, removing the need for complex security configurations.
- **High Stability**: Optimized for typical installations of fewer than 200 charging points.
- **Billing Integration**: Server can send invoices directly to tenants or forward 15-minute energy consumption intervals to ZEV billing solutions.

**Target Audience:**

- **Electricians & Installers**: Designed to be installed and commissioned by professionals without deep IT knowledge.

## 🚀 Features

- **OCPP 1.6 JSON Support**: Full WebSocket handling using `mobilityhouse/ocpp`.
- **Monolithic Architecture**:
  - **Single Process**: Runs as a single, lightweight FastAPI application.
  - **In-Memory Event Bus**: Decoupled internal communication using `pyee`.
- **Modern Tooling**:
  - **Dependency Management**: Uses `uv` for ultra-fast package management.
  - **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations.
- **Simplicity**: No RabbitMQ or microservices overhead. Just Docker + Postgres.
- **Extensible**: Modular logic layer for adding new features easily.

### Future Features

- **Remote Access**: Home Assistant-style access for remote setup and management.

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **Frameworks**:
  - [FastAPI](https://fastapi.tiangolo.com/) (WebSockets & API)
  - [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
  - [Alembic](https://alembic.sqlalchemy.org/) (Migrations)
- **Protocol**: [OCPP 1.6](https://github.com/mobilityhouse/ocpp)
- **Event Bus**: [pyee](https://github.com/jfhbrook/pyee)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Infrastructure**: Docker, Docker Compose (v2)
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

## 📂 Project Structure

```text
onetime_backend/
├── app/
│   ├── gateway/            # Protocol Handling (WebSockets & Handlers)
│   ├── services/           # Business Logic (Station, Auth, Transaction)
│   ├── main.py             # Application Entrypoint
│   ├── models.py           # Database Models
│   └── database.py         # DB Connection & Session
├── alembic/                # Database Migrations
├── tests/                  # Integration and Unit Tests
├── docker-compose.yml      # Infrastructure (PostgreSQL)
├── Makefile                # Shortcut commands for local dev
├── pyproject.toml          # Python dependencies
└── README.md               # Project Documentation
```

## 🏁 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v2)
- [uv](https://github.com/astral-sh/uv) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Local Development Setup

We use `make` and `uv` to streamline the development workflow.

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/onetime_backend.git
    cd onetime_backend
    ```

2. **Setup Environment**

    Creates a virtual environment and installs dependencies.

    ```bash
    make setup
    ```

3. **Start Database**

    Starts the PostgreSQL container on port **5433** (to avoid conflicts).

    ```bash
    make db
    ```

4. **Run Migrations**

    Applies the database schema.

    ```bash
    make migrate
    ```

    *Tip: To create a new migration after changing models, use `make generate-migration`.*

5. **Run the Server**

    Starts the FastAPI backend locally with hot-reload.

    ```bash
    make run
    ```

    The server will be available at `http://127.0.0.1:8000`.

### Running Tests

To verify the system is working correctly, run the integration tests. These simulate a Charging Station connecting to the Gateway and performing a full boot, auth, and transaction flow.

1. Ensure the server is running (`make run`) in one terminal.
2. In a separate terminal, run:

    ```bash
    make test
    ```

## 🧪 Testing Environments

This project relies on the **EVerest Simulator** for testing charging scenarios and behaviors.

### EVerest Simulator (Advanced)

A full-featured, industry-standard simulator by LF Energy. It provides deep inspection capabilities and simulates realistic hardware behaviors.

- **Simulator UI**: [http://localhost:1880/ui/](http://localhost:1880/ui/) (Control the charger)
- **OCPP Logs**: [http://localhost:8888](http://localhost:8888) (Visualize raw OCPP messages)
- **Node-RED**: [http://localhost:1880](http://localhost:1880) (Logic flows)

**How to Use:**

1. Open the **Simulator UI**.
2. Use the toggles to simulate plugging in a cable (`Plug In`).
3. Watch the **OCPP Logs** validation in real-time on port 8888.

---

## 🤝 Contributing

We welcome contributions!

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines

- **Code Style**: Follow PEP 8.
- **Testing**: Run `make test` before submitting.
- **Dependencies**: Add new packages using `uv add <package>` and update `requirements.txt` if needed.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
