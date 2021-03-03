from logging import getLogger

from os import environ

from contextlib import asynccontextmanager

from asyncio import sleep

from aioredis import create_redis_pool, ConnectionClosedError

from src import bot

from src.weather import get_current_weather


logger = getLogger(__name__)


@asynccontextmanager
async def redis_connection():
    """Create and close connection for redis server."""
    connection = await create_redis_pool((environ.get('REDIS_URL'),
                                          environ.get('REDIS_PORT')))
    try:
        yield connection
    finally:
        connection.close()
        await connection.wait_closed()


async def queue_manager():
    """Manage data from 'weather' queue.

    Every time before calling it checks the restriction.
    Free account (OpenWeatherMap) has 60 requests per minute.
    """
    try:
        async with redis_connection() as redis:
            while True:
                query = await redis.rpop('weather')
                if query:
                    user_id, city = query.decode().split(',')
                    result = await get_current_weather(city)
                    while True:
                        status = await get_access_status()
                        if status:
                            break
                        else:
                            await sleep(1)
                    await bot.send_message(int(user_id), result)
                await sleep(1)
    except ConnectionClosedError as error:
        logger.warning(error)


async def get_access_status():
    """Manage 'api_restrict' counter in redis.

    Get and update key:value that storing the current
    number of API calls for the last minute.
    """
    try:
        async with redis_connection() as redis:
            key = await redis.exists('api_restrict')
            if not key:
                await redis.set('api_restrict', '1', expire=60)
                status = True
            else:
                value = await redis.get('api_restrict')
                if value.decode() == environ.get('MINUTE_LIMIT'):
                    status = False
                else:
                    await redis.incr('api_restrict')
                    status = True
    except ConnectionClosedError as error:
        logger.warning(error)
        status = False
    return status


async def delete_user(telegram_id):
    """Delete user from redis database."""
    try:
        async with redis_connection() as redis:
            await redis.delete('users:{}'.format(telegram_id))
        logger.info('User %s was deleted', telegram_id)
    except ConnectionClosedError as error:
        logger.warning(error)
