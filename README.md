# Onetime Backend (OCPP 1.6 CSMS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

A scalable, modular backend for an EV Charging Station Management System (CSMS) built with the **Gateway Pattern**. This project implements the **OCPP 1.6 JSON** protocol, separating protocol handling from business logic to ensure high performance and maintainability.

## 🚀 Features

- **OCPP 1.6 JSON Support**: Full WebSocket handling using `mobilityhouse/ocpp`.
- **Gateway Pattern**:
  - **Gateway Service**: Stateless (mostly), handles WebSockets, translates OCPP to internal RPC/Events.
  - **CMS Service**: Pure business logic, handles database interactions.
- **Event-Driven Architecture**: Uses **RabbitMQ** for async communication and **Nameko** for RPC.
- **Dockerized**: Complete stack (Gateway, CMS, RabbitMQ, Postgres) ready to run with Docker Compose.
- **Extensible**: Designed to be easily extended with new OCPP handlers and business rules.

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Frameworks**:
  - [FastAPI](https://fastapi.tiangolo.com/) (Gateway)
  - [Nameko](https://nameko.readthedocs.io/) (Microservices/RPC)
- **Protocol**: [OCPP 1.6](https://github.com/mobilityhouse/ocpp)
- **Message Broker**: [RabbitMQ](https://www.rabbitmq.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Infrastructure**: Docker, Docker Compose

## 📂 Project Structure

```
onetime_backend/
├── gateway/                # FastAPI Gateway Service
│   ├── handlers/           # OCPP Message Handlers
│   ├── routers/            # HTTP Routes
│   └── main.py             # Entrypoint
├── services/
│   └── cms/                # Nameko CMS Service (Business Logic)
├── tests/                  # Integration and Unit Tests
├── docker-compose.yml      # Container Orchestration
├── Makefile                # Shortcut commands
└── BOILERPLATE_GUIDE.md    # Detailed Implementation Guide
```

## 🏁 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.10+](https://www.python.org/) (for local development/testing)
- [Make](https://www.gnu.org/software/make/) (optional, but recommended)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/onetime_backend.git
    cd onetime_backend
    ```

2.  **Start the infrastructure**
    ```bash
    make up
    # OR
    docker-compose up -d
    ```

3.  **Check logs**
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

1.  **Fork the Project**
2.  **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3.  **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4.  **Push to the Branch** (`git push origin feature/AmazingFeature`)
5.  **Open a Pull Request**

### Development Guidelines

- **Code Style**: Please follow PEP 8 guidelines.
- **Testing**: Ensure you add tests for any new features. Run `make test` before submitting.
- **Documentation**: Update `BOILERPLATE_GUIDE.md` or this `README.md` if you change architectural details.

### Roadmap

See [BOILERPLATE_GUIDE.md](BOILERPLATE_GUIDE.md) for a detailed roadmap of what's implemented and what's next (e.g., Database integration, Authorization, Remote Commands).

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
