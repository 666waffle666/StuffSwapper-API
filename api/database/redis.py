from redis.asyncio import from_url
from api.core.config import Config


redis = from_url(url=Config.REDIS_URL, decode_responses=True)


async def add_jti_to_blocklist(jti: str) -> None:
    await redis.set(name=jti, value="", ex=Config.TOKEN_EXPIRE_MINUTES)


async def token_is_in_blocklist(jti: str) -> bool:
    return await redis.get(jti) is not None


async def increment_resend_count(user_id: str) -> int:
    key = f"verif_resend:{user_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 3600)
    return count


async def get_resend_count(user_id: str) -> int:
    key = f"verif_resend:{user_id}"
    v = await redis.get(key)
    return int(v) if v else 0
