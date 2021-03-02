from logging import getLogger

from requests import get, exceptions

from asyncio import get_event_loop

from time import strftime, gmtime

from src import config, weather_emodji


logger = getLogger(__name__)


async def get_current_weather(city: str):
    """Request for the latest city weather data."""

    def make_request():
        """Request based only on city name."""
        response = None
        payload = {'q': '{}'.format(city),
                   'units': 'metric',
                   'appid': config['open_weather']['api_key']}
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
        message = 'Description: {} {}\n'.format(weather[0].get('description'),
                                                icon)

    message += 'Visability: {} meters\n'.format(data.get('visibility'))

    main = data.get('main')
    if main:
        message += 'Temperature: {} °C\n'.format(main.get('temp'))
        message += 'Feels like: {} °C\n'.format(main.get('feels_like'))
        message += 'Min temperature: {} °C\n'.format(main.get('temp_min'))
        message += 'Max temperature: {} °C\n'.format(main.get('temp_max'))
        message += 'Pressure: {} hPa\n'.format(main.get('pressure'))
        message += 'Pressure (sea): {} hPa\n'.format(main.get('sea_level'))
        message += 'Pressure (ground) {} hPa\n'.format(main.get('grnd_level'))
        message += 'Humidity: {} %\n'.format(main.get('humidity'))

    wind = data.get('wind')
    if wind:
        message += 'Wind:\n'
        message += '    Speed: {} meter/sec\n'.format(wind.get('speed'))
        message += '    Direction: {} degrees\n'.format(wind.get('deg'))
        message += '    Gust: {} meter/sec\n'.format(wind.get('gust'))

    clouds = data.get('clouds')
    if clouds:
        message += 'Cloudiness: {} %\n'.format(clouds.get('all'))

    rain = data.get('rain')
    if rain:
        message += 'Rain volume for the last 1 '\
                   'hour: {} mm\n'.format(rain.get('1h'))
        message += 'Rain volume for the last 3 '\
                   'hours: {} mm\n'.format(rain.get('3h'))

    snow = data.get('snow')
    if snow:
        message += 'Snow volume for the last 1 '\
                   'hour: {} mm\n'.format(snow.get('1h'))
        message += 'Snow volume for the last 3 '\
                   'hours: {} mm\n'.format(snow.get('3h'))

    sys_ = data.get('sys')
    if sys_:
        timezone = data.get('timezone')
        sunrise = sys_.get('sunrise')
        sunset = sys_.get('sunset')
        if timezone and sunrise and sunset:
            sunrise = strftime("%H:%M:%S", gmtime(sunrise + timezone))
            sunset = strftime("%H:%M:%S", gmtime(sunset + timezone))
        message += 'Sunrise: {} \n'.format(sunrise)
        message += 'Sunset: {} \n'.format(sunset)

    message = message.split('\n')
    message = [str_ for str_ in message if 'None' not in str_]
    return '\n'.join(message)
