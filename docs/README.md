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

## Deployment

Deployment instructions for Hetzner VPS will be added once the application is feature-complete.
