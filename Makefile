.PHONY: build up down test clean setup run db

# default target
all: setup db run

setup:
	@echo "Installing dependencies with uv..."
	uv pip install -r requirements.txt

db:
	@echo "Starting database..."
	docker-compose up -d db
	@echo "Waiting for DB..."
	sleep 5

migrate:
	@echo "Running migrations..."
	uv run alembic upgrade head

run:
	@echo "Starting local server..."
	uv run uvicorn app.main:app --reload --port 8000

test:
	@echo "Running integration test..."
	uv run python tests/integration/test_full_flow.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .venv

build-docker:
	docker-compose build

up-docker:
	docker-compose up -d
