# JobOps - Docker Setup Guide

Complete Docker configuration guide for JobOps Internal Operations Management System.

## 📦 Docker Services

The project uses **6 Docker containers**:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **db** | postgres:15-alpine | 5432 | PostgreSQL database |
| **rabbitmq** | rabbitmq:3.12-management | 5672, 15672 | Message broker for Celery |
| **redis** | redis:7-alpine | 6379 | Cache & Celery results backend |
| **mailhog** | mailhog/mailhog | 1025, 8025 | Email testing (SMTP + Web UI) |
| **web** | Custom (Django) | 8000 | Django REST API application |
| **celery** | Custom (Django) | - | Celery worker for background tasks |
| **celery-beat** | Custom (Django) | - | Celery beat scheduler |

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have installed:
- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

Verify installation:
```bash
docker --version
docker-compose --version
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd jobops
```

### 3. Environment Configuration

Create `.env` file from example:
```bash
cp .env.example .env
```

### 4. Build and Start Services

**Build images and start all containers:**
```bash
docker-compose up --build
```

**Or run in detached mode (background):**
```bash
docker-compose up -d --build
```

**Wait for all services to be healthy** (~30-60 seconds)

### 5. Verify Services

Check all containers are running:
```bash
docker-compose ps
```

Expected output:
```
NAME                  STATUS
jobops_api            Up (healthy)
jobops_db             Up (healthy)
jobops_rabbitmq       Up (healthy)
jobops_redis          Up (healthy)
jobops_mailhog        Up
jobops_celery         Up
jobops_celery_beat    Up
```

### 6. Access Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **Swagger Docs** | http://localhost:8000/swagger/ | - |
| **ReDoc** | http://localhost:8000/redoc/ | - |
| **Django Admin** | http://localhost:8000/admin/ | admin / admin123 |
| **RabbitMQ Management** | http://localhost:15672 | jobops_rabbit / rabbit_pass123 |
| **MailHog UI** | http://localhost:8025 | - |
