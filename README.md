# OpenMusic API (FastAPI Edition)

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat-square&logo=docker)
![Coverage](https://img.shields.io/badge/Tests-Passing-success?style=flat-square)

**OpenMusic API** is a high-performance, asynchronous RESTful API designed for managing music libraries, playlists, and user collaborations. This version introduces enterprise-grade features including server-side caching, queue-based asynchronous exports, and S3-compatible object storage.

---

## 🏗️ Architecture Overview

The system utilizes a modern, event-driven microservices architecture. It decouples the core API from heavy background tasks (like emailing) using a message broker, ensuring high responsiveness.

```mermaid
graph LR
    User[User / Client] -->|HTTP Requests| API[FastAPI App]
    
    subgraph Infrastructure
        API <-->|Read/Write| DB[(PostgreSQL)]
        API <-->|Cache Hit/Miss| Redis[(Redis Cache)]
        API -->|Upload Images| MinIO[(MinIO Storage)]
        API -->|Publish Event| MQ[(RabbitMQ)]
    end
    
    subgraph Worker
        MQ -->|Consume| Consumer[Consumer Worker]
        Consumer -->|Fetch Data| DB
        Consumer -->|Send Email| SMTP[SMTP Server]
    end
```

---

## 🚀 Key Features

### Core Capabilities

* **Music Management**: Complete CRUD operations for Albums and Songs.
* **Authentication**: Secure JWT-based authentication (Access & Refresh Tokens).
* **Playlists**: Create playlists and manage songs within them.
* **Collaborations**: Fine-grained access control allowing owners to share playlists with collaborators.

### Advanced Features

* **Server-Side Caching**: Implemented **Redis** caching for the "Get Album Likes" feature to reduce database load and improve response times. Uses a Cache-Aside pattern with TTL.
* **Object Storage**: Integrated **MinIO** (S3-compatible) for handling Album Cover uploads securely.
* **Asynchronous Export**: Decoupled "Export Playlist" feature using **RabbitMQ**. The API acts as a **Producer**, while a separate **Consumer** worker handles data fetching and email delivery.

---

## 🛠️ Tech Stack & Infrastructure

* **Language**: Python 3.11
* **Framework**: FastAPI (Async)
* **Database**: PostgreSQL (Asyncpg driver)
* **ORM**: SQLAlchemy 2.0 (Async)
* **Cache**: Redis
* **Message Broker**: RabbitMQ
* **Storage**: MinIO
* **Orchestration**: Docker Compose

### Docker Services

| Service    | Description                                     |
| :--------- | :---------------------------------------------- |
| `app`      | The main REST API application.                  |
| `consumer` | Background worker that processes export tasks.  |
| `db`       | PostgreSQL database instance.                   |
| `redis`    | In-memory cache store.                          |
| `rabbitmq` | Message broker for checking and routing events. |
| `minio`    | S3-compatible object storage for files.         |

---

## 📋 Prerequisites

* **Docker Desktop** (or Docker Engine + Compose plugin) installed.
* *(Optional)* **Python 3.11+** for local development/testing outside containers.

---

## ⚙️ Installation & Configuration

Follow these steps to get the system running locally.

### 1. Clone Repository

```bash
git clone <repository-url>
cd OpenMusic-FastAPI
```

### 2. Environment Setup

Create a `.env` file in the root directory. Configure the following variables:

| Category     | Variable                      | Description                    | Example Value                     |
| :----------- | :---------------------------- | :----------------------------- | :-------------------------------- |
| **App**      | `ACCESS_TOKEN_KEY`            | Secret for signing JWTs        | `secret_access_key`               |
|              | `REFRESH_TOKEN_KEY`           | Secret for refresh tokens      | `secret_refresh_key`              |
|              | `ACCESS_TOKEN_EXPIRE_MINUTES` | Token validity duration        | `30`                              |
| **Postgres** | `POSTGRES_USER`               | DB Username                    | `openmusic`                       |
|              | `POSTGRES_PASSWORD`           | DB Password                    | `openmusic`                       |
|              | `POSTGRES_DB`                 | Database Name                  | `openmusic`                       |
|              | `POSTGRES_SERVER`             | Service Hostname               | `db`                              |
|              | `POSTGRES_PORT`               | Port                           | `5432`                            |
| **Redis**    | `REDIS_HOST`                  | Redis Hostname                 | `redis`                           |
|              | `REDIS_PORT`                  | Redis Port                     | `6379`                            |
| **RabbitMQ** | `RABBITMQ_SERVER`             | AMQP Connection String         | `amqp://user:pass@rabbitmq:5672/` |
|              | `RABBITMQ_USERNAME`           | Username                       | `user`                            |
|              | `RABBITMQ_PASSWORD`           | Password                       | `password`                        |
|              | `RABBITMQ_ERLANG_COOKIE`      | **CRITICAL** Clustering Secret | `secret_cookie_placeholder`       |
| **MinIO**    | `MINIO_ENDPOINT`              | MinIO Hostname                 | `minio:9000`                      |
|              | `MINIO_ROOT_USER`             | Admin User                     | `minioadmin`                      |
|              | `MINIO_ROOT_PASSWORD`         | Admin Password                 | `minioadmin123`                   |
|              | `MINIO_BUCKET_NAME`           | Bucket for uploads             | `openmusic`                       |
| **SMTP**     | `SMTP_HOST`                   | SMTP Server (e.g. Mailtrap)    | `sandbox.smtp.mailtrap.io`        |
|              | `SMTP_PORT`                   | SMTP Port                      | `2525`                            |
|              | `SMTP_USER`                   | SMTP Username                  | `your_user`                       |
|              | `SMTP_PASSWORD`               | SMTP Password                  | `your_pass`                       |
| **Email**    | `MAIL_FROM`                   | Sender Address for emails      | `noreply@openmusicapp.com`        |

> **Note**: `RABBITMQ_ERLANG_COOKIE` is required for the RabbitMQ container to initialize correctly. If you encounter permission errors, you may need to clear volumes.

### 3. Run with Docker

Start all services (App, DB, Broker, Worker, Storage):

```bash
docker compose up -d --build
```

**Apply Database Migrations:**
Ensure the database schema is up to date:

```bash
docker compose exec app alembic upgrade head
```

> **Troubleshooting**: If RabbitMQ fails to start due to cookie mismatch, run `docker compose down -v` to clear volumes and restart.

---

## 🖥️ Access Points

Once running, you can access the following services:

| Service                 | Access URL                                               | Credentials (if applicable)           |
| :---------------------- | :------------------------------------------------------- | :------------------------------------ |
| **API Documentation**   | [http://localhost:8001/docs](http://localhost:8001/docs) | -                                     |
| **RabbitMQ Management** | [http://localhost:15672](http://localhost:15672)         | Env: `RABBITMQ_USERNAME` / `PASSWORD` |
| **MinIO Console**       | [http://localhost:9001](http://localhost:9001)           | Env: `MINIO_ROOT_USER` / `PASSWORD`   |

---

## 🧪 Testing

We have a comprehensive test suite covering Unit and Integration tests. To run the tests inside the container:

```bash
docker compose exec app pytest -v
```

To run specific integration tests for the Export/Consumer feature:

```bash
docker compose exec app pytest tests/integration/test_exports_and_consumer.py -v
```

---

## 📂 Project Structure

```text
.
├── app
│   ├── api              # API Routes (v1)
│   ├── core             # Config, Security, Database
│   ├── models           # SQLAlchemy ORM Models
│   ├── schemas          # Pydantic Schemas
│   ├── services         # Business Logic (Producer, Mail, Storage, etc.)
│   ├── consumer.py      # Background Worker Entrypoint
│   └── main.py          # App Entrypoint
├── tests
│   ├── integration      # Integration Tests
│   └── conftest.py      # Pytest Fixtures
├── docker-compose.yml   # Infrastructure Definition
├── Dockerfile           # App Container Definition
└── requirements.txt     # Python Dependencies
```
