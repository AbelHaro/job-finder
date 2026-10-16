"""SQLAlchemy connections to a local SQLite file."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE = Path(__file__).resolve().parents[3] / "jobs.sqlite3"


def database_url() -> URL:
    load_dotenv()
    configured = os.getenv("DATABASE_URL")
    if configured:
        url = make_url(configured)
        if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
            raise ValueError(
                "DATABASE_URL must use SQLite (sqlite:///path/to/jobs.sqlite3)"
            )
        return url
    return URL.create("sqlite", database=str(DEFAULT_DATABASE))


def get_engine() -> Engine:
    url = database_url()
    print(f"Connecting to database at {url.database}")
    return create_engine(url)


def session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=engine if engine is not None else get_engine())
