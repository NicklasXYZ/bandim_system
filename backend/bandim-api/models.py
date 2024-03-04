from typing import Optional

from sqlmodel import Field, Relationship, SQLModel
import uuid
import datetime as dt
from sqlalchemy import Column, DateTime, func
from enum import Enum
from pydantic import BaseModel



class DataSetLocationLink(SQLModel, table=True):
    dataset_uid: uuid.UUID = Field(
        default=None, foreign_key="dataset.uid", primary_key=True
    )
    location_uid: uuid.UUID = Field(
        default=None, foreign_key="location.uid", primary_key=True
    )


class RouteLocationLink(SQLModel, table=True):
    route_uid: uuid.UUID = Field(
        default=None, foreign_key="route.uid", primary_key=True
    )
    location_uid: uuid.UUID = Field(
        default=None, foreign_key="location.uid", primary_key=True
    )


class LocationTimestampLink(SQLModel, table=True):
    location_uid: uuid.UUID = Field(
        default=None, foreign_key="location.uid", primary_key=True
    )
    timestamp_uid: uuid.UUID = Field(
        default=None, foreign_key="timestamp.uid", primary_key=True
    )


class BaseAlgorithmRun(SQLModel):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


class AlgorithmRun(BaseAlgorithmRun, table=True):
    pass


class BaseLocation(SQLModel):
    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    demand: int = Field(default=0, index=True)
    depot: bool = Field(default=False, index=True)


class Location(BaseLocation, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    datasets: list["DataSet"] = Relationship(
        back_populates="locations", link_model=DataSetLocationLink
    )
    routes: list["Route"] = Relationship(
        back_populates="locations", link_model=RouteLocationLink
    )


class LocationCreate(BaseLocation):
    pass


class LocationReadCompact(BaseLocation):
    uid: uuid.UUID


class LocationReadDetails(BaseLocation):
    uid: uuid.UUID
    # TODO: Specify DataSetRead model
    datasets: list["DataSet"]
    # TODO: Specify RouteRead model
    routes: list["Route"]


class LocationTimestampReadDetails(BaseLocation):
    uid: uuid.UUID
    timestamp: "Timestamp"


class Identifier(SQLModel):
    uid: uuid.UUID


class BaseDataSet(SQLModel):
    name: str = Field(index=True)


class DataSet(BaseDataSet, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: dt.datetime = Field(default=dt.datetime.utcnow(), nullable=False)
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow, nullable=False)
    locations: list["Location"] = Relationship(
        back_populates="datasets", link_model=DataSetLocationLink
    )


class DataSetCreate(BaseDataSet):
    locations: Optional[list["Identifier"]]


class DataSetUpdate(BaseDataSet):
    locations: Optional[list["Location"]]


class DataSetReadCompact(BaseDataSet):
    uid: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime


class DataSetReadDetails(DataSetReadCompact):
    # TODO: Specify LocationRead model
    locations: list["Location"]


# class OrderBy(str, Enum):
#     id = "id"
#     name = "name"
#     created = "created"

# https://stackoverflow.com/questions/70319235/how-to-add-sortby-and-direction-as-query-parameter-in-fastapi

# class ItemQueryParams(BaseModel):
#     order_by: OrderBy = OrderBy.id
#     descending: bool = False


class BaseTimestamp(SQLModel):
    pass


class Timestamp(BaseTimestamp, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    datetime: dt.datetime = Field(default=None, nullable=True)
    route_uid: uuid.UUID = Field(default=None, foreign_key="route.uid")
    location_uid: uuid.UUID = Field(default=None, foreign_key="location.uid")


class TimestampCreate(BaseTimestamp):
    uid: uuid.UUID
    datetime: dt.datetime
    route_uid: uuid.UUID
    location_uid: uuid.UUID


class BaseRoute(SQLModel):
    pass


class Route(BaseRoute, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    locations: list["Location"] = Relationship(
        back_populates="routes", link_model=RouteLocationLink
    )
    workplan_uid: uuid.UUID = Field(default=None, foreign_key="workplan.uid")
    algorithmrun_uid: uuid.UUID = Field(default=None, foreign_key="algorithmrun.uid")


class RouteCreate(BaseRoute):
    workplan_uid: uuid.UUID
    algorithmrun_uid: Optional[uuid.UUID]
    # TODO: Specify LocationRead model
    locations: Optional[list["Location"]]


class RouteUpdate(BaseRoute):
    locations: Optional[list["Location"]]


class RouteRead(BaseRoute):
    uid: uuid.UUID
    # TODO: Specify LocationRead model
    locations: list["Location"]
    workplan_uid: uuid.UUID
    algorithmrun_uid: uuid.UUID


class BaseWorkPlan(SQLModel):
    start_time: dt.datetime = Field(nullable=False)
    end_time: dt.datetime = Field(nullable=False)
    workers: int = Field(nullable=False)
    dataset_uid: uuid.UUID = Field(default=None, foreign_key="dataset.uid")


class WorkPlan(BaseWorkPlan, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow, nullable=False)


class WorkPlanReadCompact(BaseWorkPlan):
    uid: uuid.UUID
    updated_at: dt.datetime
    # TODO: Specify RouteRead model
    routes: list["Route"]


class WorkPlanReadDetails(BaseWorkPlan):
    uid: uuid.UUID
    updated_at: dt.datetime
    # TODO: Is RouteRead model correct here?
    routes: list["RouteRead"]


class WorkPlanCreate(BaseWorkPlan):
    pass


class Individual(SQLModel, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    name: str = Field(index=True)
