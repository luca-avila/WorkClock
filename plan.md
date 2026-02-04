# WorkClock Implementation Plan

## Executive Summary

Building an employee time-tracking system for 20-100 employees with:
- **Kiosk interface** for clock-in/out using 4-digit PINs
- **Admin dashboard** for employee management and shift reporting
- **Fixed daily rate** payment model (not hourly)
- **5 core invariants** ensuring data integrity
- **1-month timeline** for balanced MVP deployment

## Requirements Summary

### Deployment & Scale
- Cloud VPS (DigitalOcean, AWS EC2)
- 20-100 employees (medium scale)
- Single tenant
- Keep all data indefinitely

### Key Product Decisions
- **Shift handling**: Unlimited shift length (admin fixes forgotten clock-outs)
- **Payment**: `daily_rate` = fixed payment per shift (regardless of hours worked)
- **Kiosk UI**: English only, standard accessibility
- **Security**: HTTPS + JWT (admin) + 4-digit PIN codes (employees)
- **Reporting**: Raw shift list + monthly payment totals
- **Backups**: Manual only (no automated scripts in MVP)

### Tech Stack
- **Frontend**: React (Vite) + CSS
- **Backend**: FastAPI + PostgreSQL
- **Auth**: JWT for Admin, 4-digit PIN for Employees
- **Infra**: Docker + Nginx reverse proxy
- **Testing**: pytest for backend unit tests
- **Config**: .env files

---

## Project Structure

```
WorkClock/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Settings from .env
│   │   ├── database.py                # SQLAlchemy setup
│   │   ├── dependencies.py            # Auth & DB session deps
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── admin_user.py
│   │   │   ├── employee.py
│   │   │   ├── time_entry.py
│   │   │   └── shift.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── auth.py
│   │   │   ├── employee.py
│   │   │   ├── time_entry.py
│   │   │   └── shift.py
│   │   ├── routers/                   # API endpoints
│   │   │   ├── auth.py               # POST /auth/login
│   │   │   ├── kiosk.py              # POST /kiosk/clock
│   │   │   ├── employees.py          # Employee CRUD
│   │   │   └── shifts.py             # Shift reports
│   │   ├── services/                  # Business logic
│   │   │   ├── auth_service.py       # JWT creation/validation
│   │   │   ├── clock_service.py      # CORE: Clock-in/out + shift creation
│   │   │   ├── employee_service.py   # Employee CRUD
│   │   │   └── shift_service.py      # Read-only shift queries
│   │   └── utils/
│   │       └── security.py           # Password hashing, JWT
│   ├── tests/
│   │   ├── conftest.py               # pytest fixtures
│   │   └── test_invariants.py        # Test 5 core rules ONLY (MVP scope)
│   ├── alembic/                       # Database migrations
│   ├── scripts/
│   │   └── create_admin.py           # Initial admin user
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx                   # Routing
│   │   ├── api/
│   │   │   ├── client.js             # Axios + JWT interceptor
│   │   │   ├── auth.js
│   │   │   ├── employees.js
│   │   │   ├── kiosk.js
│   │   │   └── shifts.js
│   │   ├── components/
│   │   │   ├── common/               # Button, Input, Table, etc.
│   │   │   ├── admin/                # Employee & shift mgmt
│   │   │   └── kiosk/                # PinPad, ClockDisplay
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── KioskPage.jsx         # Main kiosk UI
│   │   │   ├── EmployeesPage.jsx
│   │   │   └── ShiftsPage.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   └── styles/
│   │       ├── kiosk.css
│   │       └── admin.css
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── .env.example
├── nginx/
│   ├── nginx.conf                     # Reverse proxy config
│   └── ssl/                          # SSL certificates (not in git)
├── docker-compose.yml                 # Single file for dev & prod
├── .gitignore
├── README.md
├── DEPLOYMENT.md
└── LICENSE
```

---

## Database Schema

### Conceptual Model

