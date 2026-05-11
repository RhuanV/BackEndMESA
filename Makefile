# GeoAvia — MESA-Auto Framework
# ================================

.PHONY: start stop frontend backend logs clean

## Start entire project (Docker + Frontend)
start:
	@bash start.sh

## Stop all services
stop:
	@docker compose down
	@echo "✓ All services stopped"

## Start frontend only (Vite dev server)
frontend:
	@cd frontend && npm run dev

## Start backend only (Docker)
backend:
	@docker compose up --build -d
	@echo "✓ Docker services started"

## View backend logs
logs:
	@docker compose logs -f backend

## Clean build artifacts
clean:
	@rm -rf frontend/dist frontend/node_modules/.vite
	@echo "✓ Build artifacts cleaned"
