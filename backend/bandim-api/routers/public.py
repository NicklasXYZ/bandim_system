from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from database import engine
from models import (
    DataSet,
    DataSetCreate,
    DataSetRead,
    # DataSetUpdate,
    Location,
    WorkPlan,
    # PlanRead,
    Route,
    # RouteRead,
)
import uuid

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


@router.post("/datasets/", response_model=DataSetRead, tags=["datasets"])
async def create_dataset(
    *, session: Session = Depends(get_session), dataset: DataSetCreate
):
    print("HERE:")
    print(dataset)
    print()
    db_dataset = DataSet.model_validate(dataset)
    session.add(db_dataset)
    session.commit()
    session.refresh(db_dataset)
    return db_dataset


# @router.get("/datasets/", response_model=list[DataSetRead], tags=["datasets"])
# async def read_datasets(
#     *,
#     session: Session = Depends(get_session),
#     offset: int = 0,
#     limit: int = Query(default=100, le=100)
# ):
#     db_datasets = session.exec(select(DataSet).offset(offset).limit(limit)).all()
#     return db_datasets


# @router.get("/datasets/{dataset_uid}", response_model=DataSetRead, tags=["datasets"])
# async def read_dataset(
#     *, session: Session = Depends(get_session), dataset_uid: uuid.UUID
# ):
#     db_dataset = session.get(DataSet, dataset_uid)
#     if not db_dataset:
#         raise HTTPException(status_code=404, detail="Dataset not found")
#     return db_dataset


# @router.patch("/datasets/{dataset_uid}", response_model=DataSetRead, tags=["datasets"])
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


# @router.get("/locations/", response_model=list[Location], tags=["locations"])
# async def read_locations(
#     *,
#     session: Session = Depends(get_session),
#     offset: int = 0,
#     limit: int = Query(default=100, le=100)
# ):
#     db_locations = session.exec(select(Location).offset(offset).limit(limit)).all()
#     return db_locations


# @router.delete("/datasets/{dataset_uid}", tags=["datasets"])
# def delete_dataset(*, session: Session = Depends(get_session), dataset_uid: uuid.UUID):
#     db_dataset = session.get(DataSet, dataset_uid)
#     if not db_dataset:
#         raise HTTPException(status_code=404, detail="Dataset not found")
#     session.delete(db_dataset)
#     session.commit()
#     return {"ok": True}




# @router.get("/plans/{plan_uid}", response_model=PlanRead, tags=["plans"])
# async def read_plan(*, session: Session = Depends(get_session), plan_uid: uuid.UUID):
#     db_plan = session.get(Plan, plan_uid)
#     if not db_plan:
#         raise HTTPException(status_code=404, detail="Plan not found")
#     return db_plan


# @router.get("/routes/{route_uid}", response_model=RouteRead, tags=["routes"])
# async def read_route(*, session: Session = Depends(get_session), route_uid: uuid.UUID):
#     db_route = session.get(Route, route_uid)
#     if not db_route:
#         raise HTTPException(status_code=404, detail="Route not found")
#     return db_route