**Key Distinction:**
- **time_entries** = Immutable history (append-only log of all clock events)
- **shifts** = Derived state (calculated from IN→OUT pairs, represents completed work periods)

The system maintains a complete audit trail via time_entries, while shifts provide the business view for reporting and payroll.

### Core Tables

**admin_users**
```sql
id SERIAL PRIMARY KEY
email VARCHAR(255) UNIQUE NOT NULL
hashed_password VARCHAR(255) NOT NULL
role VARCHAR(50) NOT NULL DEFAULT 'admin'
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```

**employees**
```sql
id SERIAL PRIMARY KEY
name VARCHAR(255) NOT NULL
job_role VARCHAR(255) NOT NULL
daily_rate DECIMAL(10, 2) NOT NULL CHECK (daily_rate >= 0)
clock_code CHAR(4) UNIQUE NOT NULL CHECK (clock_code ~ '^[0-9]{4}$')
is_active BOOLEAN NOT NULL DEFAULT true
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```
- Unique index on `clock_code` WHERE `is_active = true` (allows reuse after deactivation)

**time_entries** (immutable)
```sql
id SERIAL PRIMARY KEY
employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT
type VARCHAR(3) NOT NULL CHECK (type IN ('IN', 'OUT'))
timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```
- Composite index on `(employee_id, timestamp DESC)` for fast lookups

**shifts**
```sql
id SERIAL PRIMARY KEY
employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT
clock_in_id INTEGER UNIQUE NOT NULL REFERENCES time_entries(id) ON DELETE RESTRICT
clock_out_id INTEGER UNIQUE NOT NULL REFERENCES time_entries(id) ON DELETE RESTRICT
started_at TIMESTAMP NOT NULL
ended_at TIMESTAMP NOT NULL CHECK (ended_at > started_at)
money_gained DECIMAL(10, 2) NOT NULL CHECK (money_gained >= 0)
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
```
- Composite index on `(employee_id, started_at DESC)` for reporting
- `money_gained` stores the employee's `daily_rate` at shift creation time

---

## Core Business Logic: The 5 Invariants

**CRITICAL**: These rules are the foundation of the system and must be enforced:

1. **Clock code uniqueness**: A clock code maps to exactly one active employee
2. **No double actions**: An employee cannot clock in twice or clock out without clocking in
3. **One open shift**: An employee can have only one open shift at a time
4. **Immutable entries**: Time entries can never be updated or deleted
5. **Valid pairs only**: Shifts are created only from valid IN → OUT pairs

### Implementation: ClockService

**File**: `/backend/app/services/clock_service.py`

**CRITICAL**: All shift creation logic lives in ClockService. No separate shift service for creation.

```python
class ClockService:
    def __init__(self, db: Session):
        self.db = db

    def process_clock_action(self, clock_code: str) -> tuple[TimeEntry, str]:
        """
        Single atomic operation for clock-in/out with shift creation.

        Database transaction ensures:
        - TimeEntry and Shift are created atomically (both or neither)
        - No race conditions from concurrent clock attempts
        - Rollback on any error (no partial state)

        Returns: (time_entry, action_type) where action_type is 'IN' or 'OUT'
        """
        try:
            # 1. Validate clock code → get active employee (Invariant 1)
            employee = self._get_active_employee(clock_code)

            # 2. Check last time entry to determine next action (Invariants 2 & 3)
            last_entry = self._get_last_time_entry(employee.id)
            next_action = 'OUT' if (last_entry and last_entry.type == 'IN') else 'IN'

            # 3. Create time entry (Invariant 4: immutable, append-only)
            time_entry = TimeEntry(
                employee_id=employee.id,
                type=next_action,
                timestamp=datetime.utcnow()
            )
            self.db.add(time_entry)
            self.db.flush()  # Get ID for shift reference

            # 4. If OUT, create shift (Invariant 5: valid IN→OUT pair)
            #    Shift is state derived from time_entry history
            if next_action == 'OUT':
                shift = Shift(
                    employee_id=employee.id,
                    clock_in_id=last_entry.id,
                    clock_out_id=time_entry.id,
                    started_at=last_entry.timestamp,
                    ended_at=time_entry.timestamp,
                    money_gained=employee.daily_rate  # Fixed rate, not hourly
                )
                self.db.add(shift)

            # 5. Atomic commit: both TimeEntry and Shift (if applicable) succeed together
            self.db.commit()
            return (time_entry, next_action)

        except Exception:
            self.db.rollback()
            raise
```

