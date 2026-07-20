.PHONY: prod-up prod-down dev-up dev-down infra-up infra-down logs-prod logs-dev logs-infra build-push clean

# Infrastructure (registry, monitoring — always running)
infra-up:
	docker compose -f infra/docker-compose.infra.yml up -d

infra-down:
	docker compose -f infra/docker-compose.infra.yml down

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

# Build and push to local registry
build-push:
	bash scripts/build-and-push.sh $(TAG) $(PLATFORM)

# Logs
logs-prod:
	docker compose -f infra/docker-compose.prod.yml logs -f

logs-dev:
	docker compose -f infra/docker-compose.dev.yml logs -f

logs-infra:
	docker compose -f infra/docker-compose.infra.yml logs -f

# Cleanup (removes volumes too)
clean:
	docker compose -f infra/docker-compose.prod.yml down -v
	docker compose -f infra/docker-compose.dev.yml down -v
	docker compose -f infra/docker-compose.infra.yml down -v
