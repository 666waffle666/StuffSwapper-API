from pydantic import BaseModel, HttpUrl
from typing import Optional
from uuid import UUID


class ItemCreate(BaseModel):
    name: str
    description: str


class ItemImageRead(BaseModel):
    id: UUID
    image_url: HttpUrl


class ItemRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID
    is_available: bool

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    images: Optional[list[str]] = None
