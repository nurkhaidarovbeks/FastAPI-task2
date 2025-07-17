import json
from fastapi import FastAPI, Depends, HTTPException, status, Response, Query, WebSocket, WebSocketDisconnect, APIRouter
from sqlmodel import Session, select
from models import User, Note
from schemas import NoteOut, NoteCreate, NoteUpdate, UserCreate, UserLogin
from database import create_db_and_tables, get_session
from auth import create_access__token
from contextlib import asynccontextmanager
from dependencies import get_current_user, require_role
from security import get_password_hash, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from tasks import send_mock_email
from typing import List
from redis import startup as redis_startup, shutdown as redis_shutdown, get_redis

router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_startup()
    create_db_and_tables()
    yield
    await redis_shutdown()

app = FastAPI(lifespan=lifespan)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password=hashed_password,
        role="user"
    )

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

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username
    }

@app.get("/admin/users")
def list_all_users(current_user: User = require_role("admin"), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]

@app.post("/notes", response_model=NoteOut)
async def create_note(note_data: NoteCreate, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user),
                redis = Depends(get_redis)):
    note = Note(text=note_data.text, owner_id=current_user.id)
    session.add(note)
    session.commit()
    session.refresh(note)
    keys = await redis.keys(f"notes:{current_user.id}:*")
    if keys:
        await redis.delete(*keys)
    return note

@app.get("/notes", response_model=list[NoteOut])
async def get_my_notes(skip: int = 0,
                       limit: int = 100,
                       search: str | None = None,
                       session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_user),
                       redis=Depends(get_redis)):

    cache_key = f"notes:{current_user.id}:{skip}:{limit}:{search or ''}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    query = select(Note).where(Note.owner_id == current_user.id)
    if search:
        query = query.where(Note.text.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    notes = session.exec(query).all()
    await redis.set(cache_key, json.dumps([note.dict() for note in notes]), ex=300)
    return notes

@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, session: Session = Depends(get_session),
             current_user: User = Depends(get_current_user)):
    note = session.get(Note, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: int, note_update: NoteUpdate, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user),
                redis = Depends(get_redis)):
    note = session.get(Note, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_update.text is not None:
        note.text = note_update.text
    session.add(note)
    session.commit()
    session.refresh(note)
    keys = await redis.keys(f"notes:{current_user.id}:*")
    if keys:
        await redis.delete(*keys)

    return note

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user),
                      redis = Depends(get_redis)):
    note = session.get(Note, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    session.delete(note)
    session.commit()

    keys = await redis.keys(f"notes:{current_user.id}:*")
    if keys:
        await redis.delete(*keys)

    return {"detail": "Note deleted"}


@app.post("/trigger-task")
def trigger_task():
    send_mock_email.delay("user@example")
    return {"message": "Task started"}