from dotenv import load_dotenv
import os

import discord
import requests
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials
from googleapiclient.discovery import build

load_dotenv()
GOOGLE_CALENDAR_API_KEY = os.environ['GOOGLE_CALENDAR_API_KEY']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_VERIFY_SID = os.environ['TWILIO_VERIFY_SID']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
DISCORD_TOKEN=os.environ['DISCORD_TOKEN']
DISCORD_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
WEATHER_API_KEY = os.environ['WEATHER_API_KEY']

#DISCORD CONFIG
intents = discord.Intents(members=True, message_content=True)
bot = discord.Bot(intents=intents, activity=discord.Activity(type=3, name="/help"), status=discord.Status.online)

#TWILIO CONFIG
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
verify_service = twilio_client.verify.v2.services(TWILIO_VERIFY_SID)

#FIREBASE CONFIG
cred = credentials.Certificate("service_account_key.json") 
firebase_admin.initialize_app(cred, {'databaseURL': "https://aasu-discord-bot-default-rtdb.firebaseio.com/"})

#GOOGLE CONFIG
google_service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)

def get_weather():
    response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=Gainesville&appid={WEATHER_API_KEY}&units=imperial")
    data = response.json()
    try:
        feels_like = data['main']['feels_like']
        desc = data['weather'][0]['description'].capitalize()
        icon_code = data['weather'][0]['icon']
        return {'perceived_temp': feels_like, 'desc': desc, 'icon_url': f"http://openweathermap.org/img/wn/{icon_code}.png"}
    except:
        return {'perceived_temp': '', 'desc': '', 'icon_url': None}
    