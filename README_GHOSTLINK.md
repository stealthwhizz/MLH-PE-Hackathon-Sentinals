# GhostLink 👻🔗

**A production-grade URL shortener with intelligent link defense**

Built for the MLH Production Engineering Hackathon by Team Sentinals.

## Features

### Core URL Shortening
- **Auto-generated short codes**: 6-character alphanumeric codes (62^6 = 56B combinations)
- **Custom short codes**: Bring your own memorable codes
- **Redis caching**: 5-minute TTL for hot URLs, graceful degradation if Redis unavailable
- **Soft delete**: URLs are deactivated, not deleted (preserves audit trail)

### 🛡️ GhostLink Intelligence

#### 1. Risk Scorer
Computes a 0-100 risk score for each URL based on multiple signals:
- **+30 points**: Destination domain health indicates dead target
- **+20 points**: Redirect chain length >3 hops
- **+15 points**: Ghost probe pressure (many inactive-link hits)
- **+20 points**: Suspicious top-level domain (TLD)
- **+15 points**: Repeated delete/recreate behavior

**Tiers:**
- 0-30: SAFE ✅
- 31-60: WATCHLIST ⚠️
- 61-100: THREAT 🚨

#### 2. Link Health Checker
Background worker (APScheduler) runs every 5 minutes:
- HEAD-checks every active URL
- Records status_code, latency_ms, redirect chain length
- Detects: DEAD, CHAINED, SSL_INVALID, OK

#### 3. Prometheus Metrics
Exposes at `GET /metrics` for Prometheus scraping:
- `urls_created_total`: Counter of URL creations
- `url_redirects_total`: Counter per short_code and app_version
- `redirect_latency_seconds`: Histogram of redirect times
- `ghost_probes_total`: Counter of inactive URL hits
- `destination_dead_total`: Dead destination detections
- `risk_score_threats_total`: URLs with score > 70
- `urls_active_total`, `urls_inactive_total`: Current counts
- `ghostlink_feature_flag_enabled`: Feature flag state (1/0)
- `ghostlink_release_info`: Version, git SHA, deployment metadata
- `ghostlink_rollbacks_total`: Rollback execution count
- `ghostlink_recovery_attempts_total`, `ghostlink_recovery_success_total`: Recovery outcome counters

## API Endpoints

Endpoint wording style is standardized across docs:

- `Request Example`
- `Success Response`
- `Error Responses`

Canonical request/response templates and complete error details live in `docs/API_REFERENCE.md`.

### Endpoint Matrix

| Method | Path | Success | Common Errors | Notes |
|---|---|---:|---|---|
| `POST` | `/shorten` | `201` | `400`, `409`, `422`, `500` | Create short URL with compact response |
| `POST` | `/urls` | `201` | `400`, `409`, `422`, `500` | Create short URL with full URL record (`user_id` required) |
| `GET` | `/{short_code}` | `302` | `404`, `410` | Primary redirect route |
| `GET` | `/r/{short_code}` | `302` | `404`, `410` | Redirect alias |
| `GET` | `/urls/{short_code}` | `302` | `404`, `410` | Redirect alias |
| `GET` | `/urls` | `200` | - | Supports `user_id` and `is_active` filtering |
| `GET` | `/urls/{id}` | `200` | `404` | Fetch URL by ID |
| `PATCH`, `PUT` | `/urls/{id}` | `200` | `400`, `403`, `404`, `422` | Update mutable URL fields |
| `DELETE` | `/urls/{id}` | `200` | `400`, `403`, `404` | Soft delete URL |
| `GET` | `/urls/{id}/risk` | `200` | `404` | Risk score and signal details |
| `GET` | `/health` | `200` | `503` | Includes release metadata and feature flags |
| `GET` | `/metrics` | `200` | - | Prometheus exposition format |
| `GET` | `/health-demo`, `/promo-demo`, `/checkout-demo`, `/dashboard-demo`, `/support-demo` | `200` | - | Synthetic canary routes |

### Response Template Example (POST /shorten)

Request Example:

```json
{
  "original_url": "https://example.com",
  "short_code": "custom1",
  "title": "Example Site",
  "user_id": 1
}
```

Success Response (`201`):

```json
{
  "id": 1,
  "short_code": "abc123"
}
```

Error Responses:

- `400` missing body, malformed JSON, or invalid field type
- `409` short code already exists
- `422` invalid URL format
- `500` short code generation failure

## Tech Stack

- **Backend**: Flask 3.1, Python 3.11
- **ORM**: Peewee (lightweight, hackathon-optimized)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Background Jobs**: APScheduler
- **Metrics**: prometheus-client
- **Testing**: pytest, pytest-cov (70% coverage required)
- **CI**: GitHub Actions (blocks merge on test failure or coverage <70%)

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis (optional, app works without it)
- uv (fast Python package manager)

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd MLH-PE-Hackathon-Sentinals

