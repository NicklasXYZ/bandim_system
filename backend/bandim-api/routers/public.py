from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import insert

from pydantic import TypeAdapter
from database import engine
from models import (
    DataSet,
    DataSetCreate,
    DataSetReadCompact,
    DataSetReadDetails,
    DataSetUpdate,
    Location,
    LocationCreate,
    LocationReadCompact,
    LocationReadDetails,
    WorkPlan,
    WorkPlanRead,
    WorkPlanCreate,
    Identifier,
    Route,
    RouteRead,
    RouteCreate,
)
import uuid

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


@router.post("/locations/", response_model=LocationReadCompact, tags=["locations"])
async def create_location(
    *, session: Session = Depends(get_session), location: LocationCreate
):
    db_location = Location.model_validate(location)
    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return db_location


@router.post(
    "/locations/bulk_insert",
    response_model=list[LocationReadCompact],
    tags=["locations"],
)
async def create_locations(
    *, session: Session = Depends(get_session), locations: list[LocationCreate]
):
    db_locations = []
    for location in locations:
        db_location = Location.model_validate(location)
        db_locations.append(db_location)
    statement = insert(Location).returning(Location)
    results = session.scalars(statement, db_locations)
    session.flush()
    return results.all()


@router.get("/locations/", response_model=list[LocationReadCompact], tags=["locations"])
async def read_locations(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    db_locations = session.exec(select(Location).offset(offset).limit(limit)).all()
    return db_locations


@router.get(
    "/locations/{location_uid}", response_model=LocationReadDetails, tags=["locations"]
)
async def read_location(
    *, session: Session = Depends(get_session), location_uid: uuid.UUID
):
    db_location = session.get(Location, location_uid)
    if not db_location:
        raise HTTPException(status_code=404, detail="Locatino not found")
    return db_location


@router.delete("/datasets/{dataset_uid}", tags=["datasets"])
def delete_dataset(*, session: Session = Depends(get_session), dataset_uid: uuid.UUID):
    db_dataset = session.get(DataSet, dataset_uid)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    session.delete(db_dataset)
    session.commit()
    return {"ok": True}


@router.post("/datasets/", response_model=DataSetReadDetails, tags=["datasets"])
async def create_dataset(
    *, session: Session = Depends(get_session), dataset: DataSetCreate
):
    primary_keys_list = [str(loc.uid) for loc in dataset.locations]
    statement = select(Location).where(Location.uid.in_(primary_keys_list))
    locations = session.exec(statement).all()
    dataset.locations = locations
    db_dataset = DataSet.model_validate(dataset)
    session.add(db_dataset)
    session.commit()
    session.refresh(db_dataset)
    return db_dataset


@router.get("/datasets/", response_model=list[DataSetReadCompact], tags=["datasets"])
async def read_datasets(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    db_datasets = session.exec(select(DataSet).offset(offset).limit(limit)).all()
    return db_datasets


@router.get(
    "/datasets/{dataset_uid}", response_model=DataSetReadDetails, tags=["datasets"]
)
async def read_dataset(
    *, session: Session = Depends(get_session), dataset_uid: uuid.UUID
):
    db_dataset = session.get(DataSet, dataset_uid)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return db_dataset


# @router.patch(
#     "/datasets/{dataset_uid}", response_model=DataSetReadDetails, tags=["datasets"]
# )
# async def update_dataset(
#     *,
#     session: Session = Depends(get_session),
#     dataset_uid: uuid.UUID,
#     dataset: DataSetUpdate
# ):
#     db_dataset = session.get(DataSet, dataset_uid)
#     if not db_dataset:
#         raise HTTPException(status_code=404, detail="Dataset not found")
#     dataset_data = dataset.model_dump(exclude_unset=True)
#     for key, value in dataset_data.items():
#         setattr(db_dataset, key, value)
#     session.add(db_dataset)
#     session.commit()
#     session.refresh(db_dataset)
#     return db_dataset


@router.post("/workplans/", response_model=WorkPlanRead, tags=["workplans"])
async def create_workplan(
    *, session: Session = Depends(get_session), workplan: WorkPlanCreate
):
    db_workplan = WorkPlan.model_validate(workplan)
    session.add(db_workplan)
    session.commit()
    session.refresh(db_workplan)
    # For consistency add (empty) route data associated with the workplan
    statement = select(Route).where(Route.workplan_uid == db_workplan.uid)
    db_routes = session.exec(statement).all()
    workplan_dict = db_workplan.model_dump()
    workplan_dict["routes"] = db_routes
    return WorkPlanRead(**workplan_dict)


@router.get(
    "/workplans/{workplan_uid}", response_model=WorkPlanRead, tags=["workplans"]
)
async def read_workplan(
    *, session: Session = Depends(get_session), workplan_uid: uuid.UUID
):
    db_workplan = session.get(WorkPlan, workplan_uid)
    if not db_workplan:
        raise HTTPException(status_code=404, detail="WorkPlan not found")
    # For consistency add (empty) route data associated with the workplan
    statement = select(Route).where(Route.workplan_uid == db_workplan.uid)
    db_routes = session.exec(statement).all()
    workplan_dict = db_workplan.model_dump()
    workplan_dict["routes"] = db_routes
    return WorkPlanRead(**workplan_dict)


# @router.post("/workplans/assign", response_model=WorkPlanRead, tags=["workplans"])
@router.post("/workplans/assign", tags=["workplans"])
async def assign_workplan(
    *, session: Session = Depends(get_session), workplan: Identifier
):
    db_workplan = session.get(WorkPlan, workplan.uid)
    db_dataset = session.get(DataSet, db_workplan.dataset_uid)
    print(db_dataset.locations)
    
    # statement = select(Location, DataSet).where(Location.dataset_uid == DataSet.uid)
    # results = session.exec(statement)
    # for hero, team in results:
    #     print("Hero:", hero, "Team:", team)
    
    # db_workplan = WorkPlan.model_validate(workplan)
    # session.add(db_workplan)
    # session.commit()
    # session.refresh(db_workplan)
    # For consistency add (empty) route data associated with the workplan
    # statement = select(Route).where(Route.workplan_uid == db_workplan.uid)
    # db_routes = session.exec(statement).all()
    # workplan_dict = db_workplan.model_dump()
    # workplan_dict["routes"] = db_routes
    # return WorkPlanRead(**workplan_dict)
    return {}

# @router.post("/routes/", response_model=RouteRead, tags=["routes"])
# async def create_route(
#     *, session: Session = Depends(get_session), route: RouteCreate
# ):
#     db_route = WorkPlan.model_validate(route)
#     session.add(db_route)
#     session.commit()
#     session.refresh(db_route)
#     # For consistency add (empty) route data associated with the workplan
#     # statement = select(Route).where(Route.workplan_uid == db_workplan.uid)
#     # db_routes = session.exec(statement).all()
#     # workplan_dict = db_workplan.model_dump()
#     # workplan_dict["routes"] = db_routes
#     # return WorkPlanRead(**workplan_dict)
#     return db_route

# @router.post("/routes/", response_model=RouteRead, tags=["routes"])


@router.get("/routes/{route_uid}", response_model=RouteRead, tags=["routes"])
async def read_route(*, session: Session = Depends(get_session), route_uid: uuid.UUID):
    db_route = session.get(Route, route_uid)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    return db_route