**Key Design Principles:**
- **Atomicity**: Database transaction wraps entire operation (TimeEntry + Shift creation)
- **Single responsibility**: ClockService owns ALL clock-in/out logic including shift creation
- **No separate shift creation**: Shifts are always created as part of clock-out action
- **Immutable history**: TimeEntry is append-only, never updated
- **Derived state**: Shift records are computed from TimeEntry pairs

---

## API Endpoints

### Auth
```
POST /auth/login
Request:  { email: string, password: string }
Response: { access_token: string, token_type: "bearer" }
```

### Kiosk
```
POST /kiosk/clock
Request:  { clock_code: string }
Response: {
  action: "IN" | "OUT",
  employee_name: string,
  timestamp: string (ISO 8601)
}
Status: 200 OK, 400 Bad Request (invalid code)
```

### Employees (Admin only)
```
GET    /employees?is_active=true
POST   /employees
PATCH  /employees/{id}

Employee Schema:
{
  id: number,
  name: string,
  job_role: string,
  daily_rate: number,
  clock_code: string (4 digits),
  is_active: boolean,
  created_at: string
}
```

### Shifts (Admin only)
```
GET /shifts
Query params: ?employee_id={id}&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=50&offset=0
Response: { shifts: Shift[], total: number }

GET /shifts/monthly-report
Query params: ?year=2026&month=2
Response: {
  month: "2026-02",
  employees: [
    {
      employee_id: number,
      employee_name: string,
      total_shifts: number,
      total_payment: number
    }
  ],
  grand_total: number
}
```

---

## Frontend Architecture

### Routing
```
/kiosk              → KioskPage (public, full-screen)
/login              → LoginPage (public)
/admin/employees    → EmployeesPage (protected)
/admin/shifts       → ShiftsPage (protected)
/                   → Redirect to /admin/employees
```

### Key Components

**KioskPage.jsx** (Most critical user-facing UI)
- Full-screen, touch-friendly interface
- Real-time clock display
- 3x4 numeric keypad (1-9, 0, Clear, Enter)
- Large status messages:
  - Success (green): "Welcome John! Clocked IN at 08:32"
  - Error (red): "Invalid code - please try again"
- Auto-clear PIN after 5 seconds
- No navigation to admin (separate URL path)

**EmployeesPage.jsx**
- Table: Name, Job Role, Daily Rate, Clock Code, Status, Actions
- Add Employee button → modal form
- Edit/Deactivate actions
- Form validation:
  - Clock code: 4 digits, unique
  - Daily rate: > 0
  - Required fields: name, job_role, daily_rate

**ShiftsPage.jsx**
- Filters: Employee dropdown, Date range picker
- Table: Employee, Clock In, Clock Out, Duration, Payment
- Monthly Report section:
  - Month/Year selector
  - Calculate button
  - Results: Employee-wise totals + Grand Total
  - Optional: Export to CSV

### State Management
- **Auth**: Context API + localStorage for JWT
- **Data fetching**: Direct API calls with React hooks (no Redux needed)
- **Forms**: Local component state

---

## Docker Setup

