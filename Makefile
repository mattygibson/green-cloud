.PHONY: prod-up prod-down dev-up dev-down logs-prod logs-dev clean

# Production stack
prod-up:
	docker compose -f infra/docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f infra/docker-compose.prod.yml down

# Development stack
dev-up:
	docker compose -f infra/docker-compose.dev.yml up -d --build

dev-down:
	docker compose -f infra/docker-compose.dev.yml down

# Logs
logs-prod:
	docker compose -f infra/docker-compose.prod.yml logs -f

logs-dev:
	docker compose -f infra/docker-compose.dev.yml logs -f

# Cleanup (removes volumes too)
clean:
	docker compose -f infra/docker-compose.prod.yml down -v
	docker compose -f infra/docker-compose.dev.yml down -v
