# OpenWeatherMapTelegramBot
Asynchronous telegram bot using OpenWeatherMap API for weather forecast. 

## Logic
Payload of commands ("/current_weather" and "/my_current_weather") puts in redis queue, task pulls it, checks if request limit has been reached (OpenWeatherMap has 60 requests per minute on free account), waits if limit reached and makes request to api endpoint and send processed result back to user.
Redis used for data persistence and convenience of counting. 
Program works asynchronous in single process.

## Usage
1. Go to [Telegram] -> API development tools
2. Copy api_id and api_hash or create if you don't have ([Telethon.SignUp]) 
3. Create a telegram bot via [BotFather]
4. Create an account on [OpenWeatherMap]. Get API key in profile
5. Open docker-compose.dev.yaml and paste:
    - api_id > TG_API_ID
    - api_hash > TG_API_HASH
    - bot_token > TG_API_KEY
    - openweather_api > WEATHER_API_KEY
6. Build image: 
```sh
docker build --tag python-weatherman .
```
7. Run in terminal
```sh
docker-compose -f docker-compose.yaml -f docker-compose.dev.yaml up
```

[Telegram]: <https://my.telegram.org/>
[Telethon.SignUp]: <https://docs.telethon.dev/en/latest/basic/signing-in.html#signing-in>
[BotFather]: <https://t.me/botfather>
[OpenWeatherMap]: <https://openweathermap.org/>