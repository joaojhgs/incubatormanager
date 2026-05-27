SHELL := /bin/bash

.DEFAULT_GOAL := help

COMPOSE_ENV_FILE := $(if $(wildcard .env),.env,.env.example)
# The apparmor layer skips the daemon's docker-default profile check on hosts that
# cannot read /sys/kernel/security/apparmor/profiles (see that file's header). It is a
# no-op where AppArmor works normally, so it is safe in the base COMPOSE invocation.
COMPOSE := docker compose --env-file $(COMPOSE_ENV_FILE) --project-directory . -f infra/docker-compose.yml -f infra/docker-compose.apparmor.yml
COMPOSE_DEV := $(COMPOSE) -f infra/docker-compose.dev.yml
BACKEND_SERVICES := auth-service company-service contract-service finance-service space-service booking-service inventory-service ticket-service dashboard-service document-service
CRON_FILES := infra/cron/booking.crontab infra/cron/contract.crontab infra/cron/finance.crontab

.PHONY: help up up-dev down logs ps build rebuild seed test test-backend test-backend-host test-libs lint format local-gate local-gate-host demo tag env clean

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

seed: ## Load deterministic local demo users and smoke fixtures
	$(COMPOSE) exec auth-service python manage.py seed_dev_users
	$(COMPOSE) exec auth-service python /app/infra/seed/seed.py

test: ## Run pytest in the auth-service container (requires `make up` or images built)
	$(COMPOSE) run --rm auth-service pytest

test-backend: ## Run pytest in every backend service container
	@for service in $(BACKEND_SERVICES); do \
		echo "==> pytest $$service"; \
		$(COMPOSE) run --rm $$service pytest; \
	done

test-backend-host: ## Run backend pytest and migration checks locally without Docker
	@for service in $(BACKEND_SERVICES); do \
		echo "==> local pytest $$service"; \
		(cd services/$$service && python3 manage.py makemigrations --check --dry-run && python3 -m pytest -q); \
	done

test-libs: ## Run shared Python library unit tests
	python3 -m pip install -q -e "libs/py-common[dev]" \
		|| python3 -m pip install -q --break-system-packages -e "libs/py-common[dev]"
	cd libs/py-common && python3 -m pytest

lint: ## Run ruff, eslint, and prettier across the monorepo
	ruff check .
	npm run lint
	npm run format:check

local-gate: ## Validate compose, scheduler crontabs, shared libs, and backend tests
	$(COMPOSE) config --quiet
	python3 -m py_compile infra/scripts/cron-runner.py
	@for file in $(CRON_FILES); do \
		echo "==> validating $$file"; \
		python3 infra/scripts/cron-runner.py --dry-run $$file >/dev/null; \
	done
	python3 -m pytest infra/tests
	$(MAKE) test-libs
	$(MAKE) test-backend

local-gate-host: ## Run non-Docker lint, frontend checks, cron validation, libs, and backend pytest
	ruff check .
	npm run lint
	npm run format:check
	npm --prefix frontend run typecheck
	npm --prefix frontend test
	npm --prefix frontend run build
	python3 -m py_compile infra/scripts/cron-runner.py
	@for file in $(CRON_FILES); do \
		echo "==> validating $$file"; \
		python3 infra/scripts/cron-runner.py --dry-run $$file >/dev/null; \
	done
	python3 -m pytest infra/tests
	$(MAKE) test-libs
	$(MAKE) test-backend-host

format: ## Apply ruff and prettier formatters
	ruff format .
	npm run format

demo: ## Reset DBs, seed, and run the stack in the foreground
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build --wait
	$(MAKE) seed
	$(COMPOSE) logs -f

tag: ## Tag a release commit and push tags to origin
	@git tag -a "v$$(date +%Y.%m.%d)" -m "release $$(date +%Y-%m-%d)"
	@git push origin --tags

env: ## Generate .env from .env.example with random secrets (use -f to overwrite)
	@bash scripts/generate-env.sh -f

clean: ## Remove build artefacts, volumes, and dangling images
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f
