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
from twilio.rest import Client

if __name__ == "__main__":


    x = [1,2,3,4,5]
    for number in x:
        if number == 3:
            x.remove(number)
        print(number)
