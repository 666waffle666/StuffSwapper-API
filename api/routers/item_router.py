from fastapi import APIRouter, Depends, HTTPException
from api.core.security.security import AccessTokenBearer
from api.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from api.services import ItemService
from api.schemas.item import ItemCreate, ItemRead, ItemUpdate

item_router = APIRouter(prefix="/items")
item_service = ItemService()


@item_router.post("/", response_model=ItemRead)
async def create_item(
    item_data: ItemCreate,
    access_token_data=Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_id = access_token_data["user_data"]["sub"]
    item = await item_service.create_item(user_id, item_data, session)
    return item


@item_router.get("/")
async def get_items(session: AsyncSession = Depends(get_session)):
    return await item_service.get_items(session)


@item_router.get("/user/{user_id}")
async def get_item(user_id: str, session: AsyncSession = Depends(get_session)):
    return await item_service.get_items_by_user_id(user_id, session)


@item_router.put("/{item_id}")
async def update_item(
    item_id: str,
    item_data: ItemUpdate,
    access_token_data=Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_id = access_token_data["user_data"]["sub"]

    item = await item_service.get_item_by_id(item_id, session)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if str(item.owner_id) != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this item")

    updated_item = await item_service.update_item(item_id, item_data, session)

    return updated_item


@item_router.delete("/{item_id}")
async def delete_item_route(
    item_id: str,
    access_token_data=Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    user_id = access_token_data["user_data"]["sub"]

    result = await item_service.delete_item(item_id, user_id, session)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if result is False:
        raise HTTPException(status_code=403, detail="Not allowed to delete this item")

    return {"detail": "Item deleted successfully"}
