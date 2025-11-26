from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Boolean, DateTime, UUID, func, Text
from api.database import Base
from uuid import uuid4, UUID as UID
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    uuid: Mapped[UID] = mapped_column(
        UUID(as_uuid=True), default=uuid4, primary_key=True
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    email_verifications: Mapped[list["EmailVerification"]] = relationship(
        "EmailVerification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    items = relationship("Item", back_populates="owner")


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    token: Mapped[str] = mapped_column(
        String, primary_key=True, index=True
    )  # store as string (uuid4 hex)
    user_id: Mapped[UID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="email_verifications")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[UID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    owner_id: Mapped[UID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.uuid"))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    owner = relationship("User", back_populates="items")
    images = relationship(
        "ItemImage", back_populates="item", cascade="all, delete-orphan"
    )


class ItemImage(Base):
    __tablename__ = "item_images"

    id: Mapped[UID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id: Mapped[UID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)

    item = relationship("Item", back_populates="images")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[UID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sender_id: Mapped[UID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False
    )
    recipient_id: Mapped[UID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False
    )
    item_id: Mapped[UID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    item = relationship("Item", foreign_keys=[item_id])
