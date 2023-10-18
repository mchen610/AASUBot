from config import WEATHER_API_KEY
import requests

emojis = {
    '01d': '☀️',
    '02d': '🌤️',
    '03d': '🌥️',
    '04d': '☁️',
    '09d': '🌧️',
    '10d': '🌧️',
    '11d': '⛈️',
    '13d': '🌨️',
    '50d': '🌫️',

    '01n': '🌑',
    '02n': '🌑',
    '03n': '☁️',
    '04n': '☁️',
    '09n': '🌧️',
    '10n': '🌧️',
    '11n': '⛈️',
    '13n': '🌨️',
    '50n': '🌫️',
}

def temp_emoji(feels_like: float):
    if feels_like > 90:
        return '🥵'
    elif 70 <= feels_like <= 90:
        return '😊'
    elif 50 < feels_like < 70:
        return '🧥'
    elif feels_like <= 50:
        return '🥶'
    
def get_weather():
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Gainesville&appid={WEATHER_API_KEY}&units=imperial")
    data = response.json()
    try:
        feels_like = data['main']['feels_like']
        desc = data['weather'][0]['description'].capitalize()
        icon_code = data['weather'][0]['icon']
        return {'temp': feels_like, 'desc': desc, 'icon_url': f"http://openweathermap.org/img/wn/{icon_code}.png", 'emoji': emojis[icon_code], 'temp_emoji': temp_emoji(feels_like)}
    except:
        return {'temp': '', 'desc': '', 'icon_url': '', 'emoji': '', 'temp_emoji': ''}