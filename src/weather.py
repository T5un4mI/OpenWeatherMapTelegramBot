from logging import getLogger

from os import environ

from requests import get, exceptions

from asyncio import get_event_loop

from time import strftime, gmtime

from src import weather_emodji


logger = getLogger(__name__)


async def get_current_weather(city: str):
    """Request for the latest city weather data."""

    def make_request():
        """Request based only on city name."""
        response = None
        payload = {'q': '{}'.format(city),
                   'units': 'metric',
                   'appid': environ.get('WEATHER_API_KEY')}
        try:
            response = get('https://api.openweathermap.org/data/2.5/weather?',
                           params=payload)
        except exceptions.HTTPError as error:
            logger.warning('get_current_weather: %s', error)
        except exceptions.ConnectionError as error:
            logger.warning('get_current_weather: %s', error)
        except exceptions.Timeout as error:
            logger.warning('get_current_weather: %s', error)
        except exceptions.RequestException as error:
            logger.warning('get_current_weather: %s', error)
        return response

    loop = get_event_loop()
    response = await loop.run_in_executor(None, make_request)
    if not response:
        return 'Error with OpenWeatherMap API, try later.'
    return data_extraction(response.json())


def data_extraction(data):
    """Parse data and create message."""
    cod = data.get('cod', '404')
    if cod == '404':
        return 'City not found. Please check the spelling of the word'

    weather = data.get('weather')
    if weather:
        icon = ''.join(filter(str.isdigit, weather[0].get('icon')))
        icon = weather_emodji.get(icon)
        msg = 'Description: {} {}\n'.format(weather[0].get('description'),
                                            icon)

    msg += f'Visability: {data.get("visibility")} meters\n'\
           f'Temperature: {data.get("main", {}).get("temp")} °C\n'\
           f'Feels like: {data.get("main", {}).get("feels_like")} °C\n'\
           f'Min temperature: {data.get("main", {}).get("temp_min")} °C\n'\
           f'Max temperature: {data.get("main", {}).get("temp_max")} °C\n'\
           f'Pressure: {data.get("main", {}).get("pressure")} hPa\n'\
           f'Pressure (sea): {data.get("main", {}).get("sea_level")} hPa\n'\
           f'Pressure (ground): {data.get("main", {}).get("grnd_level")}\
            hPa\n'\
           f'Humidity: {data.get("main", {}).get("humidity")} %\n'\
           'Wind:\n'\
           f'    Speed: {data.get("wind", {}).get("speed")} meter/sec\n'\
           f'    Direction: {data.get("wind", {}).get("deg")} degrees\n'\
           f'    Gust: {data.get("wind", {}).get("gust")} meter/sec\n'\
           f'Cloudiness: {data.get("clouds", {}).get("all")} %\n'\
           f'Rain volume for the last 1 hour: {data.get("rain", {}).get("1h")}\
            mm\n'\
           f'Rain volume for the last 3 hour: {data.get("rain", {}).get("3h")}\
            mm\n'\
           f'Snow volume for the last 1 hour: {data.get("snow", {}).get("1h")}\
            mm\n'\
           f'Snow volume for the last 3 hour: {data.get("snow", {}).get("3h")}\
            mm\n'

    sys_ = data.get('sys')
    if sys_:
        timezone = data.get('timezone')
        sunrise = sys_.get('sunrise')
        sunset = sys_.get('sunset')
        if timezone and sunrise and sunset:
            sunrise = strftime("%H:%M:%S", gmtime(sunrise + timezone))
            sunset = strftime("%H:%M:%S", gmtime(sunset + timezone))
        msg += 'Sunrise: {} \n'.format(sunrise)
        msg += 'Sunset: {} \n'.format(sunset)

    msg = msg.split('\n')
    msg = [str_ for str_ in msg if 'None' not in str_]
    return '\n'.join(msg)
