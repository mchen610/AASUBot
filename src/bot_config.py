from datetime import date

# Discord related imports
from discord import Color, Option, User, errors
from discord.ext import tasks
from discord.ext.commands import Context
from config import bot

# Twilio service import
from twilio_service import TwilioService

# Utility imports
from system_messages import send_error_msg, send_pending_msg, send_success_msg
from weather_service import get_weather_msg
from config import google_service
from org_manager import SubOrg, SubOrgManager
from times import get_time

# Import the DBService class
from db_service import DBService

# SubOrgManager Config
# Initialize the organizations with their name, color, Instagram handle, an image link of their logo, and any related keywords to search for when pulling events
orgs = {
    'AASU': SubOrg('Asian American Student Union', Color.dark_magenta(), 'ufaasu', 'https://i.imgur.com/i6fTLuY.png'),
    'CASA': SubOrg('Chinese American Student Association', Color.yellow(), 'ufcasa', 'https://i.imgur.com/R9oWQ8Z.png'),
    'HEAL': SubOrg('Health Educated Asian Leaders', Color.green(), 'ufheal', 'https://i.imgur.com/gvdij9i.png'),
    'KUSA': SubOrg('Korean Undergraduate Student Association', Color.blue(), 'ufkusa', 'https://i.imgur.com/zNME2LE.png'),
    'FSA': SubOrg('Filipino Student Association', Color.red(), 'uffsa', 'https://i.imgur.com/SHNdQTR.png', {'FAHM'}),
    'FLP': SubOrg('First-Year Leadership Program', Color.from_rgb(150, 200, 255), 'ufflp', 'https://i.imgur.com/LtJnLWk.png'),
    'VSO': SubOrg('Vietnamese Student Organization', Color.gold(), 'ufvso', 'https://i.imgur.com/7GvIPS4.png')
}

AASUManager = SubOrgManager(orgs, 'AASU', 'aasu.uf@gmail.com', google_service, lat=29.65, lon=-82.34)

# Create an instance of DBService
db_service = DBService()

# Create an instance of TwilioService
twilio_service = TwilioService()

# Command groups
subscribe = bot.create_group("subscribe", "Subscribe to event reminders.")
unsubscribe = bot.create_group("unsubscribe", "Unsubscribe from event reminders.")

# --- DISCORD FUNCTIONS --- #

@subscribe.command(description="Subscribe to event reminders via Discord.", name="discord")
async def subscribe_discord(ctx: Context):
    user = ctx.author
    user_id = str(user.id)
    valid_users = db_service.get_discord_valid_users()

    if user_id in valid_users:
        await send_error_msg(ctx, "You are already subscribed!")
    else:
        valid_users[user_id] = user.name
        db_service.set_discord_valid_users(valid_users)
        await send_success_msg(ctx, "You are now subscribed!")


@unsubscribe.command(description="Unsubscribe from Discord event reminders.", name="discord")
async def unsubscribe_discord(ctx: Context):
    user = ctx.author
    user_id = str(user.id)
    valid_users = db_service.get_discord_valid_users()

    try:
        del valid_users[user_id]
        db_service.set_discord_valid_users(valid_users)
        await send_success_msg(ctx, "You are now unsubscribed.")
    except KeyError:
        await send_error_msg(ctx, "You are already unsubscribed.")


@tasks.loop(time=get_time(8))
async def send_daily_discord():
    """Scheduled task to send daily Discord notifications to valid users."""

    # Fetch embed for 'AASU' events within 1 day (today)
    embed = AASUManager.embed('AASU', days=1)

    # Check if there are any events
    if "N/A" not in embed.description:
        embed.title = "__AASU Daily__"

        # Fetch valid and invalid users from the database
        valid_users = db_service.get_discord_valid_users()
        invalid_users = db_service.get_discord_invalid_users()

        # Send every valid user the embed and handle newly invalid users
        for user_id in list(valid_users.keys()):
            try:
                user = await bot.get_or_fetch_user(int(user_id))

                # Deletes the last daily message in message history (if any)
                await delete_last_daily(user)

                await user.send(embed=embed)

            # Handles errors if user can no longer be accessed
            except (errors.Forbidden, AttributeError):
                invalid_users[user_id] = valid_users[user_id]
                del valid_users[user_id]

        # Update data on Firebase Realtime Database
        db_service.set_discord_valid_users(valid_users)
        db_service.set_discord_invalid_users(invalid_users)


