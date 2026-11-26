"""Database engine helpers."""

from sqlalchemy import Engine, create_engine

from youtube_mcp.database.models import Base


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine and ensure declared tables exist.

    This project currently creates tables from SQLAlchemy metadata at startup;
    no migration tool is configured yet.
    """
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return engine
