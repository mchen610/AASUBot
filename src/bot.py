import discord
from discord.commands import Option
from datetime import datetime

from org_manager import SubOrgManager
from config import DISCORD_TOKEN, bot
from subscriptions import *


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await SubOrgManager.pull_events()
    SubOrgManager.pull_events.start()
    send_daily_sms.start()
    send_daily_discord.start()


@bot.command(
    description="Get events within the next 30 days or specify a sub-organization and/or timeframe.",
    options=[
        Option(
            str,
            name="organization",
            description="AASU sub-organization.",
            choices=list(SubOrgManager.orgs.keys()),
            default="AASU",
        ),
        Option(
            int,
            name="days",
            description="Get events within x number of days.",
            default=30,
            min_value=1,
            max_value=90
        )
    ]
)
async def events(ctx, organization: str, days: int):
    """Fetch and display events from a specified sub-organization within a given timeframe."""
    print(SubOrgManager.orgs['AASU'].event_list)
    org_name = organization.upper()
    embed = SubOrgManager.embed(org_name, days)
    await ctx.respond(embed=embed)


@bot.command(description="Get a description of all the commands.")
async def help(ctx):
    title = "**__AASU BOT COMMANDS__**"
    commands = """`/events [organization] [days]`: Get events within the next month or optionally specify a sub-organization or timeframe.
  - Organizations: **AASU** | **CASA** | **HEAL** | **KUSA** | **FSA** | **FLP** | **VSO**

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
    embed.set_thumbnail(url="https://i.imgur.com/i6fTLuY.png")
    await ctx.respond(embed=embed)

bot.run(DISCORD_TOKEN)