async def delete_last_daily(user: User):
    """This function reduces clutter by deleting the last message in the message history if it was also a daily message."""

    channel = await bot.create_dm(user)

    # Get last message in channel history
    history = await channel.history(limit=1).flatten()

    # Deletes last daily message if it exists
    try:
        if "AASU Daily" in str(history[0].embeds[0].title):
            await history[0].delete()
    except Exception:
        pass

# --- SMS FUNCTIONS --- #

@subscribe.command(description="Subscribe to event reminders via SMS.")
async def subscribe_sms(ctx: Context, number: Option(str, "Your phone number"), country_code: Option(str, "Your country code (default is '+1' for USA)", default="+1")):
    user = ctx.author
    user_id = str(user.id)
    number = country_code + number

    if twilio_service.is_valid_phone_number(number):
        verified_users = db_service.get_sms_verified_users()

        if user_id in verified_users:
            await send_error_msg(ctx, "You are already subscribed via SMS!")
        else:
            pending_users = db_service.get_sms_pending_users()
            pending_users[user_id] = number
            db_service.set_sms_pending_users(pending_users)

            twilio_service.send_verification_code(number)
            await send_pending_msg(ctx, "Please enter the verification code sent to your phone number using /verify.")
    else:
        await send_error_msg(ctx, "Invalid phone number.")


@unsubscribe.command(description="Unsubscribe from SMS event reminders.")
async def unsubscribe_sms(ctx: Context):
    user = ctx.author
    user_id = str(user.id)

    verified_users = db_service.get_sms_verified_users()

    if user_id in verified_users:
        del verified_users[user_id]
        db_service.set_sms_verified_users(verified_users)
        await send_success_msg(ctx, "You are now unsubscribed from SMS reminders.")
    else:
        await send_error_msg(ctx, "You are already unsubscribed from SMS reminders.")


@bot.command(description="Verify your phone number with the 6-digit code.")
async def verify(ctx, code: Option(str, "6-digit code", min_length=6, max_length=6)):
    user = ctx.author
    user_id = str(user.id)

    verified_users = db_service.get_sms_verified_users()
    pending_users = db_service.get_sms_pending_users()

    if user_id in pending_users:
        if code.isnumeric():
            verifying_number = pending_users[user_id]
            is_approved = twilio_service.check_verification_code(verifying_number, code)

            if is_approved:
                # Transfer user from pending users to verified users
                verified_users[user_id] = verifying_number
                del pending_users[user_id]

                db_service.set_sms_verified_users(verified_users)
                db_service.set_sms_pending_users(pending_users)

                await send_success_msg(ctx, "You are now subscribed via SMS!")
            else:
                await send_error_msg(ctx, "Invalid code. Please try again.")
        else:
            await send_error_msg(ctx, "Invalid code. Please make sure you enter the 6-digit code sent to your phone!")
    elif user_id in verified_users:
        await send_error_msg(ctx, "You are already subscribed via SMS!")
    else:
        await send_error_msg(ctx, "Please begin verification using /subscribe sms.")


@tasks.loop(time=get_time(8))
async def send_daily_sms():
    events_msg = AASUManager.get('AASU').event_list.events_until(1).sms_str()

    if "N/A" not in events_msg:
        today = date.today().strftime('%b %d')
        header = f"✨ Events today, {today} ✨"
        complete_msg = f"{header.center(30, '_')}\n{events_msg}\n{get_weather_msg(AASUManager.lat, AASUManager.lon)}"

        verified_users = db_service.get_sms_verified_users()
        invalid_users = db_service.get_sms_invalid_users()

        for user_id in list(verified_users.keys()):
            to_number = verified_users[user_id]
            message_sid = twilio_service.send_sms(to_number, complete_msg)
            if not message_sid:
                # If sending SMS failed, move user to invalid users
                invalid_users[user_id] = to_number
                del verified_users[user_id]

        db_service.set_sms_verified_users(verified_users)
        db_service.set_sms_invalid_users(invalid_users)
