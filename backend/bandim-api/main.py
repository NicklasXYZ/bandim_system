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
import crud, models, schemas
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
from models import DataSet, Location


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
        "description": "Operations on rotues primarily consisting of an ordered sequence of locations. Each route is associated with a health worker and a workplan.",
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


# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# async def read_snippet(filepath: str) -> Union[None, str]:
#     """Read in a Gleam code snippet from local file storage.

#     Args:
#         filepath (str): The filepath to a Gleam code snippet.

#     Returns:
#         Union[None, bool]: True if the Gleam code snippet was read in and cached
#             correctly. Otherwise None or False.
#     """
#     with open(filepath) as f:
#         name = None; uuid = None
#         print("Reading in snippet: ")
#         while True:
#             try:
#                 line = next(f)
#                 if len(line.split("//cname:")) == 2:
#                     name = line.split("//cname:")[-1].strip("'\n")
#                 if len(line.split("//cuuid:")) == 2:
#                     uuid = line.split("//cuuid:")[-1].strip("'\n")
#                 if name is not None and uuid is not None:
#                     code = str(f.read())
#                     # Cache the Gleam code snippet in Redis
#                     rc = await redis_cache.set(
#                         key = uuid,
#                         value = json.dumps(code),
#                         expire = REDIS_TTL,
#                     )
#                     if rc is None:
#                         logging.debug(
#                             f'REDIS: A Gleam code snippet could not be cached with identifier: {uuid}'
#                         )
#                     return code
#             except StopIteration:
#                 break
#     return None


# @app.get('/version')
# async def version() -> Response:
#     return Response(VERSION, 200)


# @app.options('/version')
# async def version_options() -> Response:
#     """... Send a default preflight request response...

#     Returns:
#         Response: ...
#     """
#     return Response(
#         'Success', 200,
#         headers = {
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Headers': '*'
#         }
#     )


# @app.on_event('startup')
# async def starup_event() -> None:
#     await redis_cache.init_cache()


# @app.on_event('shutdown')
# async def shutdown_event() -> None:
#     redis_cache.close()
#     await redis_cache.wait_closed()


# @app.post('/snippet')
# async def create_snippet(
#     snippet: schemas.BaseSnippet,
#     db: Session = Depends(get_db),
#     x_api_key: Optional[str] = Header(None),
#     ) -> JSONResponse:
#     """Create a Gleam code snippet and save it for long term storage.

#     Args:
#         snippet (schemas.BaseSnippet): A Gleam code snippet that is to be saved to the database.
#         db (Session, optional): A database session. Defaults to Depends(get_db).
#         x_api_key (Optional[str], optional): An API key provided by the frontend.
#             Defaults to Header(None).

#     Returns:
#         JSONResponse: The identifier of the saved code snippet.
#     """
#     # Check if the given API is valid
#     check_api_key(x_api_key, API_KEY)
#     db_snippet = crud.create_snippet(db = db, snippet = snippet)
#     logging.debug(
#         f'DB   : A Gleam code snippet was created with identifier: {db_snippet.snippetID}'
#     )
#     code = json.dumps(db_snippet.code)
#     # Cache the Gleam code snippet
#     rc = await redis_cache.set(
#         key = db_snippet.snippetID,
#         value = code,
#         expire = REDIS_TTL,
#     )
#     if rc is not None:
#         logging.debug(
#             f'REDIS: A Gleam code snippet was cached with identifier: {db_snippet.snippetID}'
#         )
#     rv = {'snippetID': db_snippet.snippetID}
#     return JSONResponse(rv, 201)


# @app.options('/snippet')
# async def snippet_options() -> Response:
#     """... Send a default preflight request response...

#     Returns:
#         Response: ...
#     """
#     return Response(
#         'Success', 200,
#         headers = {
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Headers': '*'
#         }
#     )


# @app.get('/snippet/{snippet_id}')
# async def get_snippet(
#     snippet_id: str,
#     db: Session = Depends(get_db),
#     x_api_key: Optional[str] = Header(None),
#     ) -> JSONResponse:
#     """Retrieve a Gleam code snippet given a certain identifier.

#     Args:
#         snippet_id (str): The identifier of the saved Gleam code snippet.
#         db (Session, optional): A database session. Defaults to Depends(get_db).
#         x_api_key (Optional[str], optional): An API key provided by the frontend.
#             Defaults to Header(None).

#     Raises:
#         HTTPException: If the requested Gleam code snippet was not found.

#     Returns:
#         JSONResponse: The requested Gleam code snippet.
#     """
#     # Check if the given API is valid
#     check_api_key(x_api_key, API_KEY)
#     # Try to retrieve the Gleam code snippet from cache
#     code = await redis_cache.get(key = snippet_id)
#     if code is None:
#             # Try to retrieve the Gleam code snippet from the database
#             db_snippet = crud.get_snippet(db, snippet_id = snippet_id)
#             logging.debug(
#                 f'DB   : A Gleam code snippet was retrieved with identifier: {snippet_id}'
#             )
#             if db_snippet is None:
#                 # As a last resort, try to retrieve the Gleam code snippet from local file storage
#                 filepath = await check_snippets(key = snippet_id)
#                 if filepath is not None:
#                     code = await read_snippet(filepath = filepath)
#                 else:
#                     logging.debug(
#                         f'     : No Gleam code snippet could be found with identifier: {snippet_id}'
#                     )
#                     raise HTTPException(status_code = 404, detail = 'Snippet not found')
#             else:
#                 code = db_snippet.code
#     else:
#         logging.debug(
#             f'REDIS: A Gleam code snippet was retrieved with identifier: {snippet_id}'
#         )
#         code = json.loads(code)
#     rv = {'fileName': None, 'code': code}
#     return JSONResponse(rv, 200)


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
