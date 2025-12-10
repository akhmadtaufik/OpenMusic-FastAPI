# OpenMusic API v2 (FastAPI Edition)

A robust, asynchronous REST API for managing songs, albums, playlists, and collaborations. This project re-engineers the original Node.js/Hapi OpenMusic API into a modern Python/FastAPI application, strictly adhering to Clean Architecture principles for maintainability and scalability.

## Key Features

### Authentication & Security

- ✅ **JWT Authentication**: Secure Access and Refresh Token rotation mechanism.
- ✅ **Password Security**: Strong hashing using Bcrypt.
- ✅ **Strict Access Control**: Role-based permissions ensuring resources are protected.

### Music Data Management

- ✅ **Albums & Songs**: CRUD operations for managing music catalogs.
- ✅ **Search & Filtering**: Query parameters for filtering songs by title, performer, or year.

### Playlist Management

- ✅ **Private Playlists**: Create and manage personal playlists.
- ✅ **Playlist Songs**: Add or remove songs from playlists.
- ✅ **Activity Logging**: comprehensive history tracking of all song additions and deletions within a playlist.

### Collaboration (Phase 5)

- ✅ **Sharing Access**: Owners can add collaborators to their playlists.
- ✅ **Permission Logic**: Seamless access control allowing both Owners and Collaborators to manage playlist content.

---

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
- **Database**: [PostgreSQL](https://www.postgresql.org/) (Async via asyncpg)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Containerization**: [Docker](https://www.docker.com/) & Docker Compose
- **Testing**: [Pytest](https://docs.pytest.org/)

---

## Project Structure

This project follows a strict Clean Architecture pattern to separate concerns:

```text
.
├── app
│   ├── api         # Presentation Layer (Routes & Dependencies)
│   ├── core        # Configuration, Security, & Exceptions
│   ├── models      # Database Models (SQLAlchemy Declarative Base)
│   ├── schemas     # Data Transfer Objects (Pydantic Schemas)
│   └── services    # Business Logic Layer
├── alembic         # Database Migration Scripts
├── tests           # Integration & Unit Tests
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Prerequisites

- **Docker** & **Docker Compose** (Recommended for easiest setup)
- Python 3.11+ (Only if running locally without Docker)

---

## Installation & Running

### 1. Clone the Repository

```bash
git clone <repository-url>
cd OpenMusic-FastAPI
```

### 2. Setup Environment Variables

Create a `.env` file in the root directory with the following configuration:

| Variable                      | Description               | Example Value                    |
| :---------------------------- | :------------------------ | :------------------------------- |
| `POSTGRES_USER`               | Database User             | `postgres`                       |
| `POSTGRES_PASSWORD`           | Database Password         | `postgres`                       |
| `POSTGRES_DB`                 | Database Name             | `openmusicv2`                    |
| `POSTGRES_HOST`               | Database Host             | `db` (for Docker) or `localhost` |
| `POSTGRES_PORT`               | Database Port             | `5432`                           |
| `ACCESS_TOKEN_KEY`            | Secret for Access Tokens  | `your-secret-key`                |
| `REFRESH_TOKEN_KEY`           | Secret for Refresh Tokens | `your-refresh-secret-key`        |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token Lifespan            | `30`                             |

### 3. Run with Docker Compose

Build and start the services in detached mode:

```bash
docker compose up -d --build
```

### 4. Run Database Migrations

Apply the database schema:

```bash
docker compose exec app alembic upgrade head
```

The API should now be running at `http://localhost:8001`.

---

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

## Testing

To run the integration tests inside the Docker container:

```bash
docker compose exec app pytest
```
