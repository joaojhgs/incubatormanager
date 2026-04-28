SHELL := /bin/bash

.DEFAULT_GOAL := help

COMPOSE := docker compose --project-directory . -f infra/docker-compose.yml
COMPOSE_DEV := $(COMPOSE) -f infra/docker-compose.dev.yml

.PHONY: help up up-dev down logs ps build rebuild seed test test-libs lint format demo tag env clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	     /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

up: ## Start the full stack in the background (production-shaped compose)
	$(COMPOSE) up -d --build

up-dev: ## Start stack with dev overrides (bind mounts + watchfiles + Django runserver)
	$(COMPOSE_DEV) up -d --build

down: ## Stop the stack and remove containers
	$(COMPOSE) down

logs: ## Tail logs from every service
	$(COMPOSE) logs -f --tail=100

ps: ## Show the status of every service
	$(COMPOSE) ps

build: ## Build all service images
	$(COMPOSE) build

rebuild: ## Force a clean rebuild of every service
	$(COMPOSE) build --no-cache

seed: ## Load 10-of-everything fixtures into each service DB
	$(COMPOSE) exec auth-service python /app/infra/seed/seed.py

test: ## Run pytest in the auth-service container (requires `make up` or images built)
	$(COMPOSE) run --rm auth-service pytest

test-libs: ## Run shared Python library unit tests
	python3 -m pip install -q -e "libs/py-common[dev]" \
		|| python3 -m pip install -q --break-system-packages -e "libs/py-common[dev]"
	cd libs/py-common && python3 -m pytest

lint: ## Run ruff, eslint, and prettier across the monorepo
	ruff check .
	npm run lint
	npm run format:check

format: ## Apply ruff and prettier formatters
	ruff format .
	npm run format

demo: ## Reset DBs, seed, and run the stack in the foreground
	$(COMPOSE) down -v
	$(COMPOSE) up --build

tag: ## Tag a release commit and push tags to origin
	@git tag -a "v$$(date +%Y.%m.%d)" -m "release $$(date +%Y-%m-%d)"
	@git push origin --tags

env: ## Generate .env from .env.example with random secrets (use -f to overwrite)
	@bash scripts/generate-env.sh -f

clean: ## Remove build artefacts, volumes, and dangling images
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f
