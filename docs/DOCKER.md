# Docker Development Guide

This document provides comprehensive instructions for setting up and running the application using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Services](#services)
- [Development Workflow](#development-workflow)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

### Required Software

| Software | Minimum Version | Recommended Version |
|----------|-----------------|---------------------|
| Docker | 20.10.0 | 24.0+ |
| Docker Compose | 2.0.0 | 2.20+ |
| Git | 2.0 | Latest |

### Verify Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Verify Docker is running
docker ps
```

## Quick Start

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env.docker

# Edit the configuration (optional for local development)
nano .env.docker
```

### 3. Start Services

```bash
# Build and start all services
make build
make up

# Or in one command
docker-compose up -d --build
```

### 4. Verify Installation

```bash
# Check service status
make status

# Test endpoints
curl http://localhost/api/health
curl http://localhost:3000
```

### 5. Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI application |
| API Health | http://localhost/api/health | Health check endpoint |
| API Docs | http://localhost/docs | Swagger documentation |
| Redis | localhost:6379 | Redis cache |
| MongoDB | localhost:27017 | MongoDB database |

## Configuration

### Environment Variables

All configuration is managed through environment variables. Copy `.env.example` to `.env.docker` and modify:

```bash
cp .env.example .env.docker
```

#### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_INITDB_ROOT_USERNAME` | MongoDB admin username | `admin` |
| `MONGO_INITDB_ROOT_PASSWORD` | MongoDB admin password | `password123` |
| `REDIS_PASSWORD` | Redis password | `redis-password` |
| `JWT_SECRET` | JWT signing secret | (change in production!) |
| `OTP_SECRET` | OTP signing secret | (change in production!) |

#### Security Notes

⚠️ **Important for Production:**

- Change all default passwords
- Generate secure secrets: `openssl rand -base64 32`
- Never commit `.env.docker` to version control
- Use Docker secrets for sensitive data in production

### Port Configuration

| Service | Default Port | Configurable |
|---------|--------------|--------------|
| Nginx | 80, 443 | Yes (docker-compose.yml) |
| Backend | 8000 | Yes (docker-compose.yml) |
| Frontend | 3000 | Yes (docker-compose.yml) |
| MongoDB | 27017 | Yes (docker-compose.yml) |
| Redis | 6379 | Yes (docker-compose.yml) |

## Services

### Backend (FastAPI)

- **Image**: Custom Dockerfile at `backend/Dockerfile`
- **Port**: 8000
- **Health Check**: `/api/health`
- **Features**:
  - Multi-stage build for small image size
  - Non-root user for security
  - Hot reload in development
  - CORS enabled

**Access:**
```bash
# Health check
curl http://localhost:8000/api/health

# API documentation
http://localhost:8000/docs
```

### Frontend (React)

- **Image**: Custom Dockerfile at `frontend/Dockerfile`
- **Port**: 3000
- **Health Check**: `/health`
- **Features**:
  - Node.js build stage
  - Nginx production serving
  - Non-root nginx user
  - Gzip compression
  - Security headers

**Access:**
```bash
# Application
http://localhost:3000

# Health check
curl http://localhost:3000/health
```

### MongoDB

- **Image**: `mongo:7-alpine`
- **Port**: 27017
- **Health Check**: `mongosh --eval "db.adminCommand('ping')"`
- **Data Volume**: `mongodb_data`
- **Initialization**: `mongodb/init-db.js`

**Access:**
```bash
# Connect using mongosh
make shell-db

# Or with connection string
mongodb://admin:password123@localhost:27017/appdb?authSource=admin
```

### Redis

- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Health Check**: `redis-cli ping`
- **Data Volume**: `redis_data`
- **Features**: AOF persistence, password protection

**Access:**
```bash
# Connect using Redis CLI
make shell-redis

# Test connection
redis-cli -a password123 ping
```

### Nginx

- **Image**: `nginx:alpine`
- **Ports**: 80, 443
- **Health Check**: `/health`
- **Features**:
  - Reverse proxy for backend API
  - Serves frontend static files
  - Gzip compression
  - Rate limiting
  - Security headers
  - WebSocket support

## Development Workflow

### File Mounts

For development, the following directories are mounted:

| Local Path | Container Path | Purpose |
|------------|----------------|---------|
| `./backend` | `/app` | Backend code (live reload) |
| `./frontend` | `/app` | Frontend code (live reload) |

### Live Reload

Both backend and frontend support hot reloading:

**Backend:**
- Python code changes are detected by uvicorn
- Changes apply automatically

**Frontend:**
- Vite dev server watches for changes
- Browser updates automatically

### Running Tests

```bash
# Run all tests
make test

# Run backend tests only
docker-compose exec backend pytest

# Run frontend tests only
docker-compose exec frontend npm test
```

### Shell Access

```bash
# Backend shell
make shell-backend

# MongoDB shell
make shell-db

# Redis CLI
make shell-redis
```

## Production Deployment

### Building for Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml build

# Tag images with version
VERSION=1.0.0 docker-compose -f docker-compose.prod.yml build

# Push to registry
docker-compose -f docker-compose.prod.yml push
```

### Running Production

```bash
# Start production services
make prod-up

# View logs
make prod-logs

# Stop production services
make prod-down
```

### SSL/TLS Configuration

For HTTPS, add SSL certificates:

1. Create `nginx/ssl` directory:
   ```bash
   mkdir -p nginx/ssl
   ```

2. Add certificate files:
   - `nginx/ssl/cert.pem` - SSL certificate
   - `nginx/ssl/key.pem` - Private key

3. Update `nginx/nginx.conf` to include SSL configuration

### Resource Limits

Production compose file includes resource limits:

| Service | CPU Limit | Memory Limit |
|---------|-----------|--------------|
| nginx | 0.5 | 256MB |
| backend | 1.0 | 512MB |
| frontend | 0.5 | 256MB |
| mongodb | 1.0 | 1GB |
| redis | 0.5 | 512MB |

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs backend
docker-compose logs mongodb
```

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :80

# Stop conflicting service or change port in docker-compose.yml
```

### Database Connection Issues

```bash
# Verify MongoDB is running
docker-compose logs mongodb

# Test MongoDB connection
make shell-db
db.adminCommand('ping')
```

### Permission Errors

```bash
# Fix permissions for mounted directories
sudo chown -R $USER:$USER backend frontend

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Clearing Everything

```bash
# Stop all services and remove volumes
make reset

# Or manually
docker-compose down -v
docker system prune -a
```

### Viewing Logs

```bash
# All logs
make logs

# Follow mode
make logs-follow

# Specific service
make logs-backend
make logs-nginx
make logs-mongodb
make logs-redis
```

## Maintenance

### Database Backup

```bash
# Create backup
make db-backup

# Backups are stored in MongoDB container at /data/backup/
```

### Database Restore

```bash
# Restore from backup
make db-backup-restore

# ⚠️ WARNING: This will overwrite existing data!
```

### Updating Images

```bash
# Pull latest images
docker-compose pull

# Rebuild with new images
docker-compose up -d
```

### Monitoring

```bash
# View container resource usage
docker stats

# View container logs
docker-compose logs -f
```

### Health Checks

All services include health checks. Check status:

```bash
# Docker health status
docker-compose ps

# Manual health check
curl http://localhost/api/health
```

## Docker Commands Reference

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make build` | Build images |
| `make rebuild` | Force rebuild images |
| `make logs` | View logs |
| `make logs-follow` | Follow logs in real-time |
| `make clean` | Remove containers and volumes |
| `make reset` | Full reset (deletes data) |
| `make test` | Run tests |
| `make status` | Show container status |

### Direct Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Execute command in container
docker-compose exec backend python -c "print('hello')"

# Build single service
docker-compose build backend

# View resource usage
docker stats
```

## File Structure

```
.
├── docker-compose.yml          # Development configuration
├── docker-compose.prod.yml     # Production configuration
├── .env.docker                 # Environment variables (gitignored)
├── .env.example               # Environment template
├── Makefile                   # Development commands
├── nginx/
│   └── nginx.conf             # Nginx configuration
├── backend/
│   ├── Dockerfile             # Backend image build
│   ├── .dockerignore          # Backend exclusions
│   └── ...                    # Backend source code
├── frontend/
│   ├── Dockerfile             # Frontend image build
│   ├── .dockerignore          # Frontend exclusions
│   ├── nginx.conf             # Frontend nginx config
│   └── ...                    # Frontend source code
├── mongodb/
│   └── init-db.js             # Database initialization
└── docs/
    └── DOCKER.md              # This documentation
```

## Support

For issues and questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review container logs: `docker-compose logs`
3. Check service health: `docker-compose ps`
4. Open an issue in the repository
