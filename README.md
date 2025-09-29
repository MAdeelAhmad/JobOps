# JobOps - Internal Operations Management System

A Django REST Framework-based system for managing internal operations, jobs, tasks, and equipment with role-based access control.

## Features

- **Role-Based Access Control**: Admin, Technician, Sales Agent roles
- **Job Management**: Create, assign, and track jobs with multiple tasks
- **Equipment Tracking**: Manage equipment and assign to tasks
- **Technician Dashboard**: View upcoming tasks grouped by date
- **Audit Logs**: Track all job and task changes
- **Background Tasks**: Automated overdue job flagging and email reminders
- **Analytics Dashboard**: Admin-only job statistics and reports
- **API Documentation**: Auto-generated Swagger/ReDoc documentation

## Tech Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL 15
- **Message Broker**: RabbitMQ 3.12
- **Task Queue**: Celery with Django Celery Beat
- **Cache**: Redis 7
- **Authentication**: JWT (SimpleJWT)
- **Email Testing**: MailHog
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd jobops
```

2. **Create .env file**
```bash
cp .env.example .env
```

3. **Build and start services**
```bash
docker-compose up --build -d
```

4. **Check services are running**
```bash
docker-compose ps
```

### Access Points

- **API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/swagger/
- **API Documentation (ReDoc)**: http://localhost:8000/redoc/
- **Admin Panel**: http://localhost:8000/admin/
- **RabbitMQ Management**: http://localhost:15672 (user: `jobops_rabbit`, password: `rabbit_pass123`)
- **MailHog Web UI**: http://localhost:8025

### Default Credentials

**Admin Account** (created automatically):
- Username: `admin`
- Password: `admin123`

## Role Permissions

| Action | Admin | Sales Agent | Technician |
|--------|-------|-------------|------------|
| Create/Edit Users | Yes | No | No |
| Create Jobs | Yes | Yes | No |
| Edit Own Jobs | Yes | Yes | No |
| Edit Assigned Jobs | Yes | No | Yes |
| Manage Equipment | Yes | No | No |
| View Analytics | Yes | No | No |

## Business Rules

1. **Job Completion**: Jobs can only be completed when all tasks are marked as completed
2. **Overdue Flagging**: Jobs past their scheduled date are automatically flagged as overdue (runs daily at midnight)
3. **Task Updates**: Only technicians assigned to a job can update its tasks
4. **User Management**: Only admins can create or modify user accounts

## Development Commands

### Run migrations
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Create superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Run tests
```bash
docker-compose exec web python manage.py test
```

## Project Structure

```
jobops/
├── docker-compose.yml              # Docker services configuration
├── Dockerfile                      # Docker image definition
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (git-ignored)
├── .gitignore                      # Git ignore rules
├── .dockerignore                   # Docker ignore rules
├── entrypoint.sh                   # Docker entrypoint script
├── manage.py                       # Django management script
├── README.md                       # Main project documentation
├── DOCKER_README.md                # Docker-specific documentation
├── DESIGN_DECISIONS.md             # Architecture & design decisions
│
├── jobops/                         # Django project configuration
│   ├── __init__.py                # Makes it a Python package + Celery app init
│   ├── settings.py                # Project settings
│   ├── urls.py                    # Main URL configuration
│   ├── wsgi.py                    # WSGI configuration for deployment
│   ├── asgi.py                    # ASGI configuration (async support)
│   └── celery.py                  # Celery configuration
│
├── users/                          # User management app
│   ├── __init__.py
│   ├── apps.py                    # App configuration
│   ├── models.py                  # User model (extends AbstractUser)
│   ├── serializers.py             # User serializers (Create, Update, Read)
│   ├── views.py                   # User ViewSets
│   ├── permissions.py             # User-related permissions (CanManageUsers)
│   ├── urls.py                    # User endpoints
│   ├── admin.py                   # User admin configuration
│   ├── managers.py                # Custom user manager (optional)
│   ├── migrations/                # Database migrations
│   │   └── __init__.py
│   └── tests/                     # User tests
│       ├── __init__.py
│       ├── test_models.py         # User model tests
│       ├── test_views.py          # User API tests
│       ├── test_serializers.py    # User serializer tests
│
└── ops/                            # Operations management app (UPDATED)
    ├── __init__.py
    ├── apps.py                    # App configuration
    ├── models.py                  # Equipment, Job, JobTask, JobChangeLog models
    ├── serializers.py             # Equipment, Job, Task serializers
    ├── views.py                   # Equipment, Job, Task ViewSets + Dashboard
    ├── permissions.py             # Job/Equipment permissions
    ├── urls.py                    # Operations endpoints
    ├── tasks.py                   # Celery tasks (overdue jobs, reminders)
    ├── admin.py                   # Operations admin configuration
    ├── utils.py                   # Utility functions (email helpers)
    ├── migrations/                # Database migrations
    │   └── __init__.py
    └── tests/                     # Operations tests
        ├── __init__.py
        ├── test_models.py         # Equipment, Job, Task model tests
        ├── test_views.py          # API endpoint tests
        ├── test_serializers.py    # Serializer tests
        ├── test_permissions.py    # Permission tests
```

## Celery Scheduled Tasks

- **Check Overdue Jobs**: Runs daily at 00:00 UTC
- **Send Daily Task Reminders**: Runs daily at 07:00 UTC

## API Authentication

All endpoints (except login) require JWT authentication. Include the token in request headers:

```
Authorization: Bearer <access_token>
```

**Example:**
```bash
# Login
curl -X POST http://localhost:8000/usr/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token in subsequent requests
curl -X GET http://localhost:8000/ops/jobs/ \
  -H "Authorization: Bearer <access_token>"
```

## Testing Email

Emails are sent via MailHog (for development):

1. Access MailHog UI: http://localhost:8025
2. Trigger email by:
   - Creating jobs scheduled for today
   - Running Celery beat task: `send_daily_task_reminder`
3. View received emails in MailHog interface
