# Smart Event Tickets — Specification v1

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask |
| Frontend | React (Vite) |
| Database | PostgreSQL 15+ |
| Cache/Queue | Redis (RQ for background jobs) |
| Telegram Bot | python-telegram-bot (async, webhook mode) |
| File Storage | Local filesystem (Docker volume) |
| Deployment | Docker Compose |
| API Docs | OpenAPI/Swagger (APIFlask) |

## Architecture

- **API-first** RESTful backend
- **React SPA** frontend for organizers (event management, check-in dashboard)
- **Telegram Bot** as a first-class citizen — attendees interact equally via web or bot
- **Background workers** for async tasks (Telegram messages, reminders, PDF generation)
- **Plugin system** via Python entry points for extensibility (payment, email, auth)

---

## Core Entities

```
Organization (tenant)
  ├── name, slug, settings (JSON)
  ├── Users (organizers)
  │     └── role: admin | operator | checkin_staff
  ├── TelegramBot (config per org: token, webhook URL)
  ├── Events
  │     ├── id, title, description, date, location, capacity
  │     ├── status: draft | published | cancelled | completed
  │     ├── seating_type: general | assigned
  │     └── TicketTypes
  │           ├── name, description, price (0 for free), capacity
  │           └── max_per_order
  ├── Orders
  │     ├── status: pending | confirmed | cancelled
  │     ├── tickets -> Tickets[]
  │     └── waitlist_entry -> Waitlist (nullable)
  ├── Tickets
  │     ├── unique QR code hash
  │     ├── seat (nullable)
  │     ├── checked_in: boolean, checked_in_at
  │     └── telegram_message_id (sent ticket card ID for updates)
  └── Attendee
        ├── email (optional)
        ├── name
        ├── telegram_chat_id
        ├── telegram_linked: boolean
        └── link_code (used during /link)
```

---

## Multi-tenant Design

- Organizations are isolated tenants (row-level isolation via `organization_id` on all tables)
- Each org operates independently
- Super admin panel for managing organizations (separate from tenant users)
- Each org can configure its own Telegram bot token

---

## Authentication & Authorization

### For organizers (web dashboard):
- Email/password (bcrypt hashing)
- Magic link (token expiring in 15 min)
- OAuth (Google, GitHub) — via plugin
- JWT access + refresh tokens
- RBAC within organizations: admin (full control), operator (manage events), check-in staff (scan only)

### For attendees (no login required):
- Guest checkout (no account)
- Optional: create account to view/manage tickets on web
- Telegram bot serves as "account" equivalent on mobile

---

## Events

- Title, description, date/time, location, capacity
- Cover image upload
- Status: draft, published, cancelled, completed
- Configurable per event: general admission OR assigned seating
- Tags/categories (optional)

---

## Ticketing

- Free tickets in v1 (price field ready for paid plugin)
- Multiple ticket types per event (e.g., General, VIP, Early Bird)
- Each ticket type has its own capacity and max-per-order limit
- Real-time capacity tracking
- QR code per ticket: SHA-256 hash -> QR image embedded in ticket card

---

## Registration Flow

### Web Flow
1. Attendee visits event page, selects ticket type, fills form
2. Form fields: **Name (required)**, **Email (optional)**, **Telegram contact (optional)**
3. On submit -> order confirmed -> ticket generated
4. If Telegram contact provided -> bot sends ticket card to that chat (after `/link` verification)
5. If no Telegram -> "Want to receive tickets on Telegram?" prompt with link code
6. Link code shown on thank-you page + can be used later via `/link <code>`

### Telegram Flow
1. `/events` -> browse published events with inline buttons
2. Select event -> choose ticket type
3. Bot collects: name (via inline form), email (optional)
4. Order confirmed -> ticket card sent immediately
5. Link code generated for web management

### Linking Methods
1. **At registration**: Provide Telegram handle, system sends link code to initiate connection
2. **Post-registration**: `/link <code>` where code is from web order confirmation page
3. **Cross-linking**: `/link` without code -> bot asks for email, looks up unlinked tickets
4. **Multiple attendees per Telegram**: One Telegram account can hold tickets for multiple people

---

## Telegram Bot — Full Design

The Telegram bot is a **first-class interface** alongside the web — not just for notifications.

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + inline keyboard: find events, link account, my tickets |
| `/link <code>` | Link Telegram to a registration using the unique code from web checkout |
| `/my_tickets` | List all upcoming tickets with inline "View" button per ticket |
| `/events` | Browse published events of the organization |
| `/subscribe <event_id>` | Subscribe to reminders for an event |
| `/unsubscribe <event_id>` | Unsubscribe |

### Inline Ticket Card (sent on order confirmation)

When an order is confirmed, the bot sends an inline ticket card as a photo + caption:

```
[QR CODE IMAGE]

🎫 Event Title
📅 June 25, 2026 at 7:00 PM
📍 Venue Name
👤 John Doe
💺 Section A, Row 5, Seat 12 (if assigned)

[✅ Add to Calendar] [📍 View Map]
```

- QR code is rendered inline as a photo (not file attachment)
- Caption shows all relevant ticket info
- Inline keyboard buttons for "Add to Calendar" (.ics) and "View Map" (location link)
- If event details change, bot edits the original message caption

### Proactive Messages

