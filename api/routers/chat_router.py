from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
from api.core.security.security import AccessTokenBearer
from api.database.models import Message
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_session
import json
import asyncio
import redis
from api.core.config import Config

chat_ws_router = APIRouter(prefix="/ws", tags=["chat_ws"])


REDIS_URL = Config.REDIS_URL


class RedisConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.redis = None
        self.pub = None

    async def start(self):
        self.redis = redis.from_url(REDIS_URL)
        self.pub = self.redis.pubsub()
        asyncio.create_task(self.listen_messages())

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        for ws in self.active_connections.get(user_id, []):
            await ws.send_json(message)

    async def publish_message(self, message: dict):
        await self.redis.publish("chat_channel", json.dumps(message))  # type: ignore

    async def listen_messages(self):
        sub = self.redis.pubsub()  # type: ignore
        await sub.subscribe("chat_channel")  # type: ignore
        async for raw in sub.listen():  # type: ignore
            if raw["type"] == "message":
                message = json.loads(raw["data"])
                await self.send_personal_message(message, message["recipient_id"])
                await self.send_personal_message(message, message["sender_id"])


manager = RedisConnectionManager()


@chat_ws_router.websocket("/chat/")
async def websocket_endpoint(
    websocket: WebSocket,
    access_token_data=Depends(AccessTokenBearer),
    session: AsyncSession = Depends(get_session),
):
    user_id = access_token_data["user_data"]["sub"]
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # data: {"recipient_id": str, "content": str, "item_id": Optional[str]}

            message = Message(
                sender_id=user_id,
                recipient_id=data["recipient_id"],
                item_id=data.get("item_id"),
                content=data["content"],
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)

            message_dict = {
                "id": message.id,
                "sender_id": message.sender_id,
                "recipient_id": message.recipient_id,
                "item_id": message.item_id,
                "content": message.content,
                "created_at": str(message.created_at),
            }

            # send to recipient
            await manager.send_personal_message(message_dict, str(message.recipient_id))
            # update UI to sender
            await manager.send_personal_message(message_dict, str(message.sender_id))

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
