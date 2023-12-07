import discord
from discord.commands import Option
from discord.ext import tasks
from datetime import datetime, timedelta, time

from config import DISCORD_TOKEN, bot, reminder_time, pull_events_time, dst_reset_time
from bot_config import *
from times import bot_tz
from weather import get_weather_embed


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await AASUManager.pull_events()
    AASUManager.pull_events.start()
    send_daily_sms.start()
    send_daily_discord.start()
    reset_tasks_dst.start()


@tasks.loop(time=dst_reset_time())
async def reset_tasks_dst():
    """Resets the task loops when daylight savings time starts or ends."""

    today = datetime.now(bot_tz) + timedelta(seconds=1)
    yesterday = today - timedelta(hours=24)
    if today.dst() != yesterday.dst():
        send_daily_sms.change_interval(reminder_time())
        send_daily_discord.change_interval(reminder_time())
        AASUManager.pull_events.change_interval(pull_events_time())
        reset_tasks_dst.change_interval(dst_reset_time())


@bot.command(
    description="Get events within the next 30 days or specify a sub-organization and/or timeframe.",
    options=[
        Option(
            str,
            name="organization",
            description="AASU sub-organization.",
            choices=list(AASUManager.orgs.keys()),
            default="AASU",
        ),
        Option(
            int,
            name="days",
            description="Get events within x number of days.",
            default=30,
            min_value=1,
            max_value=90,
        ),
    ],
)
async def events(ctx, organization: str, days: int):
    """Fetch and display events from a specified sub-organization within a given timeframe."""
    org_name = organization.upper()
    embed = AASUManager.embed(org_name, days)
    await ctx.respond(embed=embed)
    print(AASUManager.get("AASU"))


@bot.command(description="Get the current weather.")
async def weather(ctx):
    embed = get_weather_embed(AASUManager.lat, AASUManager.lon)
    await ctx.respond(embed=embed)


@bot.command(description="Get a description of all the commands.")
async def help(ctx):
    title = "**__AASU BOT COMMANDS__**"
    commands = f"""`/events [organization] [days]`: Get events within the next month or optionally specify a sub-organization or timeframe.
  - Organizations: {" | ".join([f"**{org}**" for org in AASUManager.orgs.keys()])}

`/subscribe`: Subscribe to Discord or SMS reminders.

`/unsubscribe`: Unsubscribe from Discord or SMS reminders.
"""

    embed = discord.Embed(
        title=title,
        description=commands,
        color=discord.Color.dark_theme(),
        timestamp=datetime.now(),
    )
    embed.set_footer(
        text="Help",
        icon_url="https://cdn0.iconfinder.com/data/icons/cosmo-symbols/40/help_1-512.png",
    )
    embed.set_thumbnail(url=AASUManager.orgs[AASUManager.default_org].img_url)
    await ctx.respond(embed=embed)


bot.run(DISCORD_TOKEN)
