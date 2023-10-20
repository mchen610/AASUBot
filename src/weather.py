from config import WEATHER_API_KEY
import requests

_emojis = {
    "01d": "☀️",
    "02d": "🌤️",
    "03d": "🌥️",
    "04d": "☁️",
    "09d": "🌧️",
    "10d": "🌧️",
    "11d": "⛈️",
    "13d": "🌨️",
    "50d": "🌫️",
    "01n": "🌑",
    "02n": "🌑",
    "03n": "☁️",
    "04n": "☁️",
    "09n": "🌧️",
    "10n": "🌧️",
    "11n": "⛈️",
    "13n": "🌨️",
    "50n": "🌫️",
}

def get_emoji(icon_code: str, moon_phase: float):
    if icon_code in ('01n', '02n'):
        phases = [
            (0.0625, '🌑'),
            (0.1875, '🌒'),
            (0.3125, '🌓'),
            (0.4375, '🌔'),
            (0.5625, '🌕'),
            (0.6875, '🌖'),
            (0.8125, '🌗'),
            (0.9375, '🌘'),
            (1.0000, '🌑')
        ]

        for threshold, emoji in phases:
            if moon_phase < threshold:
                return emoji

    else:
        return _emojis[icon_code]


def temp_emoji(feels_like: float):
    if feels_like > 90:
        return "🔥"

    elif 50 <= feels_like <= 90:
        return "😌"

    elif feels_like < 50:
        return "🧊"


def get_weather():
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/onecall?lat=29.65&lon=-82.34&exclude=minutely,hourly&appid={WEATHER_API_KEY}&units=imperial"
    )
    data = response.json()

    try:
        feels_like = data['current']["feels_like"]
        desc = data['current']["weather"][0]["description"].capitalize()
        icon_code = data['current']["weather"][0]["icon"]
        moon_phase = data['daily'][0]["moon_phase"]
        emoji = get_emoji(icon_code, moon_phase)
        return {
            "temp": feels_like,
            "desc": desc,
            "icon_url": f"http://openweathermap.org/img/wn/{icon_code}.png",
            "emoji": emoji,
            "temp_emoji": temp_emoji(feels_like),
        }
    
    except Exception:
        return {"temp": "80", "desc": "Feels normal I hope (I messed up)", "icon_url": "http://openweathermap.org/img/wn/04d.png", "emoji": "☁️", "temp_emoji": "😌"}


def get_weather_msg():
    weather = get_weather()
    
    desc = weather["desc"]
    temp = weather["temp"]
    emoji = weather["emoji"]
    temp_emoji = weather["temp_emoji"]

    weather_msg = f"{emoji} {desc}, feels like {temp}°F {temp_emoji}"
    return weather_msg