### Single docker-compose.yml (Development & Production)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-workclock}
      POSTGRES_USER: ${POSTGRES_USER:-workclock}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-dev_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U workclock"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    command: ${BACKEND_COMMAND:-uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload}
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql://workclock:dev_password@postgres/workclock}
      SECRET_KEY: ${SECRET_KEY:-dev_secret_key_change_in_production}
      BACKEND_CORS_ORIGINS: ${BACKEND_CORS_ORIGINS:-["http://localhost:5173"]}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build: ./frontend
    command: ${FRONTEND_COMMAND:-npm run dev -- --host}
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
    ports:
      - "5173:5173"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    profiles:
      - production

volumes:
  postgres_data:
```

**Usage:**

Development (default):
```bash
docker-compose up
# Access at http://localhost:5173
```

Production (with nginx):
```bash
docker-compose --profile production up -d
# Access at https://workclock.example.com
```

**Environment Variables:**
- Development: Uses defaults in docker-compose.yml
- Production: Create `.env` file with production values (not in git)

### Nginx Configuration
```nginx
server {
  listen 443 ssl http2;
  server_name workclock.example.com;

  ssl_certificate /etc/nginx/ssl/cert.pem;
  ssl_certificate_key /etc/nginx/ssl/key.pem;

  # Frontend (React SPA)
  location / {
    proxy_pass http://frontend;
  }

  # Backend API
  location /api/ {
    rewrite ^/api/(.*) /$1 break;
    proxy_pass http://backend:8000;
  }
}
```

---

## Implementation Timeline (4 Weeks)

### Week 1: Foundation & Setup (Days 1-7)
**Goal**: Authenticated admin can log in, database is running

- Day 1-2: Project scaffolding, Docker setup, .gitignore, README skeleton
- Day 3-4: Database schema, SQLAlchemy models, Alembic migrations
- Day 5-6: Auth system (JWT, password hashing, /auth/login endpoint)
- Day 7: Frontend setup, AuthContext, LoginPage, test login flow

**Deliverable**: Admin can log in via web UI, database is initialized

---

### Week 2: Core Clock Logic (Days 8-14)
**Goal**: Backend enforces all 5 invariants, admin can manage employees

- Day 8-9: Employee model, CRUD endpoints, validation
- Day 10-11: TimeEntry model, Shift model, ClockService implementation (all clock logic + shift creation in one service)
- Day 12-13: /kiosk/clock endpoint, test atomicity, invariant enforcement
- Day 14: Write tests/test_invariants.py (all 5 invariants), EmployeesPage UI

**Critical**:
- ClockService is the ONLY place that creates shifts
- ShiftService is read-only (queries for reporting)
- All 5 invariants must pass tests before moving to Week 3

**Deliverable**: Complete backend with tested invariants, employee management UI

---

### Week 3: User Interfaces (Days 15-21)
**Goal**: Fully functional kiosk and shift reporting

- Day 15-16: Kiosk UI design (full-screen, keypad, status messages)
- Day 17-18: Kiosk integration with backend, error handling
- Day 19-20: ShiftsPage, shift list with filters, pagination
- Day 21: Monthly report endpoint + UI, payment calculations

**User Testing**: Test kiosk on tablet/touch screen

**Deliverable**: Complete user-facing features (kiosk + admin dashboard)

---

### Week 4: Polish, Testing & Deployment (Days 22-30)
**Goal**: Production-ready app deployed on VPS

- Day 22-23: Error handling, validation, loading states, edge cases
- Day 24-25: Unit tests (pytest), manual QA, bug fixes
- Day 26-27: Documentation (README, DEPLOYMENT.md, code comments)
- Day 28-29: Production Docker setup, nginx config, SSL certificates
- Day 30: VPS deployment, end-to-end testing, user training

**Deliverable**: Live application on VPS with HTTPS, comprehensive docs

---

## Testing Strategy

### Backend Unit Tests (pytest)

**MVP Scope**: Test only the 5 core invariants (`tests/test_invariants.py`)

```python
def test_invariant_1_clock_code_unique():
    """Clock code maps to exactly one active employee"""
    # Create employee with code 1234
    # Attempt duplicate code - should fail
    # Deactivate first employee, create new with same code - should succeed

