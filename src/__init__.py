import logging.config

from os.path import abspath, join, isfile, exists
from os import getcwd, makedirs

from yaml import safe_load

from telethon.sync import TelegramClient


config_path = abspath(join(getcwd(), 'src', 'cfg', 'config.yaml'))
logger_path = abspath(join(getcwd(), 'src', 'cfg', 'logging.yaml'))

if not exists('logs'):
    makedirs('logs')

if isfile(config_path):
    with open(config_path, 'r') as file:
        config = safe_load(file)

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
                     config['telegram_bot']['api_id'],
                     config['telegram_bot']['api_hash'])

bot.start(bot_token=config['telegram_bot']['api_key'])
