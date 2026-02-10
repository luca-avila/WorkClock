# WorkClock

Employee time-tracking system with kiosk interface for 20-100 employees.

## Status

✅ **MVP Complete** - Fully functional with comprehensive testing (48/48 tests passing)

## Features

- **Kiosk Interface**: Touch-friendly clock-in/out using 4-digit PIN codes
- **Admin Dashboard**: Employee management and shift reporting with real-time updates
- **Fixed Daily Rate**: Payment model based on daily rate (not hourly)
- **Data Integrity**: 5 core invariants ensuring system reliability
- **Comprehensive Testing**: 48 tests covering all endpoints and business logic
- **Modern UI**: React frontend with Toast notifications and loading states
- **Secure**: JWT authentication for admins, PIN codes for employees
- **Docker-Ready**: Containerized for easy deployment

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Reliable relational database
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **JWT**: Admin authentication
- **pytest**: Testing framework

### Frontend
- **React**: UI framework
- **Vite**: Fast build tool
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **CSS**: Styling (no framework needed)

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy (production)
- **Let's Encrypt**: SSL certificates (production)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Development Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd WorkClock
```

2. Start the services:
```bash
docker-compose up
```

3. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Initial Setup

1. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

2. Create admin user:
```bash
docker-compose exec backend python scripts/create_admin.py
```

3. Log in to the admin dashboard at http://localhost:5173/login

## Project Structure

```
WorkClock/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── utils/       # Utilities
│   ├── tests/           # pytest tests
│   ├── scripts/         # Helper scripts
│   └── alembic/         # Database migrations
├── frontend/            # React application
│   └── src/
│       ├── api/         # API client
│       ├── components/  # React components
│       ├── pages/       # Page components
│       ├── context/     # React context
│       └── styles/      # CSS files
├── nginx/               # Nginx configuration
└── docker-compose.yml   # Docker orchestration
```

## Core Business Logic

The system enforces 5 critical invariants:

1. **Clock code uniqueness**: Each 4-digit code maps to exactly one active employee
2. **No double actions**: Employees cannot clock in twice or clock out without clocking in
3. **One open shift**: Only one unclosed shift allowed per employee at a time
4. **Immutable entries**: Time entries are append-only, never modified
5. **Valid pairs only**: Shifts created only from valid clock-in → clock-out pairs

## API Endpoints

### Authentication
- `POST /auth/login` - Admin login (returns JWT)

### Kiosk (Public)
- `POST /kiosk/clock` - Clock in/out with PIN code

### Employees (Admin only)
- `GET /employees` - List employees (with optional is_active filter)
- `POST /employees` - Create employee
- `GET /employees/{id}` - Get employee by ID
- `PATCH /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Deactivate employee (soft delete)

### Shifts (Admin only)
- `GET /shifts` - List shifts with filters (employee, date range, pagination)
- `GET /shifts/monthly-report` - Monthly payment report by employee

## Development Guide

### Running Tests

```bash
# All backend tests (48 tests)
docker compose exec backend pytest

# Specific test files
docker compose exec backend pytest tests/test_invariants.py -v
docker compose exec backend pytest tests/test_employees.py -v
docker compose exec backend pytest tests/test_kiosk.py -v

# With coverage
docker compose exec backend pytest --cov=app tests/
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### Environment Variables

Copy the example files and customize:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

See `.env.example` files for available configuration options.

## Production Deployment

### Quick Deploy

```bash
# 1. Clone repository
git clone <repo-url>
cd WorkClock

# 2. Set environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit .env files with production values

# 3. Start services
docker compose up -d

# 4. Run migrations
docker compose exec backend alembic upgrade head

# 5. Create admin user
docker compose exec backend python scripts/create_admin.py
```

### Production Checklist
- Use strong SECRET_KEY in backend/.env
- Set proper DATABASE_URL with secure password
- Configure CORS origins for your domain
- Set up SSL/HTTPS (recommended: nginx + Let's Encrypt)
- Configure regular database backups
- Review and harden firewall rules

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is a single-tenant application. For feature requests or bugs, please open an issue.

## Support

For documentation and troubleshooting, see:
- API documentation: http://localhost:8000/docs (when running)
- [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- [plan.md](plan.md) for implementation details
