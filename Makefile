.PHONY: dev prod build build-frontend logs shell clean restart setup

# ── Development ──

## Start all services in dev mode (with hot-reload)
dev:
	docker compose up --build

## Start dev mode in background
dev-d:
	docker compose up --build -d

## Start core services only (no n8n)
dev-core:
	docker compose up --build app mysql frontend

## Start backend + DB only (for frontend dev on host machine)
dev-backend:
	docker compose up --build app mysql

## Rebuild and start a specific service (e.g., make rebuild s=frontend)
rebuild:
	docker compose up --build $(s)

## View development logs
logs:
	docker compose logs -f

## View logs for a specific service
logs-svc:
	docker compose logs -f $(s)

# ── Production ──

## Start full production stack
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

## Start production with n8n
prod-n8n:
	docker compose --profile n8n -f docker-compose.yml -f docker-compose.prod.yml up --build -d

## Stop production stack
prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

## View production logs
prod-logs:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# ── Build ──

## Build all images
build:
	docker compose build

## Build production images
build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

## Build frontend image only (dev)
build-frontend:
	docker compose build frontend

## Build frontend production image
build-frontend-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build frontend

# ── Maintenance ──

## Stop and remove containers
down:
	docker compose down

## Stop, remove containers + volumes
down-v:
	docker compose down -v

## Reset everything (clean rebuild)
reset: down-v
	docker compose build --no-cache

## Clean Docker system (prune unused)
clean:
	docker system prune -f
	docker volume prune -f

## Restart all services
restart: down
	docker compose up --build -d

# ── Shell ──

## Open shell in backend container
shell:
	docker compose exec app sh

## Open shell in frontend container
shell-frontend:
	docker compose exec frontend sh

## Open MySQL CLI
mysql:
	docker compose exec mysql mysql -u app -p${DB_PASSWORD} text_to_sql

# ── Info ──

## Show running services
ps:
	docker compose ps

## Show service URLs
urls:
	@echo "=== Service URLs ==="
	@echo "Frontend:   http://localhost:3000"
	@echo "API:        http://localhost:8000"
	@echo "Health:     http://localhost:8000/health"
	@echo "MySQL:      localhost:3306"
	@echo "n8n:        http://localhost:5678  (run: make dev --profile n8n)"
	@echo ""
	@echo "=== Dev Credentials ==="
	@echo "Admin:      admin / admin123"