# Install dependencies
uv sync

# Or use pip + requirements.txt
pip install -r requirements.txt

# Create database
createdb hackathon_db

# Configure environment
cp .env.example .env
# Edit .env with your DB credentials
```

### Environment Variables

```bash
DATABASE_NAME=hackathon_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
REDIS_URL=redis://localhost:6379/0  # optional

APP_VERSION=v1-dev
PREVIOUS_APP_VERSION=v1
GIT_SHA=local
DEPLOYED_AT=unknown
RELEASE_OWNER=platform
RELEASE_NOTES_URL=
ROLLBACK_STATE_FILE=/var/lib/ghostlink-security/rollback_state.env

ENABLE_QUARANTINE_MODE=true
ENABLE_RISK_SCORING=true
ENABLE_GHOST_PROBE_ALERTS=true
ENABLE_CANARY_MONITORING=true
ENABLE_AUTO_BLOCKING=false
ENABLE_THREAT_HEATMAP=false
```

### Run Database Migrations

```bash
# Create tables
python -c "from app import create_app; app = create_app(); from app.database import db; from app.models import *; db.create_tables([Url, User, Event, HealthCheck, RiskScore])"
```

### Seed Data

```bash
# Place your CSV files in ./data/
# - users.csv
# - urls.csv
# - events.csv

python scripts/seed.py
```

### Run the Server

```bash
uv run run.py
# Or: python run.py
```

Server runs at `http://localhost:5000`

### Run Tests

```bash
# All tests with coverage
pytest --cov=app --cov-report=term app/tests/

# Unit tests only
pytest app/tests/test_unit.py

# Integration tests only
pytest app/tests/test_integration.py
```

## Docker Support

GhostLink is Docker-ready. Akshay's infrastructure setup includes:
- Dockerfile for Flask app
- docker-compose.yml with PostgreSQL + Redis + Nginx
- Prometheus + Grafana + Alertmanager for observability
- k6 for load testing

**Environment variables** are used for all configuration (12-factor app).

## Rollback Automation

Preview rollback impact before any restart:

```bash
make rollback-plan-app2
make rollback-plan-app1
```

Execute rollback:

```bash
make rollback-app2
```

Validate release and recovery signals:

```bash
curl -i http://localhost/health
curl -s http://localhost/metrics | grep -E "ghostlink_rollbacks_total|ghostlink_recovery_attempts_total|ghostlink_recovery_success_total"
```

## Project Structure

```
MLH-PE-Hackathon-Sentinals/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── database.py              # Peewee + Redis setup
│   ├── models/                  # Peewee ORM models
│   │   ├── url.py
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── health_check.py
│   │   └── risk_score.py
│   ├── routes/                  # Flask blueprints
│   │   ├── urls.py              # Core URL operations
│   │   └── health.py            # Health + metrics
│   ├── services/                # Business logic
│   │   ├── shortener.py         # Short code generation
│   │   ├── cache.py             # Redis wrapper
│   │   ├── risk_scorer.py       # Risk computation
│   │   └── link_health.py       # Background health checks
│   └── tests/                   # pytest suite
│       ├── conftest.py
│       ├── test_unit.py
│       └── test_integration.py
├── scripts/
│   └── seed.py                  # Idempotent CSV loader
├── .github/workflows/
│   └── ci.yml                   # GitHub Actions CI
├── requirements.txt
├── pyproject.toml
├── DECISIONS.md                 # Architecture decisions
└── README.md
```

## CI/CD

GitHub Actions runs on every push/PR:
1. Spins up PostgreSQL + Redis (Docker services)
2. Installs dependencies
3. Runs pytest with coverage
4. **Blocks merge if coverage < 70%**
5. **Blocks merge if any test fails**

## Edge Cases Handled (Bonus Points)

✅ **410 Gone**: Inactive URL hit returns 410, not 404  
✅ **409 Conflict**: Duplicate short_code returns 409  
✅ **422 Unprocessable**: Malformed URL returns 422  
✅ **400 Bad Request**: Missing body/fields returns 400  
✅ **404 Not Found**: Unknown short_code returns 404  
✅ **All JSON**: Never return HTML traceback

## Architecture Decisions

See [DECISIONS.md](./DECISIONS.md) for detailed rationale on:
- ORM choice (Peewee vs SQLAlchemy)
- Caching strategy (Redis TTLs)
- Background workers (APScheduler vs Celery)
- Error handling patterns
- Testing strategy
- Security considerations

## Team

**Team Sentinals**
- **Amogh**: Backend (Flask, models, routes, services, tests, CI)
- **Akshay**: DevOps (Docker, Nginx, Prometheus, Grafana, k6)

## License

MIT License - Built for MLH Production Engineering Hackathon 2026
