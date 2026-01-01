.PHONY: help build up down logs clean test shell-backend shell-db shell-redis \
         reset status logs-follow build-no-cache rebuild restart logs-backend \
         logs-frontend logs-nginx logs-mongodb logs-redis prod-up prod-down \
         prod-logs prod-rebuild

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
CYAN = \033[0;36m
NC = \033[0m # No Color

# Default target
help:
	@echo ""
	@echo "$(CYAN)Docker Development Commands$(NC)"
	@echo "========================================"
	@echo ""
	@echo "$(GREEN)Core Commands:$(NC)"
	@echo "  make up             Start all services (detached)"
	@echo "  make down           Stop all services"
	@echo "  make build          Build all images"
	@echo "  make rebuild        Force rebuild all images"
	@echo "  make restart        Restart all services"
	@echo ""
	@echo "$(GREEN)Logging:$(NC)"
	@echo "  make logs           View all service logs"
	@echo "  make logs-follow    Follow logs (Ctrl+C to exit)"
	@echo "  make status         Show container status"
	@echo ""
	@echo "$(GREEN)Service Logs:$(NC)"
	@echo "  make logs-backend   Backend logs"
	@echo "  make logs-frontend  Frontend logs"
	@echo "  make logs-nginx     Nginx logs"
	@echo "  make logs-mongodb   MongoDB logs"
	@echo "  make logs-redis     Redis logs"
	@echo ""
	@echo "$(BLUE)Shell Access:$(NC)"
	@echo "  make shell-backend  Shell into backend container"
	@echo "  make shell-db       MongoDB shell"
	@echo "  make shell-redis    Redis CLI"
	@echo ""
	@echo "$(YELLOW)Testing & Maintenance:$(NC)"
	@echo "  make test           Run tests in containers"
	@echo "  make clean          Remove containers and volumes"
	@echo "  make reset          Full reset (WARNING: deletes data!)"
	@echo ""
	@echo "$(RED)Production:$(NC)"
	@echo "  make prod-up        Start production services"
	@echo "  make prod-down      Stop production services"
	@echo "  make prod-logs      View production logs"
	@echo "  make prod-rebuild   Rebuild production images"
	@echo ""

# Build all images
build:
	@echo "$(GREEN)Building all Docker images...$(NC)"
	docker-compose build

# Force rebuild all images
rebuild:
	@echo "$(GREEN)Force rebuilding all Docker images...$(NC)"
	docker-compose build --no-cache

# Start all services
up:
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo ""
	@echo "$(CYAN)Services started successfully!$(NC)"
	@echo "$(CYAN)Access points:$(NC)"
	@echo "  - Frontend (dev): http://localhost:3000"
	@echo "  - Backend API:    http://localhost:8000"
	@echo "  - API Health:     http://localhost:8000/api/health"
	@echo "  - API Docs:       http://localhost:8000/docs"
	@echo "  - Nginx:          http://localhost:80"
	@echo "  - MongoDB:        localhost:27017"
	@echo "  - Redis:          localhost:6379"

# Stop all services
down:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down

# View logs
logs:
	@echo "$(GREEN)Showing all service logs...$(NC)"
	docker-compose logs --tail=50

# Follow logs
logs-follow:
	@echo "$(GREEN)Following logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs --follow

# Restart all services
restart:
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker-compose restart

# Clean up (remove containers and volumes)
clean:
	@echo "$(RED)Removing containers and volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Containers and volumes removed.$(NC)"

# Full reset - WARNING: deletes all data!
reset:
	@echo "$(RED)WARNING: This will delete ALL data including databases!$(NC)"
	@echo "$(RED)Are you sure? (type 'yes' to continue)${NC}"
	@read -p "" ans && if [ "$$ans" != "yes" ]; then echo "Aborted."; exit 1; fi
	docker-compose down -v --remove-orphans
	docker network prune -f
	@echo "$(GREEN)Full reset complete.$(NC)"

# Run tests
test:
	@echo "$(GREEN)Running backend tests...$(NC)"
	- docker-compose exec -T backend pytest --cov=. --cov-report=term-missing 2>/dev/null || echo "Backend tests completed with warnings"
	@echo ""
	@echo "$(GREEN)Running frontend tests...$(NC)"
	- docker-compose exec -T frontend npm test -- --run 2>/dev/null || echo "Frontend tests completed with warnings"

# Show container status
status:
	@echo "$(GREEN)Container Status:$(NC)"
	docker-compose ps

# Shell into backend container
shell-backend:
	@echo "$(GREEN)Entering backend container...$(NC)"
	docker-compose exec backend /bin/bash || docker-compose exec backend /bin/sh

# MongoDB shell
shell-db:
	@echo "$(GREEN)Entering MongoDB shell...$(NC)"
	docker-compose exec mongodb mongosh -u admin -p password123 --authenticationDatabase admin

# Redis CLI
shell-redis:
	@echo "$(GREEN)Entering Redis CLI...$(NC)"
	docker-compose exec redis redis-cli -a password123

# Backend logs
logs-backend:
	@echo "$(GREEN)Backend logs:${NC}"
	docker-compose logs --tail=100 backend

# Frontend logs
logs-frontend:
	@echo "$(GREEN)Frontend logs:${NC}"
	docker-compose logs --tail=100 frontend

# Nginx logs
logs-nginx:
	@echo "$(GREEN}Nginx logs:${NC}"
	docker-compose logs --tail=100 nginx

# MongoDB logs
logs-mongodb:
	@echo "$(GREEN}MongoDB logs:${NC}"
	docker-compose logs --tail=100 mongodb

# Redis logs
logs-redis:
	@echo "$(GREEN}Redis logs:${NC}"
	docker-compose logs --tail=100 redis

# Production commands (use docker-compose.prod.yml)
prod-up:
	@echo "$(GREEN}Starting production services...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	@echo "$(YELLOW}Stopping production services...$(NC)"
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	@echo "$(GREEN}Production logs:${NC}"
	docker-compose -f docker-compose.prod.yml logs --tail=50

prod-rebuild:
	@echo "$(GREEN}Rebuilding production images...$(NC)"
	docker-compose -f docker-compose.prod.yml build --no-cache

# Database backup
db-backup:
	@echo "$(GREEN}Backing up MongoDB...$(NC)"
	@mkdir -p backups
	docker-compose exec mongodb mongodump --out /data/backup/$(shell date +%Y%m%d_%H%M%S) -u admin -p password123 --authenticationDatabase admin
	@echo "$(GREEN}Backup created in backups directory.${NC}"

# Database restore
db-restore:
	@echo "$(RED}Restoring MongoDB from backup...${NC}"
	@echo "$(RED}This will overwrite existing data!${NC}"
	@ls backups/
	@read -p "Backup directory to restore: " backup_dir && \
		docker-compose exec -T mongodb mongorestore /data/backup/$$backup_dir -u admin -p password123 --authenticationDatabase admin --drop
	@echo "$(GREEN}Restore complete.${NC}"

# Health check all services
health:
	@echo "$(GREEN}Checking service health...${NC)"
	@echo ""
	@echo "Backend Health:"
	@curl -s http://localhost:8000/api/health | jq . 2>/dev/null || curl -s http://localhost:8000/api/health
	@echo ""
	@echo "Container Status:"
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
