# Makefile for GeoDataHub

.PHONY: help install install-dev install-api test clean format lint run-api run-examples

help:
	@echo "GeoDataHub - Available commands:"
	@echo ""
	@echo "  make install        Install package"
	@echo "  make install-dev    Install package with dev dependencies"
	@echo "  make install-api    Install package with API dependencies"
	@echo "  make test           Run tests"
	@echo "  make format         Format code with black"
	@echo "  make lint           Lint code with flake8"
	@echo "  make clean          Remove build artifacts"
	@echo "  make run-api        Start the API server"
	@echo "  make run-examples   Run example scripts"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

install-api:
	pip install -e .[api]

install-all:
	pip install -e .[api,cli,dev]

test:
	pytest tests/ -v

format:
	black geodatahub/ geodatahub_api/ cli.py examples/

lint:
	flake8 geodatahub/ geodatahub_api/ cli.py --max-line-length=120

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf **/__pycache__
	rm -rf **/*.pyc
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/

run-api:
	uvicorn geodatahub_api.main:app --reload --host 0.0.0.0 --port 8000

run-examples:
	python examples/basic_usage.py

setup-dev:
	python -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  source venv/bin/activate  (Linux/Mac)"
	@echo "  venv\\Scripts\\activate     (Windows)"
	@echo "Then run: make install-all"

docs:
	@echo "Documentation generation not yet implemented"

.DEFAULT_GOAL := help
