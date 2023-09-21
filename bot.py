import discord
from discord.ext import commands

from datetime import date, datetime, timedelta 
from dateutil.parser import parse as date_parse

from googleapiclient.discovery import build

API_KEY = 'AIzaSyB-iPQzUWjNvGh4RMn3lxOfmzvF32LT150'

allEvents: list[dict[str, str]] = [];
suborgEvents: dict = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []};

def main():

    service = build('calendar', 'v3', developerKey=API_KEY)

    today = datetime.today()
    print(today)
    today.replace(hour=0, minute=0, second=0, microsecond=0)
    inOneMonth = today + timedelta(days=30)

    timeMin = today.isoformat() + 'Z'
    timeMax = inOneMonth.isoformat() + 'Z'
    
    events_result = service.events().list(calendarId='aasu.uf@gmail.com', timeMin=timeMin, timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    for event in events:
        name = event['summary']
        start = event['start'].get('date')
        end = (date_parse(event['end'].get('date'))-timedelta(days=1)).strftime('%Y-%m-%d')
        if start != end:
            end = ' **-** ' + end
        else:
            end = ''
        newEvent = {'name': name, 'start': start, 'end': end}

        allEvents.append(newEvent)
        for org in suborgEvents:
            if org in name:
                suborgEvents[org].append(newEvent)




if __name__ == '__main__':
    main()



intents = discord.Intents.default()
intents.members = True
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents, activity=discord.Activity(type=3, name="!help"), status=discord.Status.online)
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")  


@bot.command()
async def events(ctx, *args):
    eventList: list = [];
    heading = "EVENTS"

    args = list(args)
    for i in range(len(args)):
        args[i] = args[i].upper()
    print(args)

    for org in set(args) & set(suborgEvents):
        eventList = eventList + suborgEvents[org]
        heading = org+" "+heading

    eventList.sort(key=lambda x: x['start'])

    if len(eventList) == 0:
        eventList = allEvents
        heading = "ALL AASU EVENTS"
    
    today = date.today()
    tomorrow = today+timedelta(1)
    inOneWeek = today+timedelta(7)


    if "TODAY" in args:
        eventList = [event for event in eventList if event['start']==str(today)]
        print(eventList)
        if len(eventList) == 0:
            heading = "No events today!"
        else:
            heading = heading + " " + "TODAY"
            
        
        
    elif "TOMORROW" in args:
        eventList = [event for event in eventList if event['start']==str(tomorrow)]
        if len(eventList) == 0:
            heading = "No events tomorrow!"
        else:
            heading = heading + " " + "TOMORROW"

    elif "WEEK" in args:
        eventList = [event for event in eventList if event['start']<str(inOneWeek)]
        if len(eventList) == 0:
            heading = "No events this week!"
        else:
            heading = heading + " " + "THIS WEEK"

    if len(eventList) > 0:
        heading = f"__**{heading}**__"

    await ctx.send(heading)

    for event in eventList:
        await ctx.send(f"*{event['start']+event['end']}* **{event['name']}**")

@bot.command()
async def calendar(ctx):
    await ctx.send("[**UF AASU Calendar**](http://www.ufaasu.com/calendar/)")

@bot.command()
async def help(ctx):
    await ctx.send(
'''
**COMMANDS**
!events [suborg] [timeframe]
!calendar

**Suborgs**: AASU, CASA, HEAL, KUSA, FSA, FLP, VSO
**Timeframes**: today, tomorrow, week
''')


bot.run("MTE1MjQ0NzU0ODg3NTg3ODUzMA.G0wcx7.l_GVcVLT7x2FOAyML-9Ulkdps32Uj0W6PHEZos")