from dotenv import load_dotenv
import os

import discord
from discord.commands import Option 
from discord.ext import tasks

from datetime import date, time, datetime, timedelta, timezone
from dateutil.parser import parse as date_parse

from googleapiclient.discovery import build

from twilio.rest import Client
import phonenumbers

import firebase_admin
from firebase_admin import credentials, db

#ENV VARIABLES
load_dotenv()
GOOGLE_CALENDAR_API_KEY = os.environ['GOOGLE_CALENDAR_API_KEY']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_VERIFY_SID = os.environ['TWILIO_VERIFY_SID']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
DISCORD_AASU_BOT_TOKEN=os.environ['DISCORD_AASU_BOT_TOKEN']

#DISCORD CONFIG
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  
bot = discord.Bot(intents=intents, activity=discord.Activity(type=3, name="/help"), status=discord.Status.online)

#TWILIO CONFIG
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
verify_service = twilio_client.verify.v2.services(TWILIO_VERIFY_SID)

#FIREBASE CONFIG
cred = credentials.Certificate("service_account_key.json") 
firebase_admin.initialize_app(cred, {'databaseURL': "https://aasu-discord-bot-default-rtdb.firebaseio.com/"})

#GLOBALS
subOrgEvents = {'ALL': [], 'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []}
subOrgColors = {'ALL': discord.Color.dark_theme(),  'AASU': discord.Color.dark_theme(), 'CASA': discord.Color.red(), 'HEAL': discord.Color.green(), 'KUSA': discord.Color.blue(), 'FSA': discord.Color.red(), 'FLP': discord.Color.from_rgb(255, 255, 255), 'VSO': discord.Color.orange()}
est = timezone(timedelta(hours=-4))
midnight = time(5, 3, 0, 0, est)
before_midnight = time(5, 2, 0, 0, est)

@tasks.loop(time=before_midnight)
async def update_events():

    newSubOrgEvents = {'ALL': [], 'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []}
    
    today = datetime.utcnow()
    today.replace(hour=0, minute=0, second=0, microsecond=0)
    inOneMonth = today + timedelta(days=30)

    timeMin = today.isoformat() + 'Z'
    timeMax = inOneMonth.isoformat() + 'Z'

    service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)
    events_result = service.events().list(calendarId='aasu.uf@gmail.com', timeMin=timeMin, timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    for event in events:
        try:
            name = event['summary']
            start = date_parse(event['start'].get('date')).date()
            end = date_parse(event['end'].get('date')).date()
            length = (end - start).days
            for i in range(length):
                start = date_parse(event['start'].get('date')).date()+timedelta(days=i)
                newEvent = {'name': name, 'start': start}

                newSubOrgEvents['ALL'].append(newEvent)
                for org in newSubOrgEvents:
                    if org in name:
                        newSubOrgEvents[org].append(newEvent)
                if "FAHM" in name and "FSA" not in name:
                    newSubOrgEvents['FSA'].append(newEvent)
        except:
            pass

    global subOrgEvents
    subOrgEvents = newSubOrgEvents

def get_events_embed(header: str, suborg: str = 'ALL', timeframe: str = ''):
    timeframes = {"TODAY": date.today(), "TOMORROW": date.today()+timedelta(1), "WEEK": date.today()+timedelta(7), "THIS WEEK": date.today()+timedelta(7)}

    try:
        eventList = [event for event in subOrgEvents[suborg] if event['start']<=timeframes[timeframe.upper()]]
    except:
        eventList = subOrgEvents[suborg]

    msg = '\n'
    for event in eventList:
        start = event['start'].strftime('%a, %b %d')
        msg = f"{msg}\n{start}: **{event['name']}**"
    
    if msg == '\n':
        msg = f"{msg}**No events!**"

    embed = discord.Embed(title=header, description=msg, color=subOrgColors[suborg], timestamp=datetime.now())
    return embed

def get_error_embed(msg: str):
    return discord.Embed(description=f"Error: **{msg}**", color=discord.Color.red(), timestamp=datetime.now())

def get_pending_embed(msg: str):
    return discord.Embed(description=f"Pending: **{msg}**", color=discord.Color.yellow(), timestamp=datetime.now())

def get_success_embed(msg: str):
    return discord.Embed(description=f"Success: **{msg}**", color=discord.Color.brand_green(), timestamp=datetime.now())

def get_daily_sms():
    msg = "No events today!"
    
    tomorrow = date.today()+timedelta(days=1)
    eventList = [event for event in eventList if event['start']<=tomorrow]
    if len(eventList) > 0:
        msg = "IMMEDIATE EVENTS\n"
        for event in eventList:
            start = event['start'].strftime('%a, %b %d')
            msg = f"{msg}\n{start}: {event['name']}"
    return msg

@tasks.loop(time=midnight)
async def send_daily_sms():

    msg = get_daily_sms()
    data = db.reference('users_sms/verified_users').get() or {}
    for id in data:
        twilio_client.messages \
            .create(
                body=msg,
                from_ =  TWILIO_PHONE_NUMBER,
                to = data[str(id)]
            )

#TESTED
@tasks.loop(time=midnight)
async def send_daily_discord():
    header = "__**IMMEDIATE EVENTS**__"
    embed = get_events_embed(header, timeframe = "TOMORROW")
    ref = db.reference('users_discord')
    data = ref.get() or {'id': [], 'invalid_id': []}
    for id in data['id']:
        user = bot.get_user(id)
        try:
            channel = await bot.create_dm(user)
            last_message = await channel.history(limit=1).next()
            if header in last_message.embeds[0].title:
                await last_message.delete()
            await user.send(embed=embed)
        except:
            try:
                data['invalid_id'].append(id)
            except:
                data['invalid_id'] = [id]
            ref.set(data)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}") 
    await update_events()
    update_events.start()
    send_daily_sms.start()
    send_daily_discord.start()

@bot.command(description="Get events within the next month or optionally specify a sub-organization or timeframe.")
async def events(ctx, timeframe: Option(str, "Get events within a certain timeframe (today, tomorrow, this week)", default=''), suborg: Option(str, "AASU sub-organization", default='ALL')):
    suborg = suborg.upper()
    timeframe = timeframe.upper()
    if suborg in subOrgEvents:
        timeframes = ['TODAY', 'TOMORROW', 'WEEK', 'THIS WEEK', '']
        if timeframe in timeframes:
            if timeframe == "WEEK":
                timeframe = "THIS WEEK"
            header = F"__**{suborg} EVENTS {timeframe}**__"
            embed = get_events_embed(header, suborg, timeframe)
            await ctx.respond(embed=embed)
        else:
            embed = get_error_embed("Invalid timeframe.")
            await ctx.respond(embed=embed)
    else:
        embed = get_error_embed("Invalid suborg.")
        await ctx.respond(embed=embed)


@bot.command(description="Verify your phone number with the 6-digit code.")
async def verify(ctx, code: Option(str, "6-digit code")):
    user = ctx.author

    ref = db.reference('users_sms')
    data = ref.get() or {}

    if 'pending_users' in data and str(user.id) in data['pending_users']:
        if code.isnumeric() and len(code) == 6:
            verifying_number = data['pending_users'][str(user.id)]
            result = verify_service.verification_checks.create(to=verifying_number, code=code)
            if result.status == 'approved':
                try:
                    data['verified_users'][user.id] = verifying_number
                except:
                    data['verified_users'] = {user.id: verifying_number}
                del data['pending_users'][str(user.id)]
                ref.set(data)

                embed = get_success_embed("You are now subscribed via SMS!")
                await ctx.respond(embed=embed)
                
            else:
                embed = get_error_embed("Invalid key. Please try again.")
                await ctx.respond(embed=embed)
        else:
            embed = get_error_embed("Invalid key. Please make sure you enter the 6-digit key sent to your phone!")
            await ctx.respond(embed=embed)
            
    elif 'verified_users' in data and str(user.id) in data['verified_users']:
        embed = get_error_embed("You are already subscribed via SMS!")
        await ctx.respond(embed=embed)

    else:
        embed = get_error_embed("Please begin verification using `/subscribe sms`.")
        await ctx.respond(embed=embed)

subscribe = bot.create_group("subscribe", "Subscribe to event reminders.")

@subscribe.command(description="Subscribe to event reminders via Discord.")
async def disc(ctx):
    user = ctx.author
    ref = db.reference('users_discord/id')
    data = ref.get() or []
    if user.id in data:
        embed = get_error_embed("You are already subscribed!")
        await ctx.respond(embed=embed)
    else:
        data.append(user.id)
        ref.set(data)
        embed = get_success_embed("You are now subscribed!")
        await ctx.respond(embed=embed)

@subscribe.command(description="Subscribe to event reminders via SMS.")
async def sms(ctx, number: Option(str, "Your phone number"), country_code: Option(str, "Your country code (default is '+1' for USA)", default="+1")):
    user = ctx.author
    number = country_code + number

    try:    
        is_valid_number = phonenumbers.is_possible_number(phonenumbers.parse(number)) and twilio_client.lookups.v2.phone_numbers(number).fetch().valid
    except:
        is_valid_number = False

    if is_valid_number:
        verified_users = db.reference('users_sms/verified_users').get()

        if verified_users and str(user.id) in verified_users:
            embed = get_error_embed("You are already subscribed via SMS!")
            await ctx.respond(embed=embed)

        else:
            ref = db.reference('users_sms/pending_users')
            data = ref.get() or {}
            data[user.id] = number
            ref.set(data)
            verify_service.verifications.create(to=number, channel='sms')
            embed = get_pending_embed("Please enter the verification code sent to your phone number using `/verify`.")
            await ctx.respond(embed=embed)
            
    else:
        embed = get_error_embed("This phone numbre does not exist!")
        await ctx.respond(embed=embed)


unsubscribe = bot.create_group("unsubscribe", "Unsubscribe from event reminders.")

@unsubscribe.command(description="Unsubscribe from Discord event reminders.")
async def disc(ctx):
    user = ctx.author
    ref = db.reference('users_discord/id')
    data = ref.get()
    try:
        data.remove(user.id)
        ref.set(data)        
        embed = get_success_embed("You are now unsubscribed.")
        await ctx.respond(embed=embed)
    except:
        embed = get_error_embed("You are already unsubscribed.")
        await ctx.respond(embed=embed)

@unsubscribe.command(description="Unsubscribe from SMS event reminders.")
async def sms(ctx):
    user = ctx.author
    ref = db.reference('users_sms/verified_users')
    data = ref.get()

    try:
        del data[str(user.id)]
        ref.set(data)
        embed = get_success_embed("You are now unsubscribed from SMS reminders.")
        await ctx.respond(embed=embed)
    except:
        embed = get_error_embed("You are already unsubscribed from SMS reminders.")
        await ctx.respond(embed=embed)

@bot.command(description="Get the link to AASU's calendar.")
async def calendar(ctx):
    await ctx.respond("[**UF AASU Calendar**](http://www.ufaasu.com/calendar/)")

@bot.command(description="Get a description of all the commands.")
async def help(ctx):
    await ctx.respond(
'''
**__COMMANDS__**

- `/events [suborg] [timeframe]`: Get events within the next month or optionally specify a sub-organization or timeframe.
  - *Suborgs: AASU, CASA, HEAL, KUSA, FSA, FLP, VSO*
  - *Timeframes: today, tomorrow, week*

- `/calendar`: Get the link to AASU's calendar.

- `/subscribe`: Subscribe to Discord or SMS reminders.

- `/unsubscribe`: Unsubscribe from Discord or SMS reminders.
''')
    
bot.run(DISCORD_AASU_BOT_TOKEN)