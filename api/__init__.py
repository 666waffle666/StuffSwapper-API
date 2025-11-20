from fastapi import FastAPI
from fastapi.responses import JSONResponse
from api.routers import auth_router

api = FastAPI()

api.include_router(auth_router)


@api.get("/")
async def get_root():
    return JSONResponse(content={"message": "Hello world!"})
