SHELL := /bin/bash

.DEFAULT_GOAL := help

COMPOSE := docker compose -f infra/docker-compose.yml
COMPOSE_DEV := $(COMPOSE) -f infra/docker-compose.dev.yml

.PHONY: help up down logs ps build rebuild seed test lint format demo tag clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	     /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

up: ## Start the full stack in the background (production-shaped compose)
	$(COMPOSE) up -d --build

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

test: ## Run the full backend + frontend test suite
	$(COMPOSE) run --rm auth-service pytest

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

clean: ## Remove build artefacts, volumes, and dangling images
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f
