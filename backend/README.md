# AI Study Backend

FastAPI backend service for AI Study Platform.

## Features

- FastAPI web framework
- PostgreSQL database with SQLAlchemy ORM
- Alembic database migrations
- JWT authentication
- AI service integration
- Automatic dependency management with uv

## Development

### Prerequisites

- Python 3.11+
- uv package manager
- PostgreSQL database

### Installation

```bash
# Install dependencies
uv sync --dev

# Run the application
uv run uvicorn main:app --reload
```

### Database Migration

See [README_MIGRATION.md](README_MIGRATION.md) for detailed migration instructions.

### Code Quality

```bash
# Run linting
uv run ruff check .

# Run type checking
uv run pylint app/

# Run tests
uv run pytest
```