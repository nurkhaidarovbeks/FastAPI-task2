import os
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from config import settings

engine = create_engine(settings.database_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
