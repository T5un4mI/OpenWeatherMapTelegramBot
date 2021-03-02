from logging import getLogger

from asyncio import exceptions, get_event_loop, gather

from telethon import events, errors

from aioredis import ConnectionClosedError

from src.data_operations import redis_connection, queue_manager, delete_user

from src import bot


logger = getLogger(__name__)


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """
    Register user in the Redis.

    key - users:telegram_id
    hash fields - 'first_name', 'telegram_id'
    """
    user = await event.get_sender()

    first_name = user.first_name
    telegram_id = event.sender_id

    user_key = 'users:{}'.format(telegram_id)
    bot_response = 'Hello, {}!'.format(first_name)

    try:
        async with redis_connection() as redis:
            exists = await redis.exists(user_key)
            if not exists:
                transaction = redis.multi_exec()
                transaction.hset(user_key, 'telegram_id', telegram_id)
                transaction.hset(user_key, 'first_name', first_name)
                await transaction.execute()
                bot_response += '\nRegistration in the system successfully co'\
                                'mpleted!'
            else:
                bot_response += '\nYou are already registered in the system!'
    except ConnectionClosedError as error:
        logger.warning('Command "/start": %s', error)
        bot_response += '\nError. Please, retry "/start" again'

    try:
        await event.respond(bot_response)
    except errors.UserIsBlockedError:
        await delete_user(telegram_id)
        raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/set_up_city'))
async def set_up_city(event):
    """Set the user's city.

    Command "/my_current_weather" makes a forecast based on this data.

    key - users:telegram_id
    hash field - 'city'
    """
    telegram_id = event.sender_id
    user_key = 'users:{}'.format(telegram_id)

    try:
        async with bot.conversation(telegram_id, timeout=30) as conv:
            await conv.send_message('Enter city name or "cancel"')

            response = await conv.get_response()
            city = response.text

            if city == 'cancel':
                bot_response = 'Operation was canceled ❌'
            else:
                try:
                    async with redis_connection() as redis:
                        await redis.hset(user_key, 'city', city)
                        bot_response = 'The city has been successfully select'\
                                       'ed. At any time, you can change it, u'\
                                       'sing "/set_up_city" command'
                except ConnectionClosedError as error:
                    logger.warning('Command "/set_up_city": %s', error)
                    bot_response = 'Error. Please, retry /set_up_city again'

            try:
                await conv.send_message(bot_response)
            except errors.UserIsBlockedError:
                await delete_user(telegram_id)
                raise events.StopPropagation
    except exceptions.TimeoutError:
        try:
            await event.respond('Time is over ⌛️\nEnter "/set_up_city" to sta'
                                'rt over')
        except errors.UserIsBlockedError:
            await delete_user(telegram_id)
            raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/current_weather'))
async def current_weather(event):
    """Сurrent weather forecast by city name.

    After entering the command, bot will ask to enter the name of the city.
    """
    telegram_id = event.sender_id

    try:
        async with bot.conversation(telegram_id, timeout=30) as conv:
            await conv.send_message('Enter city name or "cancel"')

            response = await conv.get_response()
            city = response.text

            if city == 'cancel':
                bot_response = 'Operation was canceled ❌'
            else:
                try:
                    async with redis_connection() as redis:
                        await redis.lpush('weather',
                                          '{},{}'.format(telegram_id,
                                                         city))
                        bot_response = 'Processing...⏳'
                except ConnectionClosedError as error:
                    logger.warning('Command "/current_weather": %s', error)
                    bot_response = 'Error. Pls, retry /current_weather again'

            try:
                await event.respond(bot_response)
            except errors.UserIsBlockedError:
                await delete_user(telegram_id)
                raise events.StopPropagation
    except exceptions.TimeoutError:
        try:
            await event.respond('Time is over ⌛️\nEnter "/current_weather" to'
                                'start over')
        except errors.UserIsBlockedError:
            await delete_user(telegram_id)
            raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/my_current_weather'))
async def my_current_weather(event):
    """Weather forecast for the set city."""
    telegram_id = event.sender_id
    user_key = 'users:{}'.format(telegram_id)

    try:
        async with redis_connection() as redis:
            exists = await redis.hexists(user_key, 'city')
            if exists:
                city = await redis.hget(user_key, 'city')
                await redis.lpush('weather',
                                  '{},{}'.format(telegram_id,
                                                 city.decode()))
                bot_response = 'Processing...⏳'
            else:
                bot_response = 'Error. Enter "/set_up_city" first'

    except ConnectionClosedError as error:
        logger.warning('Command "/my_current_weather": %s', error)
        bot_response = 'Error. Please, retry "/my_current_weather" again'

    try:
        await event.respond(bot_response)
    except errors.UserIsBlockedError:
        await delete_user(telegram_id)
        raise events.StopPropagation


@bot.on(events.NewMessage(pattern='/help'))
async def help(event):
    """Send description of all commands."""
    telegram_id = event.sender_id
    bot_response = '/current_weather - actual weather forecast. Bot will ask '\
                   'you to enter the name of the city.\n'\
                   '/my_current_weather - actual weather forecast for the cit'\
                   'y specified in the "set_up_city command".\n'\
                   '/set_up_city - choose one city to make a forecast by "my_'\
                   'current_weather". You could update city at any time.'
    try:
        await event.respond(bot_response)
    except errors.UserIsBlockedError:
        await delete_user(telegram_id)
        raise events.StopPropagation


async def start_telegram_bot():
    """Launch system."""
    await bot.run_until_disconnected()


loop = get_event_loop()
tasks = gather(
        loop.create_task(start_telegram_bot()),
        loop.create_task(queue_manager())
    )

try:
    loop.run_until_complete(tasks)
except KeyboardInterrupt:
    tasks.cancel()
    loop.run_forever()
    tasks.exception()
finally:
    loop.close()
