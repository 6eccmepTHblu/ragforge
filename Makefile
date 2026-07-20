.PHONY: install install-dev run demo seed-ui test lint format docker-build docker-run

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev,openai,anthropic,chroma,pdf]"

run:
	uvicorn app.main:app --reload --port 8000

demo:
	python -m scripts.demo

seed-ui:
	python -m scripts.seed_ui_data

test:
	pytest

lint:
	ruff check app tests

format:
	ruff format app tests

docker-build:
	docker build -t ragforge:latest .

docker-run:
	docker run --rm -p 8000:8000 ragforge:latest
