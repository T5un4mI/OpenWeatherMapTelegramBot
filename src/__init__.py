import logging.config

from os.path import abspath, join, exists
from os import getcwd, makedirs, environ

from yaml import safe_load

from telethon.sync import TelegramClient

logger_path = abspath(join(getcwd(), 'src', 'logging.yaml'))

if not exists('logs'):
    makedirs('logs')

with open(logger_path, 'rt') as file:
    logger_config = safe_load(file.read())
    logging.config.dictConfig(logger_config)


weather_emodji = {'01': '☀️',
                  '02': '⛅️',
                  '03': '☁️',
                  '04': '☁️',
                  '09': '🌧',
                  '10': '🌦',
                  '11': '🌩',
                  '13': '🌨',
                  '50': '🌫'}

bot = TelegramClient('Session_bot_test',
                     environ.get('TG_API_ID'),
                     environ.get('TG_API_HASH'))

bot.start(bot_token=environ.get('TG_API_KEY'))
