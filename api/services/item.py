from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.database.models import Item
from typing import Sequence
from api.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    async def get_items(self, session: AsyncSession) -> Sequence[Item]:
        result = await session.execute(select(Item))
        items = result.scalars().all()
        return items

    async def get_item_by_id(self, item_id: str, session: AsyncSession) -> Item | None:
        statement = select(Item).where(Item.id == item_id)
        result = await session.execute(statement)
        item = result.scalar_one_or_none()
        return item

    async def get_items_by_user_id(
        self, user_id: str, session: AsyncSession
    ) -> Sequence[Item]:
        statement = select(Item).where(Item.owner_id == user_id)
        result = await session.execute(statement)
        items = result.scalars().all()
        return items

    async def create_item(self, user_id: str, data: ItemCreate, session: AsyncSession):
        item = Item(
            name=data.name,
            description=data.description,
            owner_id=user_id,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    async def update_item(
        self, item_id: str, item_data: ItemUpdate, session: AsyncSession
    ):
        item = await self.get_item_by_id(item_id, session)

        if not item:
            return None

        item_data_dict = item_data.model_dump(exclude_unset=True)

        for k, v in item_data_dict.items():
            setattr(item, k, v)

        await session.commit()
        await session.refresh(item)
        return item

    async def delete_item(self, item_id: str, user_id: str, session: AsyncSession):
        item = await self.get_item_by_id(item_id, session)
        if not item:
            return None

        if str(item.owner_id) != user_id:
            return False

        await session.delete(item)
        await session.commit()
        return True
