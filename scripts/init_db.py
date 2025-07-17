import os
from sqlmodel import SQLModel, create_engine
from models import *

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)
print("Creating tables...")
SQLModel.metadata.create_all(engine)
print("Done.")