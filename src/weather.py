from config import WEATHER_API_KEY
import requests
from datetime import datetime
from times import bot_tz
from discord import Embed, Color

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


def temp_emoji(temp: float):
    if temp > 90:
        return "🔥"

    elif 50 <= temp <= 90:
        return "😌"

    elif temp < 50:
        return "🧊"


def get_weather(lat: float, lon: float):
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={WEATHER_API_KEY}&units=imperial"
    )
    data = response.json()

    try:
        temp = data['current']["temp"]
        desc = data['current']["weather"][0]["description"].capitalize()
        icon_code = data['current']["weather"][0]["icon"]
        moon_phase = data['daily'][0]["moon_phase"]
        emoji = get_emoji(icon_code, moon_phase)
        return {
            "temp": temp,
            "desc": desc,
            "icon_url": f"http://openweathermap.org/img/wn/{icon_code}.png",
            "emoji": emoji,
            "temp_emoji": temp_emoji(temp),
        }
    
    except Exception:
        return {"temp": "0", "desc": "Error", "icon_url": "http://openweathermap.org/img/wn/04d.png", "emoji": "☁️", "temp_emoji": "😌"}


def get_weather_msg(lat: float, lon: float):
    weather = get_weather(lat, lon)
    desc = weather["desc"]
    temp = weather["temp"]
    emoji = weather["emoji"]
    temp_emoji = weather["temp_emoji"]

    weather_msg = f"{emoji} {desc}: it's {temp}°F {temp_emoji}"
    return weather_msg

def get_weather_embed(lat: float, lon: float):
    msg = get_weather_msg(lat, lon)
    embed = Embed(title="Weather", description=msg, timestamp=datetime.now())
    embed.set_author(name=f"Today is {datetime.now(tz=bot_tz).strftime('%A, %b %d')}.")
    return embed

def set_weather_footer(embed: Embed, lat: float, lon: float):
    weather = get_weather(lat, lon)
    desc = weather["desc"]
    temp = weather["temp"]
    icon_url = weather["icon_url"]
    temp_emoji = weather["temp_emoji"]

    embed.set_footer(text=f"{desc}: it's {temp}°F {temp_emoji}", icon_url=icon_url)

