import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.models import Base

_repo = Path(__file__).resolve().parents[2]
load_dotenv(_repo / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lojistik_db")
REQUIRE_POSTGRES = os.getenv("REQUIRE_POSTGRES", "false").lower() == "true"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    if REQUIRE_POSTGRES:
        raise RuntimeError(f"PostgreSQL bağlantısı zorunlu ama kurulamadı: {e}") from e
    print(f"PostgreSQL'e bağlanılamadı, SQLite'a düşülüyor... Hata: {e}")
    DATABASE_URL = "sqlite:///sirketler.db"
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
