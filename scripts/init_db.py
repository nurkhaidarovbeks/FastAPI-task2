from sqlmodel import SQLModel, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)