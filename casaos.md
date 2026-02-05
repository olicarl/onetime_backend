# CasaOS Installation Guide

This guide details the specific settings required when installing the **OneTime** application on CasaOS, whether via "Custom App" or manual configuration.

## 📦 General Settings

* **App Name**: `onetime`
* **Docker Image**: `your_dockerhub_username/onetime-frontend:latest` (This is the main icon/entry point)
  * *Note: CasaOS usually focuses on one main container for the UI, but this project uses multi-container Compose. The best way is to Import the YAML.*
* **Default Credentials**:
  * **Username**: `admin`
  * **Password**: `admin`

## 🐳 Docker Compose Import (Recommended)

1. Click **+** -> **Install a Custom App**.
2. Click the **Import** icon (top right).
3. Upload or Paste the content of `casaos-compose.yml`.
4. **Action Required**: Change `your_dockerhub_username` to your actual Docker Hub username in the image fields.

## 🛠 Manual Configuration Details

If you need to verify or manually change settings, here are the correct mappings:

### 1. Frontend (The Web UI)

This is the main entry point you will see on the dashboard.

* **Container Name**: `frontend`
* **Image**: `your_dockerhub_username/onetime-frontend:latest`
* **Network**: `bridge`
* **Ports**:
  * **Host Port**: `8080` (or any free port like 8090)
  * **Container Port**: `80`
  * **Protocol**: `TCP`
* **Web UI Address**: `http://<IP>:8080`

### 2. Backend (The API)

Did not necessarily need to be exposed, but useful for debugging or external API access.

* **Container Name**: `backend`
* **Image**: `your_dockerhub_username/onetime-backend:latest`
* **Ports**:
  * **Host Port**: `8000`
  * **Container Port**: `8000`
* **Environment Variables**:
  * `DATABASE_URL`: `postgresql://user:password@db/onetime`
* **Links** (Critical for Raspberry Pi):
  * `db:db`

### 3. Database (Postgres)

Stores all your data.

* **Container Name**: `db`
* **Image**: `postgres:15`
* **Ports**:
  * **Host Port**: `5433` (Use a non-standard port like 5433 to avoid conflicts)
  * **Container Port**: `5432`
* **Volumes (Mounts)**:
  * **Host Path**: `/DATA/AppData/onetime/postgres`
  * **Container Path**: `/var/lib/postgresql/data`
* **Environment Variables**:
  * `POSTGRES_USER`: `user`
  * `POSTGRES_PASSWORD`: `password`
  * `POSTGRES_DB`: `onetime`

## ⚠️ Important Notes

* **DNS Issues**: On some devices (like Raspberry Pi), Docker DNS fails. We use `links: - db:db` in the backend config to fix this.
* **Data Persistence**: Your data is saved in `/DATA/AppData/onetime/postgres`. Back up this folder if you want to save your database.
