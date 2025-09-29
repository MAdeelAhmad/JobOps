# JobOps - Design Decisions

## Core Architecture

**Stack:** Django REST Framework + PostgreSQL + RabbitMQ + Redis + Docker

### Key Technology Choices

| Component | Choice | Why |
|-----------|--------|-----|
| **Database** | PostgreSQL | ACID compliance, JSONField support, advanced indexing |
| **Message Broker** | RabbitMQ | Message durability, guaranteed delivery, built-in monitoring |
| **Cache/Sessions** | Redis | Fast in-memory operations, Celery result backend |
| **Authentication** | JWT (SimpleJWT) | Stateless, mobile-friendly, scalable |

---

## Data Model Decisions

### User Management
- **Single User Model** with role field (`admin`, `technician`, `sales_agent`)
- Extends Django's `AbstractUser` for compatibility
- Role-based queryset filtering at database level

### Job Workflow
- **Job → Tasks hierarchy** with ordered sequential tasks
- Equipment assigned to tasks (not jobs) for granular tracking
- Job completion blocked until all tasks complete
- Automatic audit logging with JSONField for change tracking

### Relationships
```
Job (1:N) → JobTask (M:N) → Equipment
User (1:N) → Job (assigned_to)
User (1:N) → Job (created_by)
```

---

## API Design

### Structure
- **RESTful endpoints** with DRF ViewSets
- **Role-based permissions** via custom permission classes
- **Separate serializers** for read/write operations
- **Auto-generated docs** with Swagger/ReDoc

### Security
- JWT tokens: 60min access, 24hr refresh
- Custom permissions enforce business rules
- Environment-based configuration
- CORS configured for specific origins

---

## Business Logic

### Critical Rules
1. **Job Completion Validation**: All tasks must be completed first
2. **Auto-timestamps**: Task completion times captured automatically  
3. **Overdue Flagging**: Daily Celery task marks overdue jobs
4. **Audit Trail**: All changes logged with user/timestamp/details

### Background Tasks
- **Celery + RabbitMQ** for async processing
- **MailHog** for development email testing
- **Celery Beat** for scheduled tasks (overdue checks)

---

## Performance & Scalability

### Database Optimization
- **Indexes** on frequently queried fields (`status`, `role`, `scheduled_date`)
- **select_related/prefetch_related** to prevent N+1 queries
- **Role-based filtering** at queryset level

### Development Setup
- **Docker Compose** with 7 services for consistency
- **Health checks** ensure proper startup order
- **Volume mounts** for live code reloading

---

## Testing Strategy

**Comprehensive coverage**: Models, Views, Serializers, Permissions, Tasks
- Django TestCase with transaction rollback
- Test isolation for reliability

---

## Trade-offs Made

### Accepted Complexity
- **7 Docker containers** → Development consistency
- **Model-level validation** → Data integrity + slight performance cost
- **Separate serializers** → API clarity + more code

### Current Limitations
- No real-time updates (WebSockets)
- No file uploads (S3 integration)
- Email notifications only (SMS/push)

---
