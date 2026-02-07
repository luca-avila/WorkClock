# Week 1 Complete - Testing Guide

## What Was Accomplished

### Backend (Days 1-6)
✅ Project structure with Docker
✅ PostgreSQL database with async SQLAlchemy
✅ 4 database models (AdminUser, Employee, TimeEntry, Shift)
✅ Alembic migrations setup
✅ JWT authentication system
✅ Password hashing with bcrypt
✅ `/auth/login` endpoint
✅ Admin creation script

### Frontend (Day 7)
✅ React + Vite setup
✅ React Router for navigation
✅ Axios API client with JWT interceptor
✅ AuthContext for state management
✅ LoginPage with form validation
✅ Responsive CSS styling

---

## Testing the Login Flow

### Step 1: Start the Application

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Step 2: Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic revision --autogenerate -m "Create initial tables"
docker-compose exec backend alembic upgrade head

# Verify tables created
docker-compose exec postgres psql -U workclock -c "\dt"
# Should show: admin_users, employees, time_entries, shifts, alembic_version
```

### Step 3: Create Admin User

```bash
# Interactive mode
docker-compose exec backend python scripts/create_admin.py

# Or non-interactive
docker-compose exec backend python scripts/create_admin.py \
  --email admin@workclock.com \
  --password AdminPass123
```

### Step 4: Test Backend API

```bash
# Test health endpoint
curl http://localhost:8000/health
# Response: {"status":"healthy"}

# Test login endpoint
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@workclock.com","password":"AdminPass123"}'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

### Step 5: Test Frontend

1. Open browser: http://localhost:5173
2. You should see the login page
3. Enter credentials:
   - Email: admin@workclock.com
   - Password: AdminPass123
4. Click "Login"
5. Check browser console (F12):
   - Should see successful login
   - Token stored in localStorage
6. Check Network tab:
   - POST request to /auth/login
   - Response with access_token

### Step 6: Verify Token Storage

```javascript
// Open browser console (F12) on http://localhost:5173
localStorage.getItem('token')
// Should show JWT token

// Check token expiration
const token = localStorage.getItem('token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('Token expires:', new Date(payload.exp * 1000))
// Should be 8 hours from creation
```

---

## API Documentation

FastAPI automatically generates interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try the login endpoint in Swagger UI:
1. Click on "POST /auth/login"
2. Click "Try it out"
3. Enter email and password
4. Click "Execute"
5. See the response with access_token

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: Wait for postgres healthcheck
# - Missing .env: Copy from .env.example
# - Port 8000 in use: Change port in docker-compose.yml
```

### Frontend won't start
```bash
# Check logs
docker-compose logs frontend

# Common issues:
# - Node modules not installed: Rebuild container
docker-compose up --build frontend

# - Port 5173 in use: Change port in docker-compose.yml
```

### Login fails with CORS error
```bash
# Check CORS settings in backend/.env
BACKEND_CORS_ORIGINS=["http://localhost:5173"]

# Restart backend after changing
docker-compose restart backend
```

### Login fails with 401
```bash
# Verify admin exists
docker-compose exec postgres psql -U workclock -c "SELECT * FROM admin_users;"

# Verify password (should see hashed password)
docker-compose exec postgres psql -U workclock -c "SELECT email, hashed_password FROM admin_users;"

# Try creating admin again
docker-compose exec backend python scripts/create_admin.py
```

### Database not initialized
```bash
# Check if migrations ran
docker-compose exec postgres psql -U workclock -c "SELECT * FROM alembic_version;"

# If empty, run migrations
docker-compose exec backend alembic upgrade head
```

---

## Next Steps (Week 2)

Now that authentication works, Week 2 will implement:

1. **ClockService** - Core business logic with 5 invariants
2. **Employee CRUD** - Create, read, update, deactivate employees
3. **Kiosk endpoint** - POST /kiosk/clock for clock-in/out
4. **Employee management UI** - Admin can manage employees
5. **Tests** - test_invariants.py for all 5 core rules

---

## Quick Reference

### Useful Commands

```bash
# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Rebuild and restart
docker-compose up -d --build [service]

# Database shell
docker-compose exec postgres psql -U workclock

# Backend shell
docker-compose exec backend bash

# Run Python script
docker-compose exec backend python scripts/[script].py

# Check running containers
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v
```

### Database Queries

```sql
-- View admin users
SELECT * FROM admin_users;

-- View employees (none yet, Week 2)
SELECT * FROM employees;

-- View time entries (none yet, Week 2)
SELECT * FROM time_entries;

-- View shifts (none yet, Week 2)
SELECT * FROM shifts;
```

---

## Week 1 Achievement Unlocked! 🎉

You now have:
- ✅ Fully functional authentication system
- ✅ Admin can log in via web UI
- ✅ JWT tokens working
- ✅ Database initialized and ready
- ✅ Frontend and backend connected
- ✅ Foundation ready for Week 2 business logic
