.PHONY: build up down test clean

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

test:
	# We need to install test dependencies locally or run inside docker
	# For simplicity, assuming local run if venv is active, or use docker
	# This command runs the integration test against the running stack
	python3 tests/integration/test_full_flow.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
