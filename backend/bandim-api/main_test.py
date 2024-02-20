from fastapi.testclient import TestClient
import uuid
from database import engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from main import app
import pytest
from routers import public


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


def create_bulk_locations_succeed(client: TestClient):
    req = [
        {
            "latitude": 11.85345134655994,
            "longitude": -15.598089853772322,
        },
        {
            "latitude": 11.84812109448719,
            "longitude": -15.600460066985532,
        },
    ]
    response = client.post(
        "/api/public/locations/bulk_insert",
        json=req,
    )
    assert response.status_code == 200
    res = response.json()
    assert len(res) == 2
    assert "uid" in res[0]
    assert "uid" in res[1]
    return res


def test_bulk_locations_succeed(client: TestClient):
    create_bulk_locations_succeed(client=client)


def test_create_bulk_locations_fail(client: TestClient):
    # Missing longitude coordinates
    req = [
        {
            "longitude": -15.598089853772322,
        },
        {
            "longitude": -15.600460066985532,
        },
    ]
    response = client.post(
        "/api/public/locations/bulk_insert",
        json=req,
    )
    assert response.status_code == 422


def create_location_succeed(client: TestClient):
    req = {
        "latitude": 11.85345134655994,
        "longitude": -15.598089853772322,
    }
    response = client.post(
        "/api/public/locations/",
        json=req,
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    return res


def get_location_succeed(client: TestClient, location_uid):
    response = client.get(
        f"/api/public/locations/{location_uid}",
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    assert "datasets" in res
    assert "depot" in res
    assert "routes" in res
    return res


def test_location_succeed(client: TestClient):
    res = create_location_succeed(client=client)
    get_location_succeed(client=client, location_uid=res["uid"])


def create_dataset_succeed(client: TestClient, dataset_name, locations):
    req = {"name": dataset_name, "locations": locations}
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


def get_dataset_succeed(client: TestClient, dataset_uid, locations):
    response = client.get(
        f"/api/public/datasets/{dataset_uid}",
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    assert "name" in res
    assert "locations" in res
    assert "uid" in res["locations"][0]
    assert "uid" in res["locations"][1]
    location_uids = [loc["uid"] for loc in res["locations"]]
    for location in locations:
        assert location["uid"] in location_uids
    assert "created_at" in res
    assert "updated_at" in res
    return res

def create_workplan_succeed(client: TestClient, dataset_uid, locations):
    req = {"name": dataset_name, "uid": locations}
    response = client.post(
        "/api/public/workplans/",
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


def test_create_dataset_succeed(client: TestClient):
    locations_res = create_bulk_locations_succeed(client=client)
    locations = [{"uid": str(loc["uid"])} for loc in locations_res]
    dataset_res = create_dataset_succeed(
        client, dataset_name="Random Dataset 1", locations=locations
    )
    get_dataset_succeed(
        client=client, dataset_uid=dataset_res["uid"], locations=locations
    )







# def test_create_locations_fail(client: TestClient):
#     req = [
#         {
#             "latitude": 11.85345134655994,
#             "longitude": ""
#         },
#     ]
#     response = client.post(
#         "/api/public/locations/",
#         json=req,
#     )
#     assert response.status_code == 200
#     print(response.json())
#     assert False
# res = response.json()
# assert "uid" in res
# assert "name" in res
# assert "locations" in res
# assert "uid" in res["locations"][0]
# assert "uid" in res["locations"][1]
# assert "created_at" in res
# assert "updated_at" in res
# return res


# def create_dataset(client: TestClient, dataset_name):
#     req = {
#         "name": dataset_name,
#         "locations": [
#             {
#                 "latitude": 11.85345134655994,
#                 "longitude": -15.598089853772322,
#             },
#             {
#                 "latitude": 11.84812109448719,
#                 "longitude": -15.600460066985532,
#             },
#         ],
#     }
#     response = client.post(
#         "/api/public/datasets/",
#         json=req,
#     )
#     assert response.status_code == 200
#     res = response.json()
#     assert "uid" in res
#     assert "name" in res
#     assert "locations" in res
#     assert "uid" in res["locations"][0]
#     assert "uid" in res["locations"][1]
#     assert "created_at" in res
#     assert "updated_at" in res
#     return res


# def test_create_dataset_populated(client: TestClient):
#     res = create_dataset(client=client, dataset_name="Random Dataset 0")


# def test_create_dataset_empty(client: TestClient):
#     req = {
#         "name": "Random Dataset 1",
#         "locations": [],
#     }
#     response = client.post(
#         "/api/public/datasets/",
#         json=req,
#     )
#     assert response.status_code == 200
#     res = response.json()
#     assert "uid" in res
#     assert "name" in res
#     assert "locations" in res
#     assert "created_at" in res
#     assert "updated_at" in res


# def test_create_route(client: TestClient):
#     res = create_dataset(client=client, dataset_name="Random Dataset 2")
