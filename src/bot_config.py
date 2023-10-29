from datetime import date

# Discord related imports
from discord import Color, Option, User, errors
from discord.ext import tasks
from discord.ext.commands import Context
from config import bot

# Phone number verification imports
from twilio.base.exceptions import TwilioRestException
import phonenumbers
from config import verify_service, twilio_client, TWILIO_PHONE_NUMBER

# Utility imports
from system_messages import send_error_msg, send_pending_msg, send_success_msg
from weather import get_weather_msg
from config import google_service
from org_manager import SubOrg, SubOrgManager
from times import eight_am as loop_time
from firebase_admin import db

#SUBORGMANAGER CONFIG
# Initialize the organizations with their name, color, instagram handle, an image link of their logo, and any related keywords to search for when pulling events
orgs = {
        'AASU': SubOrg('Asian American Student Union', Color.dark_magenta(), 'ufaasu', 'https://i.imgur.com/i6fTLuY.png'),
        'CASA': SubOrg('Chinese American Student Association', Color.yellow(), 'ufcasa', 'https://i.imgur.com/R9oWQ8Z.png'),
        'HEAL': SubOrg('Health Educated Asian Leaders', Color.green(), 'ufheal', 'https://i.imgur.com/gvdij9i.png'),
        'KUSA': SubOrg('Korean Undergraduate Student Association', Color.blue(), 'ufkusa', 'https://i.imgur.com/zNME2LE.png'),
        'FSA': SubOrg('Filipino Student Association', Color.red(), 'uffsa', 'https://i.imgur.com/SHNdQTR.png', {'FAHM'}),
        'FLP': SubOrg('First-Year Leadership Program', Color.from_rgb(150, 200, 255), 'ufflp', 'https://i.imgur.com/LtJnLWk.png'),
        'VSO': SubOrg('Vietnamese Student Organization', Color.gold(), 'ufvso', 'https://i.imgur.com/7GvIPS4.png')
}

AASUManager = SubOrgManager(orgs, 'AASU', 'aasu.uf@gmail.com', google_service)

# Command groups
subscribe = bot.create_group("subscribe", "Subscribe to event reminders.")
unsubscribe = bot.create_group("unsubscribe", "Unsubscribe from event reminders.")

# --- DISCORD FUNCTIONS ---

@subscribe.command(description="Subscribe to event reminders via Discord.", name="discord")
async def disc(ctx: Context):
    user = ctx.author
    user_id = str(user.id)
    valid_users_ref = db.reference('discord/valid_users')
    valid_users = valid_users_ref.get() or {}

    if user_id in valid_users:
        await send_error_msg(ctx, "You are already subscribed!")

    else:
        valid_users[user_id] = user.name
        valid_users_ref.set(valid_users)
        await send_success_msg(ctx, "You are now subscribed!")


@unsubscribe.command(description="Unsubscribe from Discord event reminders.", name="discord")
async def disc(ctx: Context):
    user = ctx.author
    user_id = str(user.id)
    ref = db.reference('discord/valid_users')
    valid_users = ref.get()

    try:
        del valid_users[user_id]
        ref.set(valid_users)        
        await send_success_msg(ctx, "You are now unsubscribed.")

    except:
        await send_error_msg(ctx, "You are already unsubscribed.")


@tasks.loop(time=loop_time)
async def send_daily_discord():
    """Scheduled task to send daily Discord notifications to valid users.

    This task fetches an embed of 'AASU' events on the current day. If the task
    fails to fetch a user, that user is moved to an 'invalid_users' dict.

    """

    # Fetch embed for 'AASU' events within 1 day (today)
    embed = AASUManager.get('AASU').embed(days=1)

    # Check if there are any events
    if "N/A" not in embed.description:
        embed.title = "__AASU Daily__"
        
        # Fetch valid users dictionary from Firebase Realtime Database
        valid_users_ref = db.reference('discord/valid_users')
        valid_users = valid_users_ref.get() or {}

        # Fetch invalid users dictionary from Firebase Realtime Database
        invalid_users_ref = db.reference('discord/invalid_users')
        invalid_users = invalid_users_ref.get() or {}

        # Send every valid user the embed and handle newly invalid users
        # Use list() to generate a copy of the keys to avoid complications from deleting during the loop
        for user_id in list(valid_users.keys()):
            try:    
                user = await bot.get_or_fetch_user(user_id)
                
                # Deletes the last daily message in message history (if any)
                await delete_last_daily(user)

                await user.send(embed=embed)
            
            # Handles errors if user can no longer be accessed (errors.Forbidden) or can no longer be found (AttributeError)
            # Transfers the user information from valid users to invalid users
            except (errors.Forbidden, AttributeError):
                invalid_users[user_id] = valid_users[user_id]
                del valid_users[user_id]

        # Update data on Firebase Realtime Database
        invalid_users_ref.set(invalid_users)
        valid_users_ref.set(valid_users)


