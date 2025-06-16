## Prerequisites

Before you begin, ensure you have the following installed:

- Python (>=3.12,<4.0 as specified in `pyproject.toml`)
- Poetry (for dependency management)
- Docker and Docker Compose (for running the PostgreSQL database)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yarqui/pythonweb-10.git
cd pythonweb-12
```

### 2. Set Up Python Environment

This project uses Poetry to manage dependencies.

Install the project dependencies:

```bash
poetry install
```

This will create a virtual environment and install all necessary packages listed in `pyproject.toml`.

## Database Setup

### Using Docker Compose

The project uses a PostgreSQL database, which can be easily run using Docker Compose. The configuration is defined in `docker-compose.yml`.

1.  **Start the database container:**

    ```bash
    docker-compose up -d
    ```

    This command will pull the `postgres:16` image (if not already present) and start the database service in detached mode.
    The database will be accessible on `localhost:5432` with the following credentials (as defined in `docker-compose.yml` and `src/conf/config.py`):

    - **User:** `postgres`
    - **Password:** `finalpassword`
    - **Database Name:** `contactapp-db`

2.  **To stop the database container:**

    ```bash
    docker-compose down
    ```

    To stop and remove the volume (deleting all data):

    ```bash
    docker-compose down -v
    ```

## Database Migrations

### Using Alembic

Database schema migrations are managed by Alembic. The migration scripts are located in the `alembic/versions` directory.

To apply the latest migrations to your database:

```bash
poetry run alembic upgrade head
```

Ensure your database container is running before executing this command.

## Running the Application

To run the FastAPI application, use Uvicorn.

```bash
poetry run fastapi dev main.py
```

**Note:** The application documentation will be available at `http://127.0.0.1:8000/docs`.
