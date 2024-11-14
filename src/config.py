from dotenv import load_dotenv
import os

import discord
from twilio.rest import Client

from googleapiclient.discovery import build, Resource
import zoneinfo

bot_tz = zoneinfo.ZoneInfo('America/New_York')

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

# Task times config

# Twilio config
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
verify_service = twilio_client.verify.v2.services(TWILIO_VERIFY_SID)

# Google Calendar config
google_service: Resource = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)



    