.PHONY: build up down test clean setup run db

# default target
all: setup db run

setup:
	@echo "Creating virtual environment and installing dependencies..."
	uv venv
	uv pip install -r requirements.txt

db:
	@echo "Starting database..."
	docker compose up -d db
	@echo "Waiting for DB..."
	sleep 5

DATABASE_URL=postgresql://user:password@localhost:5433/onetime

generate-migration:
	@echo "Generating migration..."
	DATABASE_URL=$(DATABASE_URL) uv run alembic revision --autogenerate -m "Initial Schema"

migrate:
	@echo "Running migrations..."
	DATABASE_URL=$(DATABASE_URL) uv run alembic upgrade head

run:
	@echo "Starting local server..."
	DATABASE_URL=$(DATABASE_URL) uv run uvicorn app.main:app --reload --port 8000

test:
	@echo "Running integration test..."
	DATABASE_URL=$(DATABASE_URL) uv run python -m tests.integration.test_full_flow

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .venv

build-docker:
	docker compose build

up-docker:
	docker compose up -d
