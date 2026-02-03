# Onetime Backend (OCPP 1.6 CSMS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

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

├── pyproject.toml          # Python dependencies
└── README.md               # Project Documentation
```

## 🏁 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v2)

### Local Development Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/onetime_backend.git
    cd onetime_backend
    ```

2. **Start the Application**

    Starts the database and backend services.

    ```bash
    docker compose up -d
    ```

    The server will be available at `http://127.0.0.1:8000`.
    Migrations are applied automatically on startup.

   ### 🔌 Service Access

    Once running, you can access the different components at the following URLs:

    | Service | URL | Description |
    | :--- | :--- | :--- |
    | **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI Server & Swagger UI |
    | **Frontend** | [http://localhost:5173](http://localhost:5173) | Web Management Interface |
    | **Simulator UI** | [http://localhost:1880/ui/](http://localhost:1880/ui/) | Control the simulated charger |
    | **OCPP Logs** | [http://localhost:8888](http://localhost:8888) | View raw OCPP messages |
    | **Node-RED** | [http://localhost:1880](http://localhost:1880) | Simulator Logic Flows |
    | **Database** | `localhost:5433` | PostgreSQL (user/password) |

   ## 💻 Development Workflow

    This project is designed to be developed entirely using Docker.

   ### Backend Development

    The backend code is mounted into the container, so changes are applied automatically.

    - **Code Changes**: Edit files in `app/`, and the server will auto-reload.
    - **Logs**: View logs with `docker compose logs -f backend`.

   ### Frontend Development

    The frontend is built inside a Docker container.

    - **Code Changes**: After editing files in `frontend/`, rebuild the container to see changes:

        ```bash
        docker compose up -d --build frontend
        ```

   ### Database Migrations

    To generate a new migration after modifying `models.py`:

    ```bash
    docker compose exec backend sh -c "alembic revision --autogenerate -m 'Description of change'"
    ```

    Then restart the backend to apply it:

    ```bash
    docker compose restart backend
    ```

### Running Tests

To verify the system is working correctly, run the integration tests. These simulate a Charging Station connecting to the Gateway and performing a full boot, auth, and transaction flow.

1. Ensure the server is running (`docker compose up -d`).
2. Run the tests inside the container:

    ```bash
    docker compose exec backend python -m tests.integration.test_full_flow
    ```

## 🧪 Testing Environments

This project comes with a **pre-configured charging station simulator** to help you test different scenarios and charger behaviors.

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
- **Testing**: Run tests using `docker compose exec backend python -m tests.integration.test_full_flow`.
- **Dependencies**: Add new packages to `requirements.txt` and rebuild (`docker compose build`).

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🐳 CasaOS Deployment

This project is ready to be installed on [CasaOS](https://casaos.io/) using a custom Docker Compose file.

### One-Click Installation (App Store)

1. Open your CasaOS dashboard.
2. Click the **+** button and select **Install a Custom App**.
3. Click the import icon (top right) in the custom app window.
4. Paste the content of `casaos-compose.yml` or upload the file.
5. **Important**: Before installing, change `your_dockerhub_username` in the image fields to your actual Docker Hub username (or the username where the images are hosted).
6. Click **Install**.

### Setup for Image Publishing (GitHub Actions)

To automatically publish the latest version of the app to Docker Hub whenever you push to GitHub:

1. Go to your GitHub Repository **Settings** > **Secrets and variables** > **Actions**.
2. Create the following repository NEW secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username.
   - `DOCKER_PASSWORD`: Your Docker Hub Access Token.
3. Push your code to the `main` branch. The action will run, build the images, and push them to Docker Hub.
