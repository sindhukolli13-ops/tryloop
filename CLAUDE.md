# Tryloop — Project Brief for Claude Code

## Workflow Rules for Claude Code

> **Read this first before doing anything.**

1. **Work one build step at a time.** Follow the Build Order section below. Do NOT skip ahead or combine steps.
2. **After completing each step**, commit all changes with a clear descriptive commit message (e.g. `feat: scaffold project structure with Docker Compose and env templates`).
3. **After committing, stop and summarize:** what was done, what files were created/changed, and what the next step is. Do NOT proceed to the next step without my explicit confirmation.
4. **If a step is too large for one session**, break it into sub-steps. Commit after each sub-step. Always leave the project in a working state — no half-finished files.
5. **When resuming a new session**, read this file first, then check the git log and existing file structure to understand where things stand before writing any code.
6. **Ask before making architectural decisions** that aren't covered in this doc. Don't guess — ask.
7. **Add brief inline comments** to explain non-obvious code. I'm a people manager getting back into code, so clarity helps.

---

## What is Tryloop?
Tryloop is a platform for renting electronic devices on short-term trials (e.g. 7 days) before deciding to purchase. It operates in the Netherlands and is focused on sustainability — every rented device extends its lifecycle and reduces e-waste.

The platform has two sides:
- **Customer-facing**: browse devices, request a trial, manage rentals, decide to buy or return
- **Admin/staff-facing**: manage inventory, track refurbishment, view sustainability metrics

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (self-hosted) |
| Caching / Sessions | Redis (self-hosted) |
| Auth | Auth.js (NextAuth) + JWT with refresh tokens + OAuth (Google) |
| Payments | Stripe (checkout + deposits only) |
| Validation | Pydantic (backend) + Zod (frontend) |
| Reverse Proxy | Nginx |
| Hosting | Self-hosted VPS (Hetzner, EU) |

**Important:** No third-party SaaS platforms (no Supabase, Firebase, Vercel, etc.). Everything is self-hosted except Stripe for payments.

**TypeScript must be used throughout the entire frontend.** All components, pages, API calls, and utilities must be fully typed.

---

## Brand & Design

- **Name:** Tryloop
- **Domain:** tryloop.nl
- **Tone:** Clean, minimal, trustworthy, professional — think Apple meets Stripe meets Linear
- **Audience:** Dutch consumers interested in trying electronics before buying
- **Design language:** Minimal, modern, light theme. Think sustainability meets tech — clean whites, earthy accents, confident typography. Avoid generic AI aesthetics (no purple gradients, no Inter font, no cookie-cutter layouts).
- **Mobile-first:** All pages must be designed mobile-first, then enhanced for desktop

### Homepage Must Include
1. **Hero** — clear value proposition ("Try before you buy. Return, or keep it.")
2. **How it works** — 3-step visual explanation (Try → Decide → Buy or Return)
3. **Sustainability impact** — live stats (CO₂ saved, devices looped, etc.)
4. **Featured devices** — curated product cards with availability
5. **Call to action** — "Start a Trial" prominent CTA

---

## Core Features

### 1. Device Catalog (Customer)
- Browse available devices by category (phones, laptops, tablets, wearables, headphones, etc.)
- Each device has: name, brand, specs, photos, trial price, purchase price, availability status, condition grade
- Filter by category, availability, price range
- **Product comparison** — select up to 3 devices to compare specs side by side
- **Featured products** — admin-curated devices shown prominently on homepage
- Inventory-aware availability (shows "Available", "In Trial", "Coming Soon")

### 2. Trial Rental Flow (Customer)
- Select a device → choose trial duration (**7 or 14 days**) → pay trial fee + refundable deposit via Stripe
- Inventory reserved immediately on payment
- Receive confirmation with trial start/end dates
- At end of trial: customer **returns the device** (deposit refunded, minus any damage deductions)
- Email notifications: trial confirmation, reminder at day 5 (or day 12 for 14-day), trial end notice, return instructions

