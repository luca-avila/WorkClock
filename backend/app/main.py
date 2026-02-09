"""
WorkClock FastAPI Application

Employee time-tracking system with kiosk interface and admin dashboard.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth_router, employees_router, kiosk_router

# Create FastAPI application
app = FastAPI(
    title="WorkClock API",
    description="Employee time-tracking system with kiosk interface for 20-100 employees",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(kiosk_router)


@app.get("/")
async def root():
    """
    Root endpoint - API health check.

    Returns:
        Basic API information
    """
    return {
        "name": "WorkClock API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Health status
    """
    return {"status": "healthy"}
