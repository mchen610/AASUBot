from typing import Optional
from googleapiclient.discovery import Resource

from discord import Color, Embed
from discord.ext import tasks

from datetime import time, datetime, timedelta
from dateutil.parser import parse as date_parse

from event import Event, EventList
from weather import set_weather_footer
from system_messages import get_error_msg
from times import est, get_utc_offset, midnight as loop_time



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
    def timeframe_str(days: int):
        if days == 1:
            return "TODAY"
        elif days == 2:
            return "TODAY AND TOMORROW"
        elif days == 7:
            return "THIS WEEK"
        else:
            return f"WITHIN THE NEXT {days} DAYS"

    def embed(self, lat: float, lon: float, days: int = 7):
        if days < 0:
            return get_error_msg("Please enter a positive integer!")
        elif days > 90:
            return get_error_msg("Please enter a positive integer below or equal to 90!")
        else:
            
            header = f"**__{self.name} EVENTS {self.__class__.timeframe_str(days)}__**"
            event_list = self.event_list.events_until(days)
            
            embed = Embed(title=header, description=event_list.to_markdown(), color=self.color, timestamp=datetime.now())
            embed.set_author(name=f"Today is {datetime.now(tz=est).strftime('%A, %b %d')}.")
            embed.set_thumbnail(url=self.img_url)
            set_weather_footer(embed, lat, lon)

            return embed
    
    def str_msg(self, days: int = 7):
        if days < 0 or days > 90:
            return "Invalid days."

        header = f"{self.name} EVENTS {self.__class__.timeframe_str(days)}"
        event_list = self.event_list.events_until(days)
        return f"{header}\n\n{event_list}"

class SubOrgManager:
    def __init__(self, orgs: dict[str, SubOrg], default_org: str, calendar_id: str, google_service: Resource, lat: float, lon: float):
        self.orgs = orgs
        self.default_org = default_org
        self.calendar_id = calendar_id 
        self.google_service = google_service
        self.lat = lat
        self.lon = lon
        self.iter = 0

    def clear_events(self):
        """Clears every SubOrg instance's event list."""
        for org in self.orgs.values():
            org.event_list.clear()

    @tasks.loop(time=loop_time)
    async def pull_events(self):
        """Updates events in each SubOrg instance every 24 hours at 12 A.M. in case any events were created or updated"""
        
        self.clear_events()

        # Google Calendar requires UTC. Use local time's UTC offset to ensure correct date.
        today = datetime.utcnow()
        today.hour = get_utc_offset(today)

        time_min = today.isoformat() + 'Z'
        time_max = (today + timedelta(days=90)).isoformat() + 'Z'
        
        raw_events = self.google_service.events().list(calendarId=self.calendar_id, timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy='startTime').execute().get('items', [])

        for event in raw_events:
            try:
                event_name: str = event['summary']
                start, end = date_parse(event['start'].get('date')).date(), date_parse(event['end'].get('date')).date()
                event_length = (end - start).days
                for i in range(event_length):
                    date_obj = date_parse(event['start'].get('date')).date()+timedelta(days=i)
                    new_event = Event(event_name, date_obj)

                    for org in self.orgs.values():
                        if org.name == self.default_org or org.keywords & set(event_name.split()):
                            org.event_list.add(new_event)

            except:
                pass

    def embed(self, org_name: str = None, days: int = 7):
        """Returns a discord.Embed object containing events specific to a given organization and days."""
        org = org_name or self.default_org

        org = self.get(org_name)
        if org:
            return org.embed(self.lat, self.lon, days)
        return get_error_msg("Invalid organization name.")
    
    def get(self, org_name) -> Optional[SubOrg]:
        return self.orgs.get(org_name.upper(), None)     
    
    def __getitem__(self, org_name) -> Optional[SubOrg]:
        return self.get(org_name)
    
    def str(self):
        string = ''
        for org in self.orgs.values():
            string = string + str(org) + '\n'
        return string[:-1]
 
    
