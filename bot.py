from dotenv import load_dotenv

import discord
from discord.commands import Option 
from discord.ext import tasks

from datetime import date, datetime, timedelta
from dateutil.parser import parse as date_parse

from googleapiclient.discovery import build

import os

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


twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
verify_service = twilio_client.verify.v2.services(TWILIO_VERIFY_SID)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  

bot = discord.Bot(intents=intents, activity=discord.Activity(type=3, name="/help"), status=discord.Status.online)

#path to Firebase credentials
cred = credentials.Certificate("service_account_key.json") 
firebase_admin.initialize_app(cred, {'databaseURL': "https://aasu-discord-bot-default-rtdb.firebaseio.com/"})

allEvents: list[dict[str, str]] = []
subOrgEvents: dict = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []}

@tasks.loop(hours=24.0)
async def get_events():
    global allEvents
    global subOrgEvents

    newEvents = [];
    newSubOrgEvents = {'AASU': [], 'CASA': [], 'HEAL': [], 'KUSA': [], 'FSA': [], 'FLP': [], 'VSO': []};
    
    service = build('calendar', 'v3', developerKey=GOOGLE_CALENDAR_API_KEY)

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
        if "FAHM" in name and "FSA" not in name:
            newSubOrgEvents['FSA'].append(newEvent)

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

    msg = await get_daily_sms()
    data = db.reference('users_sms/verified_users').get() or {}
    for id in data:
        twilio_client.messages \
            .create(
                body=msg,
                from_ =  TWILIO_PHONE_NUMBER,
                to = data[str(id)]
            )


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
    ref = db.reference('users_discord')
    data = ref.get() or {'id': [], 'invalid_id': []}
    for id in data['id']:
        user = bot.get_user(id)
        try:
            await user.send(msg)
        except:
            try:
                data['invalid_id'].append(id)
            except:
                data['invalid_id'] = [id]
            ref.set(data)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}") 
    get_events.start()
    send_daily_sms.start()
    send_daily_discord.start()


@bot.command(description="Get events within the next month or optionally specify a sub-organization or timeframe.")
async def events(ctx, timeframe: Option(str, "Get events within a certain timeframe (today, tomorrow, this week)", default=''), suborg: Option(str, "AASU sub-organization", default='')):
    suborg = suborg.upper()
    timeframe = timeframe.upper()
    if suborg in subOrgEvents or suborg == '':
        if suborg in subOrgEvents:
            eventList = subOrgEvents[suborg]
            heading = f"{suborg} EVENTS"
        elif suborg == '':
            eventList = allEvents
            heading = "ALL AASU EVENTS"
    
        timeframes = {"TODAY": date.today(), "TOMORROW": date.today()+timedelta(1), "WEEK": date.today()+timedelta(7), "THIS WEEK": date.today()+timedelta(7), '': date.today()+timedelta(30)}
        if timeframe in timeframes:
            eventList = [event for event in eventList if (datetime.strptime(event['start'], '%Y-%m-%d').date()<=timeframes[timeframe])]
            if timeframe == "WEEK":
                timeframe = "THIS WEEK"
            if len(eventList) == 0:
                if suborg == '':
                    await ctx.respond(f"Absolutely no events {timeframe.lower()}!")
                else:
                    await ctx.respond(f"No {suborg} events {timeframe.lower()}!")
            else:
                heading = heading + " " + timeframe
            
                msg = f"__**{heading}**__\n"

                for event in eventList:
                    msg = msg+'\n*'+event['start']
                    if event['end']!=event['start']:
                        msg = msg + " **-** " + event['end']
                    msg = msg + f"* **{event['name']}**"
                await ctx.respond(msg)
        else:
            await ctx.respond("Error: Invalid timeframe.")
    else:
        await ctx.respond("Error: Invalid suborg.")

@bot.command(description="Get the link to AASU's calendar.")
async def calendar(ctx):
    await ctx.respond("[**UF AASU Calendar**](http://www.ufaasu.com/calendar/)")

