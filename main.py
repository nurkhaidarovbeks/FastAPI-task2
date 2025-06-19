from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlmodel import Session, select
from models import User
from schemas import UserLogin, UserCreate
from database import create_db_and_tables, get_session
from contextlib import asynccontextmanager
from security import get_password_hash, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access__token

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
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access__token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
