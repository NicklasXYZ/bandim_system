from fastapi.testclient import TestClient
import uuid
import json
from database import engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from main import app
import pytest
from datetime import datetime, timedelta
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
    # Create error: Missing longitude coordinates
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


def create_workplan_succeed(client: TestClient, dataset_uid: str):
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=1)
    req = {
        "dataset_uid": dataset_uid,
        "start_time": str(start_time),
        "end_time": str(end_time),
        "workers": 3,
    }
    response = client.post(
        "/api/public/workplans/",
        json=req,
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    assert "start_time" in res
    assert "end_time" in res
    assert "workers" in res
    assert "dataset_uid" in res
    assert "updated_at" in res
    assert "routes" in res
    return res


def get_workplan_succeed(client: TestClient, workplan_uid: str):
    response = client.get(
        f"/api/public/workplans/{workplan_uid}",
    )
    assert response.status_code == 200
    res = response.json()
    assert "uid" in res
    assert "start_time" in res
    assert "end_time" in res
    assert "workers" in res
    assert "dataset_uid" in res
    assert "updated_at" in res
    assert "routes" in res
    return res


def test_all_succeed(client: TestClient):
    locations_res = create_bulk_locations_succeed(client=client)
    locations = [{"uid": str(loc["uid"])} for loc in locations_res]
    dataset_res = create_dataset_succeed(
        client, dataset_name="Random Dataset 0", locations=locations
    )
    get_dataset_succeed(
        client=client, dataset_uid=dataset_res["uid"], locations=locations
    )
    workplan_res = create_workplan_succeed(
        client=client, dataset_uid=dataset_res["uid"]
    )
    get_workplan_succeed(
        client=client,
        workplan_uid=workplan_res["uid"],
    )


def read_points_from_json(file_path):
    """
    Read geospatial locations from a JSON file.

    :param file_path: Path to the JSON file
    :return: List of dicts with 'latitude' and 'longitude' keys
    """
    with open(file_path, "r") as file:
        points = json.load(file)
    return points


def test_route_assignment(client: TestClient):
    # Load many locations
    file_path = "./random_geolocations.json"
    locations = read_points_from_json(file_path)

    # Bulk insert locatinos
    response = client.post(
        "/api/public/locations/bulk_insert",
        json=locations,
    )
    assert response.status_code == 200
    locations_res = response.json()
    locations = [{"uid": str(loc["uid"])} for loc in locations_res]

    # Associate the locations with a dataset
    req = {"name": "Random Dataset 1", "locations": locations}
    response = client.post(
        "/api/public/datasets/",
        json=req,
    )
    assert response.status_code == 200
    dataset_res = response.json()

    # Using the data set with added locations, create a workplan
    # for a number of workers
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=1)
    req = {
        "dataset_uid": dataset_res["uid"],
        "start_time": str(start_time),
        "end_time": str(end_time),
        "workers": 3,
    }
    response = client.post(
        "/api/public/workplans/",
        json=req,
    )
    assert response.status_code == 200
    workplan_res = response.json()

    # Assign routes and schedules for 3 workers

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=1)
    req = {
        "uid": workplan_res["uid"],
    }
    response = client.post(
        "/api/public/workplans/assign",
        json=req,
    )
    assert response.status_code == 200
    assignment = response.json()
    print(assignment)
    assert False
