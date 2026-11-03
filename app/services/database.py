
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.config import settings


# --------------------------------------------------
# 1. SQLAlchemy ORM Base
# --------------------------------------------------

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Future database models should inherit from Base.
    """
    pass


# --------------------------------------------------
# 2. Database Engine
# --------------------------------------------------
database_url = settings.database_url.get_secret_value()
def create_database_engine() -> Engine:
    """
    Create the central PostgreSQL engine.

    pool_pre_ping checks whether a pooled connection is
    still alive before SQLAlchemy uses it.
    """

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=settings.debug,
    )


engine = create_database_engine()


# --------------------------------------------------
# 3. Session Factory
# --------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# --------------------------------------------------
# 4. Database Session Dependency
# --------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session and always close it.

    Suitable for FastAPI dependency injection.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# 5. Context Manager for Non-FastAPI Services
# --------------------------------------------------

@contextmanager
def get_db_session():
    """
    Provide a session for service and repository code.

    Commits on success and rolls back on failure.
    """

    db = SessionLocal()

    try:
        yield db
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# --------------------------------------------------
# 6. Database Connectivity Check
# --------------------------------------------------

def check_database_connection() -> bool:
    """
    Check whether PostgreSQL is reachable.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except SQLAlchemyError:
        return False


# --------------------------------------------------
# 7. Database Initialisation
# --------------------------------------------------

def initialize_database() -> None:
    """
    Initialise application database tables.

    This creates ORM tables registered with Base.metadata.

    It does not create the pgvector knowledge table;
    that belongs to the vector-store initialisation process.
    """

    try:
        Base.metadata.create_all(bind=engine)

    except SQLAlchemyError:
        raise RuntimeError(
            "Could not initialise application database tables."
        )


# --------------------------------------------------
# 8. Database Shutdown
# --------------------------------------------------

def close_database_connections() -> None:
    """
    Dispose the SQLAlchemy connection pool during shutdown.
    """

    engine.dispose()
