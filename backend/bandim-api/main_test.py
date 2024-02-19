from fastapi.testclient import TestClient
import uuid
from database import engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from main import app
import pytest
from routers import public

# def get_session():
#     with Session(engine) as session:
#         yield session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[public.get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def create_dataset(client: TestClient, dataset_name):
    req = {
        "name": dataset_name,
        "locations": [
            {
                "latitude": 11.85345134655994,
                "longitude": -15.598089853772322,
            },
            {
                "latitude": 11.84812109448719,
                "longitude": -15.600460066985532,
            },
        ],
    }
    response = client.post(
        "/api/public/datasets/",
        json=req,
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    assert "name" in res
    assert "locations" in res
    assert "uid" in res["locations"][0]
    assert "uid" in res["locations"][1]
    assert "created_at" in res
    assert "updated_at" in res
    return res


def test_create_dataset_populated(client: TestClient):
    res = create_dataset(client=client, dataset_name="Random Dataset 0")


def test_create_dataset_empty(client: TestClient):
    req = {
        "name": "Random Dataset 1",
        "locations": [],
    }
    response = client.post(
        "/api/public/datasets/",
        json=req,
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    assert "name" in res
    assert "locations" in res
    assert "created_at" in res
    assert "updated_at" in res


def test_create_route(client: TestClient):
    res = create_dataset(client=client, dataset_name="Random Dataset 2")