@bot.command(description="Get a description of all the commands.")
async def help(ctx):
    await ctx.respond(
'''
**COMMANDS:**

- `/events [suborg] [timeframe]`: Get events within the next month or optionally specify a sub-organization or timeframe.
  - *Suborgs: AASU, CASA, HEAL, KUSA, FSA, FLP, VSO*
  - *Timeframes: today, tomorrow, week*

- `/calendar`: Get the link to AASU's calendar.

- `/subscribe`: Subscribe to Discord or SMS reminders.

- `/unsubscribe`: Unsubscribe from Discord or SMS reminders.
''')


@bot.command(description="Verify your phone number with the 6-digit code.")
async def verify(ctx, code: Option(str, "6-digit code")):
    user = ctx.author

    ref = db.reference('users_sms')
    data = ref.get() or {'verified_users': {}, 'pending_users': {}}

    if str(user.id) in data['pending_users']:
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

                await ctx.respond("You are now subscribed via SMS!")
                
            else:
                await ctx.respond("Error: Invalid key. Please try again.")
        else:
            await ctx.respond("Error: Invalid key. Please make sure you enter the 6-digit key sent to your phone!")
            
    elif 'verified_users' in data and str(user.id) in data['verified_users']:
        await ctx.respond("Error: You are already subscribed via SMS!")

    else:
        await ctx.respond("Error: Please begin verification using `/subscribe sms`.")

subscribe = bot.create_group("subscribe", "Subscribe to event reminders.")

@subscribe.command(description="Subscribe to event reminders via Discord.")
async def discord(ctx):
    user = ctx.author
    ref = db.reference('users_discord/id')
    data = ref.get() or []
    if user.id in data:
        await ctx.respond("Error: You are already subscribed!")
    else:
        data.append(user.id)
        ref.set(data)
        await ctx.respond("You are now subscribed!")

@subscribe.command(description="Subscribe to event reminders via SMS.")
async def sms(ctx, number: Option(str, "Your phone number"), country_code: Option(str, "Your country code (default is '+1' for USA)", default="+1")):
    user = ctx.author
    number = country_code + number

    try:    
        is_valid_number = phonenumbers.is_possible_number(phonenumbers.parse(number)) and twilio_client.lookups.v2.phone_numbers(number).fetch().valid
    except:
        is_valid_number = False

    if is_valid_number:
        ref = db.reference('users_sms')
        data = ref.get() or {'verified_users': {}, 'pending_users': {}}

        if 'verified_users' in data and str(user.id) in data['verified_users']:
            await ctx.respond("Error: You are already subscribed via SMS!")

        else:
            data['pending_users'][user.id] = number
            ref.set(data)
            verify_service.verifications.create(to=number, channel='sms')
            await ctx.respond("Please enter the verification code sent to your phone number using `/verify`.")
            
    else:
        ctx.respond("Error: This phone number does not exist!")


unsubscribe = bot.create_group("unsubscribe", "Unsubscribe from event reminders.")

@unsubscribe.command(description="Unsubscribe from Discord event reminders.")
async def discord(ctx):
    user = ctx.author
    ref = db.reference('users_discord/id')
    data = ref.get() or []
    try:
        data.remove(user.id)
        ref.set(data)        
        await ctx.respond("You are now unsubscribed.")
    except:
        await ctx.respond("Error: You are already unsubscribed.")


@unsubscribe.command(description="Unsubscribe from SMS event reminders.")
async def sms(ctx):
    user = ctx.author
    ref = db.reference('users_sms')
    data = ref.get()

    try:
        del data['verified_users'][str(user.id)]
        ref.set(data)
        await ctx.respond("You are now unsubscribed from SMS reminders.")
    except:
        await ctx.respond("Error: You are already unsubscribed from SMS reminders.")
    

bot.run(DISCORD_AASU_BOT_TOKEN)