def test_invariant_2_no_double_clock_in():
    """Cannot clock in twice without clock out"""
    # Clock IN twice - second should be OUT, not second IN

def test_invariant_3_one_open_shift():
    """Only one open shift allowed per employee"""
    # After IN, verify no shift exists (open state)
    # After OUT, verify exactly one shift created
    # After second IN, verify still only one closed shift

def test_invariant_4_time_entries_immutable():
    """TimeEntry has no update methods"""
    # Verify TimeEntry service/model has no update operations
    # Attempt to modify existing entry - should fail

def test_invariant_5_shifts_from_valid_pairs():
    """Shifts only created from IN→OUT pairs"""
    # Verify shift created only on OUT action
    # Verify shift references correct IN and OUT entries
    # Verify money_gained equals employee daily_rate at shift creation
```

**Post-MVP**: Add business logic and integration tests as needed

### Frontend Testing
- **Manual testing only for MVP**
- Checklist: Login, employee CRUD, kiosk clock-in/out, shift reports, monthly calculations
- Test on actual kiosk device (tablet/touch screen)

---

## Deployment to VPS

### VPS Requirements
- 2 CPU cores, 4 GB RAM, 50 GB SSD
- Ubuntu 22.04 LTS
- Providers: DigitalOcean ($24/mo), AWS EC2 t3.medium, Linode

### Deployment Steps
```bash
# 1. Server setup
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install docker-compose -y

# 2. Clone repository
git clone <repo-url>
cd WorkClock

# 3. Configure environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit .env files with production values

# 4. SSL certificate (Let's Encrypt)
certbot certonly --standalone -d workclock.example.com
cp /etc/letsencrypt/live/workclock.example.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/workclock.example.com/privkey.pem nginx/ssl/key.pem

# 5. Create .env for production
cat > .env <<EOF
POSTGRES_PASSWORD=<strong-password>
SECRET_KEY=<strong-secret-key-32-chars>
DATABASE_URL=postgresql://workclock:<strong-password>@postgres/workclock
BACKEND_CORS_ORIGINS=["https://workclock.example.com"]
VITE_API_URL=https://workclock.example.com/api
BACKEND_COMMAND=uvicorn app.main:app --host 0.0.0.0 --port 8000
FRONTEND_COMMAND=nginx -g 'daemon off;'
EOF

# 6. Deploy with production profile
docker-compose --profile production up -d --build

# 7. Database setup
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/create_admin.py --email admin@example.com --password SecurePass123

# 8. Firewall
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### Backup Process (Manual)
```bash
# Backup database
docker-compose exec postgres pg_dump -U workclock workclock > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260204.sql | docker-compose exec -T postgres psql -U workclock
```

**Schedule**: Daily backups during initial weeks, weekly once stable

---

## Critical Files to Implement First

1. **backend/app/services/clock_service.py** - Core business logic: clock-in/out + shift creation (all 5 invariants enforced here)
2. **backend/app/models/time_entry.py** - Immutable time entry model (append-only history)
3. **backend/app/models/shift.py** - Shift model (derived state from time_entries)
4. **backend/app/routers/kiosk.py** - Kiosk endpoint (delegates to ClockService)
5. **tests/test_invariants.py** - Test all 5 invariants before building UI
6. **frontend/src/pages/KioskPage.jsx** - Main kiosk UI (after backend is solid)
7. **docker-compose.yml** - Single file for dev & prod

**Note**: ShiftService is read-only (queries only). All shift creation happens in ClockService.

---

## Security Considerations

- **JWT**: Strong SECRET_KEY (32+ chars), 8-hour expiration, HTTPS-only
- **Passwords**: Bcrypt hashing with salt, min 8 characters
- **Clock codes**: 4-digit PIN (9000 combinations, acceptable for 100 employees)
- **Database**: Prepared statements via SQLAlchemy (SQL injection prevention)
- **CORS**: Whitelist production frontend domain only
- **HTTPS**: Nginx redirects HTTP→HTTPS, Let's Encrypt SSL