| Trigger | Message | Timing |
|---------|---------|--------|
| Order confirmed | Ticket card with QR | Immediately |
| Event reminder | "Reminder: [Event] starts in 24h!" + QR | 24h before |
| Event reminder | Same | 1h before |
| Event cancelled | "[Event] has been cancelled." | On cancellation |
| Event rescheduled | "[Event] has been moved to [new date]." | On reschedule |
| Spot opened (waitlist) | "A spot opened for [Event]! You have 2h to claim it." | On spot open |
| Check-in prompt | "Ready to check in? Show your QR at the entrance." | At event start |

### Bot Architecture
- python-telegram-bot library (async)
- Webhook mode (not polling) for production
- Per-organization bot instances (multi-tenant)
- Bot token stored per organization in database
- Background task queue for sending messages (so API doesn't block)

---

## Check-in System

- **Web-based PWA** for organizers (responsive, installable on phone)
- **QR scanner** via browser `getUserMedia`
- **Manual search** by name, email, or ticket code
- **Real-time** via WebSocket (Flask-SocketIO)
- **Offline mode**: IndexedDB cache, sync on reconnect
- **Check-in stats**: rate, total, remaining (dashboard widget)
- **Staff roles**: check-in operators scoped to specific events

---

## Waitlist

- Auto-enroll when event/ticket-type capacity is reached
- Auto-notify (via Telegram) next in line when a spot opens
- Claim window: 2 hours to claim the freed ticket
- Position tracking per ticket type

---

## Plugin System

- **Discovery**: `pyproject.toml` entry points under `tickets.plugins`
- **Hook interfaces**:
  - `tickets.payment_provider` -> `charge()`, `refund()`, `validate()`, `handle_webhook()`
  - `tickets.notification_channel` -> `send()`, `validate_config()`
  - `tickets.auth_provider` -> `authenticate()`, `get_login_url()`, `get_user_info()`
- Plugins are standalone Python packages installed via pip
- Plugin config UI in organization settings

---

## API Endpoints

```
Public (no auth):
  POST   /api/v1/auth/login
  POST   /api/v1/auth/register
  POST   /api/v1/auth/magic-link
  GET    /api/v1/events
  GET    /api/v1/events/<slug>
  POST   /api/v1/events/<slug>/order
  GET    /api/v1/tickets/<code>
  POST   /api/v1/tickets/<code>/check-in
  POST   /api/v1/tickets/link

Organizer (scoped to org):
  CRUD   /api/v1/org/events
  CRUD   /api/v1/org/events/<id>/ticket-types
  CRUD   /api/v1/org/events/<id>/seating
  GET    /api/v1/org/events/<id>/orders
  GET    /api/v1/org/events/<id>/waitlist
  GET    /api/v1/org/events/<id>/stats
  GET    /api/v1/org/check-in
  PUT    /api/v1/org/bot-config

Admin (super admin):
  CRUD   /api/v1/admin/organizations
  CRUD   /api/v1/admin/users
```

---

## Background Jobs (Redis + RQ)

| Job | Trigger |
|-----|---------|
| Send ticket card via Telegram | Order confirmed |
| Edit ticket card (event details changed) | Event updated |
| Send 24h reminder | Cron (every hour) |
| Send 1h reminder | Cron |
| Notify waitlist | Ticket cancelled |
| Generate QR code images | Order confirmed |
| Generate .ics calendar files | On demand |
| Cleanup expired link codes | Cron (daily) |

---

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── config.py              # Settings (env-based)
│   ├── extensions.py          # SQLAlchemy, migrate, Redis, RQ
│   ├── models/
│   │   ├── organization.py
│   │   ├── event.py
│   │   ├── ticket.py
│   │   ├── order.py
│   │   ├── attendee.py
│   │   └── waitlist.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── tickets.py
│   │   ├── checkin.py
│   │   ├── admin.py
│   │   └── bot_webhook.py
│   ├── services/
│   │   ├── order_service.py
│   │   ├── ticket_service.py
│   │   ├── checkin_service.py
│   │   ├── waitlist_service.py
│   │   └── telegram_bot.py
│   ├── tasks/
│   │   ├── telegram_tasks.py
│   │   ├── reminder_tasks.py
│   │   └── cleanup_tasks.py
│   ├── plugins/
│   │   ├── base.py
│   │   └── loader.py
│   └── utils/
│       ├── qr.py
│       ├── ics.py
│       └── telegram_helpers.py
├── migrations/                # Alembic
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│   services: api, worker, redis, db
└── .env.example

frontend/
├── src/
│   ├── pages/
│   │   ├── EventList.tsx
│   │   ├── EventDetail.tsx
│   │   ├── Checkout.tsx
│   │   ├── OrderConfirmation.tsx
│   │   ├── Dashboard.tsx
│   │   ├── ManageEvent.tsx
│   │   └── CheckIn.tsx
│   ├── components/
│   ├── hooks/
│   ├── services/              # API client
│   ├── stores/                # State management
│   └── utils/
├── vite.config.ts
├── Dockerfile
└── package.json
```

---

## Deferred Features (not in v1)

- Paid tickets (v2 via payment plugin)
- Email notifications (v2 via email plugin)
- Analytics dashboard
- Discount codes
- Ticket transfers
- Data export / CSV
- Virtual/hybrid events

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Telegram-first | Yes | Primary delivery for tickets + reminders; web is equal peer |
| Multi-tenant | Row-level isolation | Simpler than schema-per-tenant, good enough for scale |
| Guest checkout | Yes | Lower friction for attendees |
| QR code | SHA-256 hash | Unique per ticket, no PII in hash |
| WebSocket for check-in | Flask-SocketIO | Real-time updates without polling |
| RQ over Celery | Simpler | Enough for v1, can swap later |
| Local filesystem | Docker volume | Simple for self-hosted, can migrate to S3 later |
