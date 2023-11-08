from dotenv import load_dotenv
import os

import discord
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials
from googleapiclient.discovery import build, Resource

from times import get_offset_naive_time

load_dotenv()
GOOGLE_CALENDAR_API_KEY = os.environ['GOOGLE_CALENDAR_API_KEY']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_VERIFY_SID = os.environ['TWILIO_VERIFY_SID']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
DISCORD_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
WEATHER_API_KEY = os.environ['WEATHER_API_KEY']
FIREBASE_REALTIME_DATABASE_URL = os.environ['FIREBASE_REALTIME_DATABASE_URL']

# Discord config
intents = discord.Intents(members=True, message_content=True)
bot = discord.Bot(intents=intents, activity=discord.Activity(type=3, name="/help"), status=discord.Status.online)
def reminder_time(): return get_offset_naive_time(8)
def pull_events_time(): return get_offset_naive_time(0)
def dst_reset_time(): return get_offset_naive_time(2)


# Twilio config
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
verify_service = twilio_client.verify.v2.services(TWILIO_VERIFY_SID)

# Firebase config
cred = credentials.Certificate("service_account_key.json") 
firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_REALTIME_DATABASE_URL})

# Google Calendar config
google_service: Resource = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)



    