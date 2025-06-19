from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import Session, select
from models import User
from schemas import UserLogin, UserCreate
from database import create_db_and_tables, get_session
from contextlib import asynccontextmanager
from security import get_password_hash, verify_password

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, password=hashed_password)

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}

@app.post("/login")
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == user_data.username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"message": "Login successful", "username": user.username}
