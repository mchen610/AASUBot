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

    username = "frdddidn"
    try:
        with open("discordepic.json", "r+") as file:
            data = json.load(file)
            data['usernames'].append(username)  
    except:
        data = {'usernames': [username]};

    with open("discordepic.json", "w") as file:       
        json.dump(data, file, indent=4)