import discord
from discord.ext import commands, tasks

from datetime import date, datetime, timedelta
from dateutil.parser import parse as date_parse
from pytz import timezone

from googleapiclient.discovery import build

import os
import json

from twilio.rest import Client

API_KEY = os.environ['GOOGLE_CALENDAR_API_KEY']

allEvents: list[dict[str, str]] = [];
subOrgEvents: dict = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []};

intents = discord.Intents.default()
intents.members = True
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents, activity=discord.Activity(type=3, name="!help"), status=discord.Status.online)
bot.remove_command('help')

@tasks.loop(hours=24.0)
async def get_events():
    global allEvents
    global subOrgEvents

    newEvents = [];
    newSubOrgEvents = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []};

    service = build('calendar', 'v3', developerKey=API_KEY)

    today = datetime.utcnow()
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
        newEvent = {'name': name, 'start': start, 'end': end}

        newEvents.append(newEvent)
        for org in newSubOrgEvents:
            if org in name:
                newSubOrgEvents[org].append(newEvent)

    allEvents = newEvents
    subOrgEvents = newSubOrgEvents

async def get_daily_sms():
    msg = "No events today!";
    tomorrow = date.today()+timedelta(days=1)
    eventList = [event for event in allEvents if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=tomorrow)]
    if len(eventList) > 0:
        msg = "IMMEDIATE EVENTS\n"
        for event in eventList:
            msg = msg+'\n'+event['start'][5:]
            if event['end']!=event['start']:
                msg = msg + " ➾ " + event['end'][5:]
            msg = msg + ": " + event['name']
    return msg


@tasks.loop(hours=24.0)
async def send_daily_sms():

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']

    client = Client(account_sid, auth_token)
    
    msg = await get_daily_sms()
    with open('numbers.json', 'r+') as file:
        data = json.load(file)
        valid_numbers = []
        for number in data['numbers']:
            try:
                client.messages \
                    .create(
                        body=msg,
                        from_ =  "+18336331775",
                        to = number
                    )
                valid_numbers.append(number)
            except:
                if number not in data['invalid_numbers']:
                    data['invalid_numbers'].append(number)
        data['numbers'] = valid_numbers
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

async def get_daily_discord():
    msg = "No events today!";
    tomorrow = date.today()+timedelta(days=1)
    eventList = [event for event in allEvents if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=tomorrow)]
    if len(eventList) > 0:
        msg = "__**IMMEDIATE EVENTS**__\n"
        for event in eventList:
            msg = msg+'\n*'+event['start']
            if event['end']!=event['start']:
                msg = msg + " **-** " + event['end']
            msg = msg + f"* **{event['name']}**"
    return msg

@tasks.loop(hours=24.0)
async def send_daily_discord():
    msg = await get_daily_discord()
    try:
        with open('discord_users.json', 'r+') as file:
            data = json.load(file)
            for username in data['usernames']:
                user = discord.utils.get(bot.users, name=username)
                if user:
                    await user.send(msg)
                else:
                    print("User not found: " + username)
    except:
        print("No subscriptions :(")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}") 
    get_events.start()
    send_daily_sms.start()
    send_daily_discord.start()


@bot.command()
async def events(ctx, *args):
    eventList: list = [];
    heading = "EVENTS"

    args = list(args)
    for i in range(len(args)):
        args[i] = args[i].upper()
    print(args)

    for org in set(args) & set(subOrgEvents):
        eventList = eventList + subOrgEvents[org]
        heading = org+" "+heading

    eventList.sort(key=lambda x: x['start'])

    if len(eventList) == 0:
        eventList = allEvents
        heading = "ALL AASU EVENTS"


    timeframes = {"TODAY": date.today(), "TOMORROW": date.today()+timedelta(1), "WEEK": date.today()+timedelta(7)}
    numTimeFrames = 0;
    for timeframe in timeframes: 
        if timeframe in args:
            numTimeFrames+=1
            if numTimeFrames > 1:
                await ctx.send("Please only enter one timeframe!")
                break
            eventList = [event for event in eventList if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=timeframes[timeframe])]
            human_str = timeframe
            human_str = human_str.replace("WEEK", "THIS WEEK")
            if len(eventList) == 0:
                await ctx.send(f"No events {human_str.lower()}!")
            else:
                heading = heading + " " + human_str
        
    if len(eventList) > 0 and numTimeFrames<=1:
        msg = f"__**{heading}**__\n"
          
        for event in eventList:
            msg = msg+'\n*'+event['start']
            if event['end']!=event['start']:
                msg = msg + " **-** " + event['end']
            msg = msg + f"* **{event['name']}**"
        await ctx.send(msg)

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
!subscibe
!unsubscribe

**Suborgs**: AASU, CASA, HEAL, KUSA, FSA, FLP, VSO
**Timeframes**: today, tomorrow, week
''')
    
@bot.command()
async def subscribe(ctx):
    user = ctx.author
    
    try:
        with open("discord_users.json", "r+") as file:
            data = json.load(file)
            if user.name not in data['usernames']:
                data['usernames'].append(user.name)
                await ctx.send("You are now subscribed!")
            else:
                await ctx.send("You are already subscribed!")
    except:
        data = {'usernames': [user.name]};

    with open("discord_users.json", "w") as file:       
        json.dump(data, file, indent=4)

@bot.command()
async def unsubscribe(ctx):
    user = ctx.author
    
    try:
        with open("discord_users.json", "r+") as file:
            data = json.load(file)
            if user.name in data['usernames']:
                data['usernames'].remove(user.name)
                await ctx.send("You are now unsubscribed!")
                with open("discord_users.json", "w") as file:       
                    json.dump(data, file, indent=4)
            else:
                await ctx.send("You are already unsubscribed!")
                
    except:
        await ctx.send("You are already unsubscribed!")




bot.run("MTE1MjQ0NzU0ODg3NTg3ODUzMA.G0wcx7.l_GVcVLT7x2FOAyML-9Ulkdps32Uj0W6PHEZos")