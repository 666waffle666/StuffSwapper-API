from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr = Field()
    username: str = Field()
    password1: str = Field(min_length=6, max_length=64)
    password2: str = Field(min_length=6, max_length=64)


class UserRead(BaseModel):
    uuid: UUID
    email: EmailStr
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str
