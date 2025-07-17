import aioredis
from fastapi import Depends
from config import settings

redis = None

async def startup():
    global redis
    redis = aioredis.from_url(f"redis://{settings.redis_host}:{settings.redis_port}", decode_responses=True)

async def shutdown():
    await redis.close()

def get_redis():
    return redis