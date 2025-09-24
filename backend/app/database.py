from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - supports both SQLite (development) and PostgreSQL (production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./patients.db")

# Handle Railway/Heroku postgres URL format (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate settings for PostgreSQL vs SQLite
if DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Set to True for SQL debugging
    )
else:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    date_of_birth = Column(String, nullable=False, index=True)  # Store as string in YYYY-MM-DD format
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL - supports both SQLite (development) and PostgreSQL (production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./patients.db")

# Handle Railway/Heroku postgres URL format (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate settings for PostgreSQL vs SQLite
if DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL configuration for Supabase
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,      # Verify connections before use
        pool_recycle=3600,       # Recycle connections every hour
        pool_size=5,             # Connection pool size
        max_overflow=10,         # Max overflow connections
        echo=False               # Set to True for SQL debugging
    )
    print("🐘 Using PostgreSQL database (Supabase)")
else:
    # SQLite configuration (development fallback)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    print("📁 Using SQLite database (development mode)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_database():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables - ONLY for SQLite fallback"""
    # Skip table creation if using Supabase REST API
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        print("✅ Using Supabase REST API - tables already exist")
        return
    
    # Only create tables for SQLite fallback
    if not DATABASE_URL.startswith("postgresql://"):
        print("📋 Creating SQLite database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ SQLite database tables created successfully")
    else:
        print("⚠️ PostgreSQL detected - use Supabase dashboard to create tables")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
