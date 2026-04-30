import asyncio
import httpx
import os

API_KEY = 'de3d24fa9fa20bff40d2a6bbd5c37ec0'
DOLLAR_API_KEY = '99d763a116d852d4c32db95c'

WEATHER_ICONS = {
    '01d': '☀️',
    '01n': '🌙',
    '02d': '⛅️',
    '02n': '☁️',
    '03d': '☁️',
    '03n': '☁️',
    '04d': '☁️',
    '04n': '☁️',
    '09d': '🌧',
    '09n': '🌧',
    '10d': '🌦',
    '10n': '🌦',
    '11d': '⛈',
    '11n': '⛈',
    '13d': '❄️',
    '13n': '❄️',
    '50d': '🌫',
    '50n': '🌫',
}

WEATHER_TRANSLATIONS = {
    'clear sky': 'ясно',
    'few clouds': 'малооблачно',
    'scattered clouds': 'переменная облачность',
    'broken clouds': 'облачно',
    'shower rain': 'короткий дождь',
    'rain': 'дождь',
    'thunderstorm': 'гроза',
    'snow': 'снежно',
    'mist': 'туман',
    'overcast clouds': 'пасмурно',
    'light rain': 'легкий дождь',
    'heavy rain': 'сильный дождь',
    'light snow': 'легкий снег',
    'heavy snow': 'сильный снег',
    'fog': 'туман',
    'haze': 'дымка',
    'dust': 'пыль',
    'sand': 'песок',
    'squall': 'шквал',
    'tornado': 'торнадо',
}

async def get_coordinates(city):
    async with httpx.AsyncClient() as client:
        geo_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}'
        response = await client.get(geo_url)
        data = response.json()

        if response.status_code == 200:
            latitude = data['coord']['lat']
            longitude = data['coord']['lon']
            print(f"Координаты для {city}: Широта {latitude}, Долгота {longitude}")
        else:
            print(f"Ошибка при получении координат для {city}.")
            latitude, longitude = None, None

    return latitude, longitude

async def get_weather(city):
    async with httpx.AsyncClient() as client:
        weatherUrl = 'https://api.openweathermap.org/data/2.5/weather' + f'?q={city}&appid={API_KEY}'
        weatherResponse = await client.get(weatherUrl)
        weatherData = weatherResponse.json()

        temp = weatherData['main']['temp'] - 273.15
        description = weatherData['weather'][0]['description']
        icon = weatherData['weather'][0]['icon']
        weather_icon = WEATHER_ICONS.get(icon, "")

        description_ru = WEATHER_TRANSLATIONS.get(description, description)

        print(f'Температура: {temp:.2f}°C')
        print(f'Погода: {description_ru} {weather_icon}')

async def get_dollar():
    async with httpx.AsyncClient() as client:
        url = f"https://api.exchangerate-api.com/v4/latest/USD?apikey={DOLLAR_API_KEY}"
        response = await client.get(url)

        if response.status_code == 200:
            data = response.json()
            usd_to_rub = data["rates"]["RUB"]
            print(f"Курс доллара: 1 USD = {usd_to_rub:.2f} RUB")
        else:
            print(f"Ошибка при получении курса доллара. Код ответа: {response.status_code}")

async def main():
    os.system('cls')

    city = input("Введите название города: ")

    latitude, longitude = await get_coordinates(city)

    if latitude is not None and longitude is not None:

        await asyncio.gather(get_weather(city), get_dollar())


if __name__ == "__main__":
    asyncio.run(main())
