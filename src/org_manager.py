from typing import Optional
import asyncio
import requests

from discord import Color, Embed
from discord.ext import tasks

from datetime import date, time, datetime, timedelta, timezone
from dateutil.parser import parse as date_parse

from event import Event, EventList
from config import google_service, get_weather
from special_messages import *


est = timezone(timedelta(hours=-4))
midnight = time(5, 3, 0, 0, est)
before_midnight = time(5, 2, 0, 0, est)


class SubOrg:
    def __init__(self, extended_name: str, color: Color, instagram: str, img_url: str, keywords: set = None):
        name = ""
        for word in extended_name.split():
            name += word[0]

        self.extended_name = extended_name
        self.name = name
        self.color = color
        self.keywords = keywords or set()
        self.keywords.add(name)
        self.event_list = EventList()

        self.instagram = instagram
        self.img_url = img_url

    def __str__(self):
        return f"{self.name.center(30, '_')}\n{'-'*30}\n{self.event_list}"
    
    def to_markdown(self):
        return f"__**{self.name.center(30, '-')}\n{'-'*30}\n**__{self.event_list.to_markdown()}"
    
    @staticmethod
    def timeframe_str(timeframe: int):
        if timeframe == 0:
            return "TODAY"
        elif timeframe == 7:
            return "THIS WEEK"
        else:
            return f"WITHIN {timeframe} DAYS"

    def embed(self, timeframe: int = 7):
        if timeframe < 0:
            return get_error_msg("Please enter a positive integer!")
        elif timeframe > 90:
            return get_error_msg("Please enter a positive integer below or equal to 90!")
        else:
            
            header = f"**__{self.name} EVENTS {self.__class__.timeframe_str(timeframe)}__**"
            event_list = self.event_list.events_until(date.today() + timedelta(days=timeframe))
            embed = Embed(title=header, description=event_list.to_markdown(), color=self.color, timestamp=datetime.now())

            weather = get_weather()
            desc, temp, icon_url = weather['desc'], weather['perceived_temp'], weather['icon_url']
            embed.set_footer(text=f"{desc}, feels like {temp}°F", icon_url=icon_url)
            embed.set_author(name=f"Today is {datetime.now().strftime('%A, %b %d')}.")
            embed.set_thumbnail(url=self.img_url)

            return embed
        
    
    def str_msg(self, timeframe: int = 7):
        if timeframe < 0 or timeframe > 90:
            return "Invalid timeframe."
        
        event_list = self.event_list.events_until(date.today() + timedelta(days=timeframe))
        return f"{self.name} EVENTS WITHIN {timeframe} DAY(S)\n{event_list}"



class SubOrgManager:
    orgs = {
            'AASU': SubOrg('Asian American Student Union', Color.dark_magenta(), 'ufaasu', 'https://i.imgur.com/i6fTLuY.png'),
            'CASA': SubOrg('Chinese American Student Association', Color.yellow(), 'ufcasa', 'https://i.imgur.com/R9oWQ8Z.png'),
            'HEAL': SubOrg('Health Educated Asian Leaders', Color.green(), 'ufheal', 'https://i.imgur.com/gvdij9i.png'),
            'KUSA': SubOrg('Korean Undergraduate Student Association', Color.blue(), 'ufkusa', 'https://i.imgur.com/6x8g4Jc.png'),
            'FSA': SubOrg('Filipino Student Association', Color.red(), 'uffsa', 'https://i.imgur.com/SHNdQTR.png', {'FAHM'}),
            'FLP': SubOrg('First-Year Leadership Program', Color.from_rgb(150, 200, 255), 'ufflp', 'https://i.imgur.com/LtJnLWk.png'),
            'VSO': SubOrg('Vietnamese Student Organization', Color.gold(), 'ufvso', 'https://i.imgur.com/7GvIPS4.png')
    }

    @classmethod
    def reset_events(cls):
        for org in cls.orgs.values():
            org.event_list.clear()

    @classmethod
    @tasks.loop(time=before_midnight)
    async def pull_events(cls):
        cls.reset_events()

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        time_min = today.isoformat() + 'Z'
        time_max = (today + timedelta(days=90)).isoformat() + 'Z'
        
        raw_events = google_service.events().list(calendarId='aasu.uf@gmail.com', timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy='startTime').execute().get('items', [])

        for event in raw_events:
            try:
                event_name: str = event['summary']
                start, end = date_parse(event['start'].get('date')).date(), date_parse(event['end'].get('date')).date()
                event_length = (end - start).days
                for i in range(event_length):
                    date_obj = date_parse(event['start'].get('date')).date()+timedelta(days=i)
                    new_event = Event(event_name, date_obj)

                    for org in cls.orgs.values():
                        
                        if org.name == 'AASU' or org.keywords & set(event_name.split()):
                            org.event_list.add(new_event)

            except:
                pass

    @classmethod
    def embed(cls, org_name: str = 'AASU', timeframe: int = 7):
        org = cls.get(org_name)
        if org:
            return org.embed(timeframe)
        return get_error_msg("Invalid organization name.")
    
    @classmethod
    def get(cls, org_name) -> Optional[SubOrg]:
        return cls.orgs.get(org_name.upper(), None)     
    
    @classmethod
    def __getitem__(cls, org_name) -> Optional[SubOrg]:
        return cls.get(org_name)
    
    @classmethod
    def str(cls):
        string = ''
        for org in cls.orgs.values():
            string = string + str(org) + '\n'
        return string
    
loop = asyncio.get_event_loop()
loop.run_until_complete(SubOrgManager.pull_events())