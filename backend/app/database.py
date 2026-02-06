"""
Database configuration and session management.
Sets up SQLAlchemy engine and session factory.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes to get database session.

    Yields:
        Database session that automatically closes after use.

    Example:
        @app.get("/employees")
        def get_employees(db: Session = Depends(get_db)):
            return db.query(Employee).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
