import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger("aqi_api")

db_url = settings.DATABASE_URL
engine = None

try:
    # Try connecting to primary database (e.g., PostgreSQL)
    temp_engine = create_engine(db_url, pool_pre_ping=True)
    with temp_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine = temp_engine
    logger.info(f"Database connected successfully to primary store: {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    logger.warning(f"Primary database connection failed ({e}). Falling back to local SQLite database: sqlite:///./app.db")
    db_url = "sqlite:///./app.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