---

## Edge Cases & Error Handling

### Edge Cases
1. **Overnight shifts**: Allowed (unlimited shift length per requirements)
2. **Code changed during open shift**: Prevent or warn admin
3. **Employee deactivated with open shift**: Block deactivation, show error
4. **System downtime**: TimeEntry creation is atomic, can retry

### Error Responses
```json
{
  "detail": "Human-readable message",
  "error_code": "INVALID_CLOCK_CODE",
  "timestamp": "2026-02-04T10:30:00Z"
}
```

**Status codes**:
- 400: Invalid input
- 401: Unauthorized
- 404: Not found
- 409: Conflict (e.g., duplicate clock code)
- 500: Internal error (logged, generic message)

---

## Documentation Structure

### README.md
- Project overview and features
- Tech stack
- Quick start (Docker setup)
- Development guide
- Project structure
- License

### DEPLOYMENT.md
- VPS requirements
- Server setup (Docker, firewall)
- Application deployment
- SSL certificate setup
- Backup procedures
- Troubleshooting

### Code Documentation
- Docstrings for all service methods (Google style)
- Inline comments for invariant logic
- API endpoint descriptions (auto-generated via FastAPI /docs)

---

## Future Enhancements (Post-MVP)

Not in 1-month timeline, consider for Phase 2:
1. Audit logs for admin actions
2. Rate limiting on kiosk endpoint
3. Employee self-service portal
4. Export to CSV/PDF
5. Dashboard with charts
6. Multi-language kiosk
7. Automated backups with retention
8. Email notifications
9. Mobile app (iOS/Android)
10. Hardware integration (RFID, fingerprint)

---

## Success Criteria

The MVP is complete when:
- ✅ All 5 core invariants are enforced and tested
- ✅ Kiosk allows clock-in/out with 4-digit PIN
- ✅ Admin can manage employees (create, edit, deactivate)
- ✅ Admin can view shifts and calculate monthly payments
- ✅ Application deployed on VPS with HTTPS
- ✅ Documentation allows maintenance by intermediate developer
- ✅ No critical bugs in core workflows
- ✅ User acceptance complete

---

## Implementation Checklist

### Pre-Development
- [ ] Review and approve this plan
- [ ] Set up development environment (Docker, Git)
- [ ] Create VPS account
- [ ] Configure domain name

### Week 1: Foundation ✓
- [ ] Directory structure + Git
- [ ] Docker Compose (dev)
- [ ] Database schema + models
- [ ] Authentication (JWT)
- [ ] Login UI

### Week 2: Core Logic ✓
- [ ] Employee CRUD
- [ ] ClockService + invariants
- [ ] Kiosk clock endpoint
- [ ] Invariant tests
- [ ] Employee management UI

### Week 3: UI ✓
- [ ] Kiosk UI (full-screen keypad)
- [ ] Kiosk integration
- [ ] Shift reporting UI
- [ ] Monthly report calculation

### Week 4: Launch ✓
- [ ] Error handling + validation
- [ ] Unit tests (backend)
- [ ] Documentation (README, DEPLOYMENT)
- [ ] Production Docker + nginx
- [ ] VPS deployment + SSL
- [ ] End-to-end testing
- [ ] User training

---

## Verification Plan

After implementation, verify:

1. **Invariants**: Run `pytest tests/test_invariants.py` - all 5 must pass
2. **Kiosk flow**:
   - Valid PIN → Clock IN → Success message
   - Same PIN → Clock OUT → Shift created
   - Invalid PIN → Error message
3. **Admin flow**:
   - Create employee with clock code 1234
   - Edit employee daily rate
   - View shifts for employee
   - Calculate monthly payment total
4. **Production**:
   - HTTPS working (no certificate errors)
   - Admin login from remote device
   - Kiosk working on tablet
   - Database persists after container restart

---

**End of Plan**
