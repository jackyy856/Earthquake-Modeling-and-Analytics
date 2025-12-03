#db connection and utilities
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Optional

from sqlmodel import SQLModel, Session, create_engine

BASE_DIR = Path(__file__).resolve().parent.parent  # project-root/
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = DB_DIR / "earthquakes.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH))).resolve()

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},  # sqlite + fastapi threads
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def reset_db_file() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
