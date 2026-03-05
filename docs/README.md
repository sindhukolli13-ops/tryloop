# Tryloop — Documentation

## Overview

Tryloop is a platform for renting electronic devices on short-term trials (7 or 14 days) before deciding to purchase. Built for the Dutch market with a focus on sustainability.

## Architecture

| Service    | Technology            | Port |
|------------|-----------------------|------|
| Frontend   | Next.js + TypeScript  | 3000 |
| Backend    | FastAPI (Python)      | 8000 |
| Database   | PostgreSQL 16         | 5432 |
| Cache      | Redis 7               | 6379 |
| Proxy      | Nginx                 | 80   |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- A `.env` file (copy from `.env.example`)

### Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd tryloop

# 2. Create your environment file
cp .env.example .env
# Edit .env with your secrets

# 3. Start all services
docker compose up --build

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/health
# Via Nginx: http://localhost
```

### Project Structure

See `CLAUDE.md` for the full project structure, tech stack, and build order.

---

## Local Testing Runbook

### Step 1: Install Docker Desktop (macOS)

```bash
brew install --cask docker
```

Open **Docker Desktop** from Applications and wait until the whale icon in the menu bar stops animating.

### Step 2: Start all services

```bash
docker compose up --build
```

First build takes ~5–10 minutes. You'll see logs for all 5 services: `postgres`, `redis`, `backend`, `frontend`, `nginx`. Postgres and Redis healthcheck before the backend starts.

### Step 3: Verify services are running

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","environment":"development"}
```

- **Frontend:** http://localhost:3000
- **Backend API docs (Swagger):** http://localhost:8000/docs
- **Via Nginx:** http://localhost

### Step 4: Seed the database

```bash
docker compose exec backend python /scripts/seed.py
```

Expected output:
```
Database seeded successfully!
  - 4 users (1 admin, 1 staff, 2 customers)
  - 6 devices
  - 12 device units
  - 3 trials (1 active, 1 refurbishing, 1 reserved)
  - 7 payments
  - 1 refurbishment log
  - 1 sustainability metric record
```

### Step 5: Test admin inventory endpoints

```bash
# 1. Login as admin and capture the token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tryloop.nl","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Got token: ${TOKEN:0:20}..."

# 2. List all device units
curl -s http://localhost:8000/inventory/units \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 3. List all devices (product catalog)
curl -s "http://localhost:8000/devices?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 4. Get a specific unit
curl -s http://localhost:8000/inventory/units/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Seeded test accounts

| Role     | Email                 | Password      |
|----------|-----------------------|---------------|
| Admin    | `admin@tryloop.nl`    | `admin123`    |
| Staff    | `staff@tryloop.nl`    | `admin123`    |
| Customer | `emma@example.com`    | `customer123` |
| Customer | `lucas@example.com`   | `customer123` |

### Stopping services

```bash
docker compose down          # stop and remove containers
docker compose down -v       # also wipe the database volume (full reset)
```

---

## Deployment

Deployment instructions for Hetzner VPS will be added once the application is feature-complete.
