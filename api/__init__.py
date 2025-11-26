from fastapi import FastAPI
from api.routers import auth_router

api = FastAPI(title="StuffSwapper API")

api.include_router(auth_router, tags=["Auth"])
