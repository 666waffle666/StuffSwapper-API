from fastapi import FastAPI
from api.routers import auth_router, item_router, chat_ws_router

api = FastAPI(title="StuffSwapper API")

api.include_router(auth_router, tags=["Auth"])
api.include_router(item_router, tags=["Items"])
api.include_router(chat_ws_router, tags=["Chat"])
