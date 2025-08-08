import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import psycopg2
from psycopg2 import OperationalError
from time import sleep

from db.models import Base
from utl.logging import logger

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@db:5432/parserdb")

DATABASE_CONFIG = dict(
    dbname="parserdb",
    user="user",
    password="password",
    host="db",
    port=5432
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_db():
    max_tries = 10
    for i in range(max_tries):
        try:
            conn = psycopg2.connect(**DATABASE_CONFIG)
            conn.close()
            logger.info("Database is ready")
            return
        except OperationalError:
            logger.info(f"Waiting for database... ({i+1}/{max_tries})")
            sleep(3)
    raise RuntimeError("Database not available after waiting")