**Trial Lifecycle States:**
```
reserved → shipped → active → returned → refurbishing → ready → available
                                          (deposit refunded, device re-enters trial pool)

reserved → cancelled (before shipment only; full refund including deposit)
```
- Trials are **try-only** — there is no purchase option at the end of a trial
- The trialed unit always returns and goes through refurbishment before becoming available again
- Purchasing products happens through a **separate purchase flow** for new/unused inventory
- Trial fee is non-refundable (this is Tryloop's revenue); deposit is always fully refunded (minus any damage deductions)

### 3. User Accounts (Customer)
- Register/login via Auth.js — email/password and OAuth (Google)
- Email verification on signup
- Password reset via email link
- JWT with refresh tokens for session management
- Dashboard:
  - Active trials (with trial lifecycle status)
  - Trial history
  - Purchases (new/unused products bought separately)
  - Damage reports submitted
- Manage return requests

### 4. Inventory Management (Admin)
- Add/edit/remove devices (product catalog)
- Track each physical unit by unique serial number
- **Condition grades per unit:** `New`, `Like New`, `Refurb A`, `Refurb B`
- Device unit statuses: `available`, `reserved`, `shipped`, `active`, `returned`, `refurbishing`, `retired`, `sold`
- Track **utilization rate** per unit (% of time rented vs sitting available)
- Track **total lifecycle revenue** per unit across all rentals
- Assign devices to rental orders
- Flag damaged units and link to damage reports
- **Set pricing rules** per device or category (trial fee, deposit amount, purchase price)
- **Manage featured products** (toggle which devices appear on homepage)
- Add/edit admin users and staff roles

### 5. Damage Reports
- Customers can submit a damage report during or after a trial
- Fields: description, photos, severity (cosmetic / functional / severe)
- Admin can review, link to refurbishment log, and decide deposit deduction
- Damage history tracked per device unit permanently

### 6. Refurbishment Lifecycle Tracking (Admin)
- When a device is returned, log its condition: `good`, `needs_cleaning`, `needs_repair`, `damaged`
- Create refurbishment tasks with status: `pending`, `in_progress`, `completed`
- Track refurbishment history per device unit
- Once refurbished, mark as `available` again

### 7. Rental Order Management (Admin)
- View all active, upcoming, and past rentals
- Flag overdue returns
- Process returns and trigger deposit refunds via Stripe
- Manage separate purchase orders for new/unused products

### 8. Sustainability Dashboard (Admin + Public summary)
- Total devices in circulation
- Total trials completed
- **Number of prevented new purchases** (trials that ended in return = one new device not bought)
- Estimated CO₂ saved (configurable kg CO₂ per device category)
- Number of devices given a second/third/nth life
- Average number of rental cycles per device (**refurb rate**)
- Lifecycle loops per device unit
- Build backend structure to support future sustainability reporting exports (CSV, PDF)

### 9. Analytics (Admin)
- Trial completion rate (% of trials that complete without issues)
- Repeat trial rate (% of customers who start a second trial)
- Purchase conversion rate (visitors → new product purchases)
- Abandoned checkout tracking
- Inventory utilization analytics per device/category
- Revenue breakdown: trial fees vs direct purchases
- Top performing devices by trial demand

---

## Database Schema (suggested starting point)

All tables must have proper indexes on foreign keys and frequently queried columns.

### `users`
- id, email, name, hashed_password, oauth_provider, oauth_id, role (customer/admin/staff), email_verified, created_at, updated_at

### `devices` (product catalog)
- id, name, brand, category, description, specs (JSON), images (array), trial_price_7d, trial_price_14d, purchase_price, deposit_amount, is_featured, is_active, created_at, updated_at

### `device_units` (physical inventory)
- id, device_id (FK), serial_number, condition_grade (New/Like New/Refurb A/Refurb B), status, rental_count, total_lifecycle_revenue, created_at, updated_at

### `trials` (replaces `rentals` — more precise naming)
- id, user_id (FK), device_id (FK), device_unit_id (FK), duration_days, start_date, end_date, status (reserved/shipped/active/returned/refurbishing/ready/available/cancelled), trial_fee, deposit_amount, stripe_payment_intent_id, created_at, updated_at

> **Note:** `device_id` is denormalized from `device_units` for faster querying ("all trials for this product model") without joining through `device_units` every time.

### `purchases` (separate flow — new/unused products only)
- id, user_id (FK), device_id (FK), device_unit_id (FK), purchase_price, stripe_payment_intent_id, created_at

> **Note:** Purchases are not linked to trials. This is a separate flow for buying new/unused inventory directly.

### `payments`
- id, user_id (FK), trial_id (FK, nullable), purchase_id (FK, nullable), type (trial_fee/deposit/deposit_refund/purchase/refund), amount, currency, stripe_intent_id, status, created_at

### `damage_reports`
- id, trial_id (FK), user_id (FK), device_unit_id (FK), description, photos (array), severity (cosmetic/functional/severe), admin_notes, deposit_deduction, status (submitted/under_review/resolved), created_at, updated_at

### `refurbishment_logs`
- id, device_unit_id (FK), trial_id (FK), condition_on_return, tasks (JSON), status (pending/in_progress/completed), technician_notes, created_at, updated_at, completed_at

### `audit_logs`
- id, user_id (FK), action, entity_type, entity_id, metadata (JSON), ip_address, created_at

### `sustainability_metrics` (computed/cached)
- id, period, total_trials, total_devices_active, co2_saved_kg, devices_given_second_life, prevented_purchases, avg_lifecycle_loops, updated_at

---

## Project Structure

```
tryloop/
├── frontend/                  # Next.js app (TypeScript throughout)
│   ├── app/
│   │   ├── (customer)/        # Customer-facing pages
│   │   │   ├── page.tsx       # Homepage (hero, how it works, sustainability, featured)
│   │   │   ├── devices/       # Device catalog + detail + comparison
│   │   │   ├── dashboard/     # User dashboard (trials, history, damage reports)
│   │   │   ├── checkout/      # Trial booking + Stripe checkout
│   │   │   ├── shop/          # Browse & buy new/unused products (separate from trials)
│   │   │   └── auth/          # Login, signup, verify, reset password
│   │   ├── (admin)/           # Admin panel (role-gated)
│   │   │   ├── inventory/     # Device + unit management, pricing rules
│   │   │   ├── trials/        # Trial order management
│   │   │   ├── refurbishment/ # Refurbishment tracking
│   │   │   ├── damage/        # Damage report review
│   │   │   ├── sustainability/# Sustainability metrics dashboard
│   │   │   └── analytics/     # Conversion + utilization analytics
│   │   └── api/               # Next.js API routes (auth only)
│   ├── components/            # Reusable UI components
│   └── lib/                   # API client, helpers, Zod schemas
│
├── backend/                   # FastAPI app (Python)
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py            # Login, signup, OAuth, refresh tokens
│   │   ├── devices.py         # Product catalog
│   │   ├── trials.py          # Trial lifecycle management
│   │   ├── purchases.py       # Purchase flow
│   │   ├── inventory.py       # Device unit management
│   │   ├── refurbishment.py   # Refurbishment logs
│   │   ├── damage.py          # Damage reports
│   │   ├── payments.py        # Stripe integration
│   │   ├── sustainability.py  # Metrics + CO₂ calculations
│   │   ├── analytics.py       # Conversion + utilization data
│   │   └── admin.py           # Admin-only operations
│   ├── services/              # Business logic (orchestrates repositories)
│   ├── repositories/          # Database queries (replaces crud/)
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas (request/response validation)
│   ├── middleware/            # Error handling, logging, rate limiting
│   └── core/                  # Config, database, auth, security
│
├── nginx/
│   └── nginx.conf
├── scripts/
│   └── seed.py                # Database seed script (imports from backend/ package)
├── docs/
│   └── README.md              # Setup, deployment, architecture docs
├── docker-compose.yml
└── .env.example
```

---

## Build Order

Build in this sequence to always have a working foundation:

1. **Project scaffolding** — folder structure, Docker Compose (frontend + backend + postgres + redis + nginx), environment variables, README skeleton
2. **Database** — PostgreSQL setup, SQLAlchemy models, Alembic migrations, seed script
3. **Auth** — email/password registration + login, email verification, password reset, Google OAuth, JWT with refresh tokens, RBAC (customer/admin/staff)
4. **Device catalog** — CRUD for devices and device units, condition grades, customer browsing, filtering, product comparison
5. **Trial flow** — create trial, inventory reservation, Stripe checkout, trial lifecycle state machine
6. **Return flow + deposit refund** — return processing, deposit refund via Stripe, unit status update, trigger refurbishment
7. **Purchase flow (separate)** — browse and buy new/unused products directly, Stripe checkout, purchases table, unit status update to `sold`
7. **Admin inventory management** — unit tracking, condition grades, utilization rate, lifecycle revenue, pricing rules, featured products
8. **Damage reports** — customer submission, admin review, deposit deduction logic
9. **Refurbishment tracking** — condition logging, task management, lifecycle updates, link to damage reports
10. **Sustainability dashboard** — metrics calculation, CO₂ config per category, public summary + admin detail
11. **Analytics dashboard** — conversion rates, abandoned checkout, inventory utilization, revenue breakdown
12. **Email notifications** — confirmation, trial reminders, return reminder, purchase receipt (SMTP, no third-party)
13. **Non-functional hardening** — rate limiting, secure headers, CSRF protection, input sanitization, audit logging, error middleware, structured logging
14. **Polish** — mobile-first responsive design, loading states, error states, empty states, seed data for demo

---

## Key Business Rules

- A device unit can only be rented by one customer at a time — prevent double booking at the database level
- Trial fee is non-refundable — this is Tryloop's core revenue from trials
- Deposit is fully refundable on return in acceptable condition (minus any damage deductions decided by admin)
- Trials are try-only — there is no option to purchase the trialed device; purchasing happens through a separate flow for new/unused products
- Device unit must go through refurbishment check before being marked `available` again
- Overdue trials (past end_date with status still `active`) must be flagged automatically
- CO₂ savings calculation: each completed trial = one new purchase potentially avoided = configurable kg CO₂ per device category
- Damage reports can trigger partial or full deposit deduction, decided by admin
- All payment-related state changes must be logged in `audit_logs`
- Trial duration options: 7 days or 14 days (extensible — don't hardcode, use config)

---

## Non-Functional Requirements

These must be implemented — not optional polish:

- **Rate limiting** — on auth endpoints especially (login, signup, password reset)
- **Secure HTTP headers** — HSTS, X-Frame-Options, CSP, X-Content-Type-Options via Nginx
- **CSRF protection** — on all state-changing endpoints
- **Input sanitization** — all user inputs validated and sanitized via Pydantic (backend) + Zod (frontend)
- **Error handling middleware** — consistent JSON error responses across all API routes
- **Structured logging** — log all requests, errors, and key business events (trial created, payment captured, etc.)
- **Audit logs** — record all admin actions and sensitive user actions with IP + timestamp
- **SOLID principles** — modular, single-responsibility code structure throughout
- **Clean architecture** — strict separation: routers → services → repositories → models

---

## Environment Variables Needed

```
# Database
# Use service name 'postgres' (not localhost) when running in Docker Compose
DATABASE_URL=postgresql://user:password@postgres:5432/tryloop

# Redis
# Use service name 'redis' (not localhost) when running in Docker Compose
REDIS_URL=redis://redis:6379

# Auth
NEXTAUTH_SECRET=
NEXTAUTH_URL=https://tryloop.nl
JWT_SECRET=
JWT_REFRESH_SECRET=

# OAuth - Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=

# Email (SMTP)
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@tryloop.nl

# App
NEXT_PUBLIC_API_URL=https://tryloop.nl/api
NEXT_PUBLIC_APP_URL=https://tryloop.nl
APP_ENV=production

# Sustainability config (kg CO₂ per category, adjustable)
CO2_PER_PHONE_KG=70
CO2_PER_LAPTOP_KG=300
CO2_PER_TABLET_KG=130
CO2_PER_WEARABLE_KG=30
CO2_PER_HEADPHONES_KG=25
```

---

## Expected Deliverables

By the end of the full build, the project should include:

1. Full project folder structure (as above)
2. Complete database schema with migrations
3. All backend API routes documented
4. All frontend pages built and functional
5. Admin dashboard fully operational
6. Seed script (`scripts/seed.py`) with realistic sample data (devices, users, trials)
7. Deployment instructions for Hetzner VPS with Docker
8. README with setup guide, architecture overview, and env var documentation
9. `.env.example` with all required variables

---


