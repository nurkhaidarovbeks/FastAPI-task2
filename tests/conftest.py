import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(file), "..")))

from main import app
from database import get_session
from models import User, Note
from security import get_password_hash

test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})

def override_get_session():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture()
def test_user():
    with Session(test_engine) as session:
        user = session.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(
                username="testuser",
                password=get_password_hash("testpassword"),
                role="user"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user