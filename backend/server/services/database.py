from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from pathlib import Path
from server.settings import DATABASE_PATHS
import logging

engines = {}

for db_key, db_path in DATABASE_PATHS.items():
    if not Path(db_path).exists():
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        open(db_path, 'a').close()
        logging.info(f"Created new database file at {db_path}")

    engines[db_key] = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False}, echo=False, future=True)

    @event.listens_for(engines[db_key], "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
SessionLocal = {db_key: sessionmaker(autocommit=False, autoflush=False, bind=engine) for db_key, engine in engines.items()}

def get_db(db_key: str):
    return SessionLocal[db_key]()