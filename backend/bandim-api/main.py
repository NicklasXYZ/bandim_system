from typing import Optional, Union, Tuple
import logging
import json
import os
from fastapi import FastAPI, Depends, HTTPException
from routers import public
from fastapi.params import Header
from starlette.responses import Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import redis_cache
from sqlalchemy.orm import Session

# from database import SessionLocal, engine
from database import engine
# import crud, models, schemas
from middleware import ContentSizeLimitMiddleware
from common import check_api_key, load_cors
from settings import (
    API_KEY,
    VERSION,
    REDIS_TTL,
    # SNIPPET_DIR,
)
from sqlmodel import SQLModel

# from sqlmodel import Session

# from .database import create_db_and_tables, engine
# from models import DataSet, Location


tags_metadata = [
    {
        "name": "datasets",
        "description": "Operations on datasets, which primarily consist of one or more locations. Each dataset represents a logical grouping of locations.",
    },
    {
        "name": "locations",
        "description": "Operations on locations, which primarily consist of latitude and longitude coordinates. Each location represents the location of a household.",
    },
    {
        "name": "routes",
        "description": "Operations on rotues primarily consisting of an ordered sequence of locations. Each route is associated with a worker and a workplan.",
    },
    {
        "name": "workplans",
        "description": "Operations on workplans (associated with a specific dataset), which primarily consist of a collection of routes with additional time-specific information.",
    },
    {
        "name": "default",
        "description": "Retrieve backend metadata",
    },
]

# app = FastAPI(docs_url = None, redoc_url = None)
# openapi_tags=openapi_tags
app = FastAPI(
    openapi_tags=tags_metadata,
    title="BandimPlatform",
    # description=description,
    summary="The Bandim Platform.",
    version="0.0.1",
    # terms_of_service="",
    # contact={
    #     "name": "",
    #     "url": "",
    #     "email": "",
    # },
    license_info={
        "name": "MIT",
        "identifier": "MIT",
    },
)
# app = FastAPI()

app.include_router(public.router, prefix="/api/public")

# CORS_CONFIG = load_cors()
# if CORS_CONFIG:
#     app.add_middleware(CORSMiddleware, **CORS_CONFIG)

# # Limit request size to 250000 bytes ~ 0.25 megabytes
# app.add_middleware(ContentSizeLimitMiddleware, max_content_size = 25_00_00)

# # Create database tables
# models.Base.metadata.create_all(bind = engine)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# def create_dataset():
#     with Session(engine) as session:
#         random_locs = DataSet(name="randomized-locations")

#         loc1 = Location(
#             latitude=11.85345134655994,
#             longitude=-15.598089853772322,
#             datasets=[random_locs]
#         )
#         loc2 = Location(
#             latitude=11.854746412196508,
#             longitude=-15.601586283046993,
#             datasets=[random_locs]
#         )
#         loc3 = Location(
#             latitude=11.84812109448719,
#             longitude=-15.600460066985532,
#             datasets=[random_locs]
#         )
#         loc4 = Location(
#             latitude=11.859027970025654,
#             longitude=-15.588562570690168,
#             datasets=[random_locs]
#         )
#         session.add(loc1)
#         session.add(loc2)
#         session.add(loc3)
#         session.add(loc4)
#         session.commit()

#         session.refresh(loc1)
#         session.refresh(loc2)
#         session.refresh(loc3)
#         session.refresh(loc4)

#         print()

#         print("loc1:", loc1)
#         print("loc1 dataset:", loc1.datasets)
#         print("loc2:", loc2)
#         print("loc2 dataset:", loc2.datasets)
#         print("loc3:", loc3)
#         print("loc3 dataset:", loc3.datasets)
#         print("loc4:", loc4)
#         print("loc4 dataset:", loc4.datasets)


def main():
    create_db_and_tables()
    # create_dataset()


if __name__ == "__main__":
    main()
