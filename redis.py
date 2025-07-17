import aioredis

redis = None

async def get_redis():
    return redis

async def startup():
    global redis
    redis = await aioredis.from_url(
        "redis://redis",
        encoding="utf-8",
        decode_responses=True
    )

async def shutdown():
    await redis.close()