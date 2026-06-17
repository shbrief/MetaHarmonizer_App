# MetaHarmonizer — dev shortcuts.
# Usage: make <target>   (Windows: use `make` via Git Bash/WSL, or run the
# docker compose commands directly — each target shows its command.)

COMPOSE := docker compose

.PHONY: help up down restart logs ps build api-shell db-shell migrate test fmt env

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if missing
	@test -f .env || (cp .env.example .env && echo "created .env from .env.example")

up: env ## Build + start the full stack (postgres, redis, api, worker, caddy)
	$(COMPOSE) up --build -d
	@echo "API:   http://localhost:8000/healthz"
	@echo "Caddy: http://localhost:8080/healthz"

down: ## Stop the stack (keeps volumes)
	$(COMPOSE) down

clean: ## Stop the stack and delete volumes (DB + redis + engine cache)
	$(COMPOSE) down -v

restart: ## Restart the api service
	$(COMPOSE) restart api

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

build: ## Rebuild images without starting
	$(COMPOSE) build

api-shell: ## Shell into the api container
	$(COMPOSE) exec api bash

db-shell: ## psql into Postgres
	$(COMPOSE) exec postgres psql -U mh -d metaharmonizer

migrate: ## Run Alembic migrations (available from Sprint 2)
	$(COMPOSE) exec api alembic upgrade head

test: ## Run backend tests against the mock engine
	$(COMPOSE) exec -e ENGINE_IMPL=mock api pytest -q
