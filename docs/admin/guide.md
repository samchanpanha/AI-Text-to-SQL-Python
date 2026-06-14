# Text-to-SQL RAG System — Administrator Guide

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Authentication & User Management](#authentication--user-management)
5. [Database Setup](#database-setup)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Log Management](#log-management)
8. [Scheduled Reports](#scheduled-reports)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────┐     ┌─────────────────┐     ┌──────────┐
│  Web Chat    │────▶│                 │────▶│  MySQL   │
│  /ws/chat    │     │   FastAPI App   │     │  (data)  │
├──────────────┤     │   (app.main)    │     └──────────┘
│  Telegram    │────▶│                 │
│  Bot         │     │  ┌───────────┐  │     ┌──────────┐
├──────────────┤     │  │  OpenAI   │  │     │  Redis   │
│  REST API    │────▶│  │  GPT-4o   │  │     │(optional)│
│  /api/*      │     │  └───────────┘  │     └──────────┘
├──────────────┤     │                 │
│  n8n         │────▶│  ┌───────────┐  │     ┌──────────┐
│  Workflows   │     │  │Scheduleer │  │     │  SMTP    │
└──────────────┘     │  │APScheduler│  │────▶│  Email   │
                     │  └───────────┘  │     └──────────┘
                     │                 │     ┌──────────┐
                     │  ┌───────────┐  │────▶│ Telegram │
                     │  │  Reports  │  │     │  Bot     │
                     │  │  (Excel)  │  │     └──────────┘
                     │  └───────────┘  │
                     └─────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|---|---|---|
| API Server | FastAPI (Python) | REST + WebSocket endpoints |
| Database | MySQL 8.0 | E-commerce data, scheduler state, logs, users |
| LLM | OpenAI GPT-4o / GPT-4o-mini | Natural language → SQL conversion |
| Scheduler | APScheduler | Cron-based report generation |
| Reports | openpyxl | Excel file generation with formatting |
| Email | smtplib + Jinja2 | Report delivery via SMTP |
| Telegram | python-telegram-bot | Bot commands + file delivery |
| Auth | JWT + API Keys | Bearer tokens, user management |

---

## Quick Start

### Prerequisites
- Python 3.12+
- MySQL 8.0
- OpenAI API key

### Local Development

```bash
# 1. Clone and enter the project
cd text-to-sql

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.template .env
# Edit .env with your settings (especially OPENAI_API_KEY and DB_*)

# 5. Initialize database
python -m scripts.init_db

# 6. Run the server
uvicorn app.main:app --reload

# 7. Open in browser
open http://localhost:8000/docs   # API docs
open http://localhost:8000/chat   # Web chat UI
```

### Docker Deployment

```bash
# Development (with live reload)
docker compose up --build

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With n8n workflow engine
docker compose --profile n8n up -d
```

### First Login

On first run, a default admin account is auto-created:

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |
| API Key | Printed in server logs on first startup |

**Important:** Change the default password immediately via `POST /api/auth/login` → get token → `PUT /api/auth/users/1` with a new password.

---

## Configuration

All configuration is via environment variables loaded from `.env`. See `.env.template` for a complete list.

### Essential Settings

```ini
# ── Must Configure ──
OPENAI_API_KEY=sk-...           # Your OpenAI API key
DB_HOST=mysql                    # MySQL host (or localhost)
DB_PASSWORD=changeme             # MySQL password
SECRET_KEY=long-random-string    # JWT signing key (generate with: openssl rand -hex 32)

# ── Optional but Recommended ──
SMTP_HOST=smtp.gmail.com         # For email delivery
SMTP_USER=your@email.com
SMTP_PASSWORD=app-password
TELEGRAM_BOT_TOKEN=...           # For Telegram bot
```

### Logging Configuration

```ini
LOG_LEVEL=INFO                   # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                  # text | json (json for production log aggregators)
LOG_OUTPUT=both                  # console | file | both
LOG_FILE=/var/log/app/app.log   # Path when OUTPUT=file or both
LOG_MAX_BYTES=10485760          # 10MB rotation
LOG_BACKUP_COUNT=5              # Keep 5 rotated files
LOG_DB_ENABLED=true             # Persist logs to DB tables
LOG_DB_RETENTION_DAYS=30        # Auto-cleanup threshold
LOG_LLM_CALLS=true              # Log all OpenAI prompt/response pairs
```

### Security Settings

```ini
RATE_LIMIT_PER_MINUTE=60         # Global default rate limit
QUERY_MAX_ROWS=1000              # Max rows returned by any SQL query
QUERY_TIMEOUT_SECONDS=30         # SQL query timeout
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
```

---

## Authentication & User Management

### Authentication Methods

The system supports two authentication methods:

#### 1. JWT Bearer Token (interactive use)

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response includes access_token (expires in 24h)
# Use in subsequent requests:
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

#### 2. API Key (programmatic / n8n use)

```bash
# Generate API key (after logging in)
curl -X POST http://localhost:8000/api/auth/api-key \
  -H "Authorization: Bearer <token>"

# Use in requests:
curl http://localhost:8000/api/query \
  -H "X-API-Key: tsq_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What were total sales?"}'
```

### Managing Users (Admin Only)

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/users` | GET | List all users |
| `/api/auth/users` | POST | Create a user |
| `/api/auth/users/{id}` | PUT | Update user (role, password, status) |
| `/api/auth/users/{id}` | DELETE | Delete user |

```bash
# Create a new user
curl -X POST http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@company.com",
    "password": "securepass123",
    "role": "user"
  }'

# Disable a user (without deleting)
curl -X PUT http://localhost:8000/api/auth/users/2 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### Roles

| Role | Permissions |
|---|---|
| `admin` | Full access: user management, all data, system config, logs, scheduler |
| `user` | Query access, view own API keys, receive scheduled reports |

---

## Database Setup

### Schema

The system uses two sets of tables:

**E-Commerce Data** (query target):
- `customers`, `categories`, `products`, `orders`, `order_items`

**System Tables** (operational):
- `users` — authentication and authorization
- `scheduled_tasks` — cron job definitions
- `report_definitions` — SQL queries per task
- `delivery_configs` — email/telegram delivery configs
- `task_execution_logs` — report run history
- `audit_logs` — all API request logs
- `llm_call_logs` — all OpenAI API call logs

### Initialization

```bash
# Auto-create all tables and seed sample data
python -m scripts.init_db

# Or via Docker (runs automatically on first start)
docker compose up
```

### Adding Custom Data

1. Connect to MySQL and add your own tables
2. The schema is introspected at runtime — no code changes needed
3. The LLM automatically discovers new tables and columns

### Database Migrations

Tables are created via SQLAlchemy's `Base.metadata.create_all()` on startup.
For production schema changes, use the SQL scripts in `scripts/init_db.sql`
as a reference.

---

## Monitoring & Health Checks

### Health Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "app": {
    "status": "healthy",
    "name": "Text-to-SQL RAG",
    "version": "1.0.0",
    "environment": "production",
    "debug": false
  },
  "database": {
    "status": "healthy",
    "host": "mysql",
    "database": "text_to_sql",
    "latency_ms": 3
  },
  "llm": {
    "status": "healthy",
    "model": "gpt-4o"
  },
  "disk": {
    "status": "healthy",
    "path": "/tmp/reports",
    "free_gb": 45.2,
    "total_gb": 100.0,
    "used_pct": 54.8
  },
  "uptime": 86400.5,
  "timestamp": 1718400000.0
}
```

### Admin Dashboard

```bash
curl http://localhost:8000/api/admin/dashboard?days=7 \
  -H "Authorization: Bearer <admin-token>"
```

Returns: user stats, API request counts, error rates, LLM usage, scheduler status.

### System Info (no secrets)

```bash
curl http://localhost:8000/api/admin/system \
  -H "Authorization: Bearer <admin-token>"
```

### Docker Healthcheck

The Dockerfile includes a healthcheck at `/health` that Docker uses to
determine container health.

---

## Log Management

### Log Storage

Logs are stored in two places:

1. **File logs** — rotated at 10MB, configured via `LOG_FILE` / `LOG_MAX_BYTES`
2. **Database logs** — persisted to `audit_logs` and `llm_call_logs` tables

### Viewing Logs via API

#### API Access Logs

```bash
# Last 50 requests
curl http://localhost:8000/api/logs/audit \
  -H "Authorization: Bearer <admin-token>"

# Filter by status code (show errors)
curl "http://localhost:8000/api/logs/audit?status_code=500&days=7" \
  -H "Authorization: Bearer <admin-token>"

# Filter by path
curl "http://localhost:8000/api/logs/audit?path=/api/query" \
  -H "Authorization: Bearer <admin-token>"
```

#### LLM Call Logs

```bash
# LLM usage stats (calls, tokens, estimated cost)
curl http://localhost:8000/api/logs/llm/stats?days=7 \
  -H "Authorization: Bearer <admin-token>"

# Full prompt/response detail
curl http://localhost:8000/api/logs/llm/42 \
  -H "Authorization: Bearer <admin-token>"
```

#### Task Execution Logs

```bash
curl http://localhost:8000/api/logs/task-executions?task_id=1&days=30 \
  -H "Authorization: Bearer <admin-token>"
```

### Log Cleanup

Logs are automatically purged daily at 3:00 AM based on `LOG_DB_RETENTION_DAYS`.

Manual trigger:
```bash
curl -X POST "http://localhost:8000/api/logs/cleanup?days=30" \
  -H "Authorization: Bearer <admin-token>"
```

### Log Format (JSON mode)

When `LOG_FORMAT=json`, every log entry is structured JSON:
```json
{
  "timestamp": "2026-06-14T12:00:00+00:00",
  "level": "INFO",
  "logger": "app.access",
  "module": "middleware.py",
  "function": "dispatch",
  "line": 42,
  "message": "GET /api/query → 200 (150ms)",
  "request_id": "a1b2c3d4",
  "duration_ms": 150,
  "status_code": 200,
  "method": "GET",
  "path": "/api/query",
  "user_ip": "192.168.1.100"
}
```

---

## Scheduled Reports

### Creating a Report Task

Tasks are created with a cron expression, one or more SQL report definitions,
and delivery configuration(s).

**Step 1: Create the task**

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Sales Report",
    "description": "Sales report sent every Monday at 8 AM",
    "cron_expression": "0 8 * * 1",
    "timezone": "UTC",
    "enabled": true
  }'
```

**Step 2: Add a report definition**

```bash
curl -X POST http://localhost:8000/api/tasks/1/reports \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Top Products",
    "sql_query": "SELECT p.name, SUM(oi.qty * oi.unit_price) as revenue FROM products p JOIN order_items oi ON p.id = oi.product_id JOIN orders o ON o.id = oi.order_id WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY p.id ORDER BY revenue DESC LIMIT 10",
    "format": "xlsx",
    "sheet_name": "Top Products",
    "sort_order": 1
  }'
```

**Step 3: Add delivery (email)**

```bash
curl -X POST "http://localhost:8000/api/tasks/1/delivery?type=email" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "name": "Manager Email"
  }'
```

Then configure email details:
```bash
curl -X PUT http://localhost:8000/api/tasks/1/delivery \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "to_recipients": "manager@company.com",
    "cc_recipients": "team@company.com",
    "subject_template": "{{ task_name }} - {{ date }}",
    "body_template": "<h2>{{ task_name }}</h2><p>Attached is the weekly report.</p>"
  }'
```

### Cron Expression Format

```
┌───────── minute (0-59)
│ ┌───────── hour (0-23)
│ │ ┌───────── day of month (1-31)
│ │ │ ┌───────── month (1-12)
│ │ │ │ ┌───────── day of week (0-6) (Sunday=0)
│ │ │ │ │
* * * * *
```

| Purpose | Expression |
|---|---|
| Every hour | `0 * * * *` |
| Daily at 8 AM | `0 8 * * *` |
| Every Monday at 8 AM | `0 8 * * 1` |
| 1st of month at midnight | `0 0 1 * *` |
| Every 30 minutes | `*/30 * * * *` |

### Manual Execution

```bash
curl -X POST http://localhost:8000/api/tasks/1/execute \
  -H "Authorization: Bearer <admin-token>"
```

---

## Security

### Authentication Flow

```
User → Login (username/password) → JWT token (24h expiry)
                                   ↓
                          Use Bearer token for all API calls
                                   ↓
                          Or generate API key (no expiry)
                                   ↓
                          Use X-API-Key header for programmatic access
```

### Rate Limiting

- Per-user: configured by `rate_limit_per_minute` on the User model
- Global default: `RATE_LIMIT_PER_MINUTE` (60/min)
- Rate limit keyed by user ID (authenticated) or IP (anonymous)
- Response includes `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers
- 429 response when exceeded

### SQL Safety

| Protection | Implementation |
|---|---|
| Read-only queries | Server appends `SELECT` prefix check |
| Max rows | `LIMIT 1000` enforced server-side |
| Query timeout | `SET max_execution_time=30000` |
| No DDL/DML | Only SELECT queries are executed |

### API Key Security

- API keys are stored hashed in the database
- Keys shown only once at generation time
- Regenerate via `POST /api/auth/api-key`
- Revoke access by disabling user or regenerating key

### Environment Security

- `.env` files are never committed (in `.gitignore`)
- Secrets loaded via `pydantic-settings` with `.env` file
- Production secrets should use Docker secrets or a vault

---

## Troubleshooting

### Common Issues

#### "Authentication required"

The endpoint requires authentication. Add:
```bash
-H "Authorization: Bearer <your-token>"
# or
-H "X-API-Key: <your-api-key>"
```

#### "Rate limit exceeded"

Wait 60 seconds or contact an admin to increase your limit.

#### LLM calls failing

```bash
# Check LLM health
curl http://localhost:8000/health

# Check recent LLM errors
curl http://localhost:8000/api/logs/llm?success=false \
  -H "Authorization: Bearer <admin-token>"
```

#### Database connection errors

```bash
# Check database health
curl http://localhost:8000/health

# Verify MySQL is running
docker compose exec mysql mysqladmin ping -h localhost
```

#### n8n cannot reach the app

Ensure both are on the same Docker network (they are by default):
```bash
docker compose exec n8n curl http://app:8000/health
```

#### Report generation fails

```bash
# Check task execution logs
curl http://localhost:8000/api/logs/task-executions?task_id=1 \
  -H "Authorization: Bearer <admin-token>"
```

### Logs

```bash
# View live application logs (Docker)
docker compose logs -f app

# View n8n logs
docker compose logs -f n8n

# Check file logs (if LOG_OUTPUT=file)
tail -f logs/app.log
```

### Health Check Monitoring (Prometheus/Grafana)

The `/health` endpoint provides all metrics needed for basic monitoring:
- Application status
- Database connectivity and latency
- LLM API key presence
- Disk space for report generation
- Uptime

For detailed metrics, use the audit logs API (`/api/logs/audit/stats`) and
admin dashboard (`/api/admin/dashboard`).
