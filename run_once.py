from sqlmodel import Session, select
from database import engine
from models import User
from security import get_password_hash

with Session(engine) as session:
    users = session.exec(select(User)).all()
    for user in users:
        if not user.password.startswith("$2b$"):
            user.password = get_password_hash(user.password)
            session.add(user)
    session.commit()