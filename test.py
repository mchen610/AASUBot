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
    for i in range(10):
        with open("test.json", "w+") as file:
            if True:
                break
        print(i)
