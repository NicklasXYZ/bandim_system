from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import insert

import datetime as dt
import numpy as np
from vrp_solver.vrp_solver import (
    VRP,
    TwoOptSolver,
    KMeansRadomizedPopulationInitializer,
    FitnessFunctionMinimizeDistance,
    individual_to_routes,
)
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
    WorkPlanReadCompact,
    WorkPlanReadDetails,
    WorkPlanCreate,
    Identifier,
    Route,
    RouteRead,
    RouteRead,
    RouteCreate,
    Timestamp,
    TimestampCreate,
    LocationTimestampReadDetails,
)
import uuid
import pandas as pd

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


@router.post("/workplans/", response_model=WorkPlanReadCompact, tags=["workplans"])
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
    return WorkPlanReadCompact(**workplan_dict)


@router.get(
    "/workplans/{workplan_uid}", response_model=WorkPlanReadCompact, tags=["workplans"]
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
    return WorkPlanReadCompact(**workplan_dict)


# @router.post("/workplans/assign", response_model=WorkPlanRead, tags=["workplans"])
@router.post("/workplans/assign", tags=["workplans"])
async def assign_workplan(
    *, session: Session = Depends(get_session), workplan: Identifier
):
    db_workplan = session.get(WorkPlan, workplan.uid)
    db_dataset = session.get(DataSet, db_workplan.dataset_uid)
    if not db_dataset:
        raise HTTPException(
            status_code=404,
            detail="A WorkPlan could not be created due to unknown dataset",
        )

    data = [
        {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "depot": loc.depot,
            "demand": loc.demand,
            "uid": loc.uid,
            # "loc": loc.model_dump()
        }
        for loc in db_dataset.locations
    ]
    df = pd.DataFrame(data=data).astype({"latitude": "float64", "longitude": "float64", "depot": "bool", "demand": "int64", "uid": "object"}).sort_values(by="depot", ascending=False)
    locations = df[["latitude", "longitude"]].to_numpy().tolist()
    
    vrp_instance = VRP(
        locations=locations,
        num_salesmen=db_workplan.workers,
        precompute_distances=True,
    )

    # Determine the appropriate population size
    n = len(locations)
    population_maximum = 10_000
    population_minimum = 25
    population_size = np.minimum(np.maximum(population_minimum, int(n / np.log2(n))), population_maximum)
    solver = TwoOptSolver(
        vrp_instance=vrp_instance,
        population_size=population_size,
        population_initializer_class=KMeansRadomizedPopulationInitializer,
        fitness_function_class=FitnessFunctionMinimizeDistance,
    )

    result = solver.run()
    best_solution = result.get_topk(k=1)[0]
    # print("Fitness: ", best_solution.fitness)
    routes = individual_to_routes(best_solution, vrp_instance)
    
    data = [] 
    for i in range(len(routes)):
        for j in range(len(routes[i])):
            d = {
                "latitude": routes[i][j][0], 
                "longitude": routes[i][j][1],
                "route": i,
                "visit_number": j,
            }
            data.append(d)
    ndf = pd.DataFrame(data=data).astype({"latitude": "float64", "longitude": "float64", "route": "int64", "visit_number": "int64"})
    merged_dfs = pd.merge(df, ndf, on=["latitude", "longitude"])
    merged_dfs = merged_dfs.sort_values(by="visit_number", ascending=True)

    visit_duration = dt.timedelta(seconds=10)

    # Add generated routes to the database
    for _, _df in merged_dfs.groupby("route"):

        # primary_keys_list = _df["uid"].to_numpy().tolist()
        # print(_df)
        
        current_time = db_workplan.start_time
        # Set the routing cost in terms of time
        default_time = dt.timedelta(seconds=120) 
        for _, row in _df.iterrows():
            current_time += default_time + visit_duration * row["demand"]
            print(current_time)
            print(row)
            break

    #     # timestamp = TimestampCreate()

    #     statement = select(Location).where(Location.uid.in_(primary_keys_list))
    #     locations = session.exec(statement).all()
    #     route = RouteCreate(
    #         locations=locations,
    #         workplan_uid=workplan.uid,
    #         algorithmrun_uid=uuid.uuid4(),
    #     )
    #     db_route = Route.model_validate(route)
    #     # Add the data to the database
    #     session.add(db_route)
    #     session.commit()
    #     session.refresh(db_route)

    # statement = select(Route).where(Route.workplan_uid == db_workplan.uid)
    # db_routes = session.exec(statement).all()
    # workplan_dict = db_workplan.model_dump()
    # workplan_dict["routes"] = db_routes

    # for route in db_routes:
    #     print(route.locations)
    #     print()
    # return WorkPlanReadDetails(**workplan_dict)
        
    # LocationTimestampReadDetails
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
