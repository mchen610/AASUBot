import discord
import asyncio
import schedule
from discord.ext import commands

from datetime import date, datetime, timedelta
from dateutil.parser import parse as date_parse
from pytz import timezone

from googleapiclient.discovery import build

import os
import json
import phonenumbers
from twilio.rest import Client

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    verify_sid = os.environ['TWILIO_VERIFY_SID']

    client = Client(account_sid, auth_token)

    number = "+329542580268"
    x = phonenumbers.parse(number)
    print(phonenumbers.is_possible_number(x))
    print(client.lookups.v2.phone_numbers(number).fetch().valid)