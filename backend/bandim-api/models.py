from typing import Optional

from sqlmodel import Field, Relationship, SQLModel
import uuid
import datetime as dt
from sqlalchemy import Column, DateTime, func


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
    locations: Optional[list["Location"]]


class DataSetUpdate(BaseDataSet):
    locations: Optional[list["Location"]]


class DataSetRead(BaseDataSet):
    uid: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    locations: list["Location"]


class Location(SQLModel, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    datasets: list["DataSet"] = Relationship(
        back_populates="locations", link_model=DataSetLocationLink
    )
    routes: list["Route"] = Relationship(
        back_populates="locations", link_model=RouteLocationLink
    )


class Timestamp(SQLModel, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    datetime: dt.datetime = Field(default=None, nullable=True)
    route_uid: uuid.UUID = Field(default=None, foreign_key="route.uid")


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


class RouteCreate(BaseDataSet):
    locations: list["Location"]
    workplan_uid: str


class RouteUpdate(BaseDataSet):
    locations: Optional[list["Location"]]


class RouteRead(BaseDataSet):
    uid: uuid.UUID
    locations: list["Location"]
    workplan_uid: str


class BaseWorkPlan(SQLModel):
    start_time: dt.datetime = Field(nullable=False)
    end_time: dt.datetime = Field(nullable=False)
    dataset_uid: uuid.UUID = Field(default=None, foreign_key="dataset.uid")


class WorkPlan(BaseWorkPlan, table=True):
    uid: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    updated_at: dt.datetime = Field(default_factory=dt.datetime.utcnow, nullable=False)


class WorkPlanRead(BaseWorkPlan):
    uid: uuid.UUID
    routes: list["Route"]


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
