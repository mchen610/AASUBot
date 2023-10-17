from dotenv import load_dotenv
import os

import discord
from discord import Color
from discord.commands import Option 
from discord.ext import tasks

from datetime import date, time, datetime, timedelta, timezone
from dateutil.parser import parse as date_parse

from googleapiclient.discovery import build

from twilio.rest import Client
import phonenumbers

import firebase_admin
from firebase_admin import credentials, db


load_dotenv()
GOOGLE_CALENDAR_API_KEY = os.environ['GOOGLE_CALENDAR_API_KEY']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_VERIFY_SID = os.environ['TWILIO_VERIFY_SID']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
DISCORD_AASU_BOT_TOKEN=os.environ['DISCORD_AASU_BOT_TOKEN']

est = timezone(timedelta(hours=-4))
midnight = time(5, 3, 0, 0, est)
before_midnight = time(5, 2, 0, 0, est)

class SubOrgGroup:
    def __init__(self):
        self.org_dict = {
            'AASU': SubOrg('Asian American Student Union', Color.dark_theme()),
            'CASA': SubOrg('Chinese American Student Association', Color.yellow()),
            'HEAL': SubOrg('Health Educated Asian Leaders', Color.green()),
            'KUSA': SubOrg('Korean Undergraduate Student Association', Color.blue()),
            'FSA': SubOrg('Filipino Student Association', Color.red()),
            'FLP': SubOrg('First-Year Leadership Program', Color.from_rgb(150, 200, 255)),
            'VSO': SubOrg('Vietnamese Student Organization', Color.orange())
        }
        self.service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)

    def reset_events(self):
        for org in self.org_dict.values():
            org.event_list = []


    @tasks.loop(time=before_midnight)
    def pull_events(self):
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        time_min = today.isoformat() + 'Z'
        time_max = (today + timedelta(days=90)).isoformat() + 'Z'
        
        raw_events = self.service.events().list(calendarId='aasu.uf@gmail.com', timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy='startTime').execute().get('items', [])

        for event in raw_events:
            try:
                name = event['summary']
                start, end = date_parse(event['start'].get('date')).date(), date_parse(event['end'].get('date')).date()
                event_length = (end - start).days
                for i in range(event_length):
                    start = date_parse(event['start'].get('date')).date()+timedelta(days=i)
                    new_event = {'name': name, 'start': start}

                    for org in self.org_dict.values():
                        if org.name in name:
                            org.event_list.append(new_event)

                    if "FAHM" in name and "FSA" not in name:
                        self.org_dict['FSA'].event_list.append(new_event)
            except:
                pass

class SubOrg:
    def __init__(self, extended_name: str, color: Color):
        name = ""
        for word in extended_name.split():
            name += word[0]

        self.extended_name = extended_name
        self.name = name
        self.color = color

        self.event_list = []
        
    def get_events_until(self, time_max: date):
        for i in range(len(self.event_list)-1, -1, -1):
            if self.event_list[i]['start'] < time_max:
                return self.event_list[:i+1]

    def get_events_embed(self, timeframe: int = 7):
        event_list = self.get_events_until(time_max = date.today() + timedelta(timeframe))

        header = f"**__{self.name} EVENTS WITHIN {timeframe} DAY(S)__**"
        for event in event_list:
            start = event['start'].strftime('%a, %b %d')
            msg = f"{msg}\n{start}: **{event['name']}**"
        
        if msg == '\n':
            msg = f"{msg}**No events!**"

        return discord.Embed(title=header, description=msg, color=self.color, timestamp=datetime.now())
