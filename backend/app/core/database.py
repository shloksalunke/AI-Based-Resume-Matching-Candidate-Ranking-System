from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# SQLite requires check_same_thread=False for multithreaded web server workers
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a scoped database session per request
    and guarantees safe closure after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all defined database tables if they do not already exist, and migrates missing columns."""
    Base.metadata.create_all(bind=engine)
    
    # Lightweight SQLite schema migration for newly added columns
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "job_descriptions" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("job_descriptions")]
            if "core_skills" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE job_descriptions ADD COLUMN core_skills JSON DEFAULT '[]'"))

        if "match_results" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("match_results")]
            if "ai_summary" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE match_results ADD COLUMN ai_summary JSON DEFAULT NULL"))
            if "llm_score" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE match_results ADD COLUMN llm_score FLOAT DEFAULT NULL"))
            if "llm_analysis" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE match_results ADD COLUMN llm_analysis JSON DEFAULT NULL"))
    except Exception as exc:
        pass

