
import discord
from discord.commands import Option 
from discord.ext import tasks

from datetime import time, timedelta, timezone


from org_manager import SubOrgManager
from config import *
from subscriptions import *

from firebase_admin import db

est = timezone(timedelta(hours=-4))
midnight = time(9, 7, 0, 0, est)
before_midnight = time(5, 6, 0, 0, est)

@tasks.loop(time=midnight)
async def send_daily_sms():
    verified_users = db.reference('users_sms/verified_users').get() or {}
    new_invalid_users = {}
    for id in verified_users:
        try:
            twilio_client.messages \
                .create(
                    body=SubOrgManager.get('AASU').str_msg(1),
                    from_ =  TWILIO_PHONE_NUMBER,
                    to = verified_users[id]
                )
        except:
            new_invalid_users[id] = verified_users[id]
    
    for id in new_invalid_users:
        del verified_users[id]
    
    ref = db.reference('users_sms/invalid_users')
    old_verified_users = ref.get() or {}
    old_verified_users.update(new_invalid_users)
    ref.set(old_verified_users)

async def delete_last_daily(user: discord.User):
    channel = await bot.create_dm(user)
    history = await channel.history(limit=1).flatten()
    if len(history) > 0 and len(history[0].embeds) > 0 and "Today" in str(history[0].embeds[0].author):
        await history[0].delete()

@tasks.loop(time=midnight)
async def send_daily_discord():
    embed = SubOrgManager.get('AASU').embed_msg(1)
    
    data = db.reference('users_discord/id').get() or []
    invalid_indices = [] 
    for index, id in enumerate(data):
        try:
            user = bot.get_user(id)
            await delete_last_daily(user)
            await user.send(embed=embed)
        except:
            invalid_indices.insert(0, index)

    invalid_data = db.reference('users_discord/invalid_id').get() or []
    for index in invalid_indices:
        invalid_data.append(data.pop(index))

    db.reference('users_discord').set({'id': data, 'invalid_id': invalid_data})

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(SubOrgManager.str())
    SubOrgManager.pull_events.start()
    send_daily_sms.start()
    send_daily_discord.start()

@bot.command(description="Get events within the next 30 days or specify a sub-organization or timeframe.")
async def events(ctx, days: Option(int, "Get events within x number of days.", default=30), organization: Option(str, "AASU sub-organization.", default='AASU')):
    org_name = organization.upper()
    embed = SubOrgManager.embed(org_name, days)
    await ctx.respond(embed=embed)

@bot.command(description="Get a description of all the commands.")
async def help(ctx):
    title = "**__AASU BOT COMMANDS__**"
    commands = '''`/events [organization] [days]`: Get events within the next month or optionally specify a sub-organization or timeframe.
  - Organizations: **AASU** | **CASA** | **HEAL** | **KUSA** | **FSA** | **FLP** | **VSO**

`/subscribe`: Subscribe to Discord or SMS reminders.

`/unsubscribe`: Unsubscribe from Discord or SMS reminders.
'''
    embed = discord.Embed(title=title, description=commands, color=discord.Color.dark_theme(), timestamp=datetime.now())
    embed.set_footer(text='Help', icon_url='https://cdn0.iconfinder.com/data/icons/cosmo-symbols/40/help_1-512.png')
    embed.set_thumbnail(url='https://i.imgur.com/i6fTLuY.png')
    await ctx.respond(embed=embed)

bot.run(DISCORD_TEST_TOKEN)