async def delete_last_daily(user: User):
    """This function reduces clutter by deleting the last message in the message history if it was also a daily message."""

    channel = await bot.create_dm(user)

    # Get last message in channel history
    history = await channel.history(limit=1).flatten()

    # Deletes last daily message if it exists
    try:
        if "AASU Daily" in str(history[0].embeds[0].title):
            await history[0].delete()
    except:
        pass

# --- SMS FUNCTIONS ---

@subscribe.command(description="Subscribe to event reminders via SMS.")
async def sms(ctx: Context, number: Option(str, "Your phone number"), country_code: Option(str, "Your country code (default is '+1' for USA)", default="+1")):
    user = ctx.author
    user_id = str(user.id)
    number = country_code + number

    try:    
        is_valid_number = phonenumbers.is_possible_number(phonenumbers.parse(number)) and twilio_client.lookups.v2.phone_numbers(number).fetch().valid
    except:
        is_valid_number = False

    if is_valid_number:
        verified_users = db.reference('sms/verified_users').get() or {}

        if user_id in verified_users:
            await send_error_msg(ctx, "You are already subscribed via SMS!")

        else:
            pending_users_ref = db.reference('sms/pending_users')
            pending_users = pending_users_ref.get() or {}

            pending_users[user_id] = number
            pending_users_ref.set(pending_users)
            
            verify_service.verifications.create(to=number, channel='sms')
            await send_pending_msg(ctx, "Please enter the verification code sent to your phone number using `/verify`.")
            
    else:
        await send_error_msg(ctx, "Invalid phone number.")


@unsubscribe.command(description="Unsubscribe from SMS event reminders.")
async def sms(ctx: Context):
    user = ctx.author
    user_id = str(user.id)

    verified_users_ref = db.reference('sms/verified_users')
    verified_users = verified_users_ref.get() or {}

    if user_id in verified_users:
        del verified_users[user_id]
        verified_users_ref.set(verified_users)

        await send_success_msg(ctx, "You are now unsubscribed from SMS reminders.")

    else:
        await send_error_msg(ctx, "You are already unsubscribed from SMS reminders.")


@bot.command(description="Verify your phone number with the 6-digit code.")
async def verify(ctx, code: Option(str, "6-digit code", min_length=6, max_length=6)):
    user = ctx.author
    user_id = str(user.id)

    verified_users_ref = db.reference('sms/verified_users')
    verified_users = verified_users_ref.get() or {}

    pending_users_ref = db.reference('sms/pending_users')
    pending_users = pending_users_ref.get() or {}

    if user_id in pending_users:
        if code.isnumeric():
            verifying_number = pending_users[user_id]
            try:

                # Attempt verification with Twilio
                result = verify_service.verification_checks.create(to=verifying_number, code=code)

                if result.status == 'approved':

                    # Transfer user from verified users to pending users
                    verified_users[user_id] = verifying_number
                    del pending_users[user_id]

                    verified_users_ref.set(verified_users)
                    pending_users_ref.set(pending_users)

                    await send_success_msg(ctx, "You are now subscribed via SMS!")
                    
                else:
                    await send_error_msg(ctx, "Invalid key. Please try again.")
                    
            except TwilioRestException:
                await send_error_msg(ctx, "Your time has passed. Please restart verification using `/subscribe sms`.")
        else:
            await send_error_msg(ctx, "Invalid key. Please make sure you enter the 6-digit key sent to your phone!")
            
    elif user_id in verified_users:
        await send_error_msg(ctx, "You are already subscribed via SMS!")

    else:
        await send_error_msg(ctx, "Please begin verification using `/subscribe sms`.")


@tasks.loop(time=loop_time)
async def send_daily_sms():
    events_msg = AASUManager.get('AASU').event_list.events_until(1).sms_str()

    if "N/A" not in events_msg:
        today = date.today().strftime('%b %d')
        header = f"✨ Events today, {today} ✨"
        complete_msg = f"{header.center(30, '_')}\n{events_msg}\n{get_weather_msg()}"

        verified_users_ref = db.reference('sms/verified_users')
        verified_users = verified_users_ref.get() or {}

        invalid_users_ref = db.reference('sms/invalid_users')
        invalid_users = invalid_users_ref.get() or {}

        for user_id in list(verified_users.keys()):
            try:
                twilio_client.messages \
                    .create(
                        body=complete_msg,
                        from_ =  TWILIO_PHONE_NUMBER,
                        to = verified_users[user_id]
                    )
            except TwilioRestException:
                invalid_users[user_id] = verified_users[user_id]
                del verified_users[user_id]

        verified_users_ref.set(verified_users)
        invalid_users_ref.set(invalid_users)
        



