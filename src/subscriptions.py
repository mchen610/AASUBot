from special_messages import send_error_msg, send_pending_msg, send_success_msg
from config import bot, verify_service, twilio_client
from firebase_admin import db
from discord import Option
import phonenumbers

@bot.command(description="Verify your phone number with the 6-digit code.")
async def verify(ctx, code: Option(str, "6-digit code")):
    user = ctx.author
    user_id = str(user.id)

    verified_ref = db.reference('users_sms/verified_users')
    verified_users = verified_ref.get() or {}
    pending_ref = db.reference('users_sms/pending_users')
    pending_users = pending_ref.get() or {}

    if user_id in pending_users:
        if code.isnumeric() and len(code) == 6:
            verifying_number = pending_users[user_id]
            result = verify_service.verification_checks.create(to=verifying_number, code=code)
            if result.status == 'approved':
                verified_users[user_id] = verifying_number
                del pending_users[user_id]
                verified_ref.set(verified_users)
                pending_ref.set(pending_users)

                await send_success_msg(ctx, "You are now subscribed via SMS!")
                
            else:
                await send_error_msg(ctx, "Invalid key. Please try again.")
        else:
            await send_error_msg(ctx, "Invalid key. Please make sure you enter the 6-digit key sent to your phone!")
            
    elif user_id in verified_users:
        await send_error_msg(ctx, "You are already subscribed via SMS!")

    else:
        await send_error_msg(ctx, "Please begin verification using `/subscribe sms`.")


subscribe = bot.create_group("subscribe", "Subscribe to event reminders.")

@subscribe.command(description="Subscribe to event reminders via Discord.")
async def disc(ctx):
    user = ctx.author
    ref = db.reference('users_discord/id')
    data = ref.get() or []
    if user.id in data:
        await send_error_msg(ctx, "You are already subscribed!")
    else:
        data.append(user.id)
        ref.set(data)
        await send_success_msg(ctx, "You are now subscribed!")

@subscribe.command(description="Subscribe to event reminders via SMS.")
async def sms(ctx, number: Option(str, "Your phone number"), country_code: Option(str, "Your country code (default is '+1' for USA)", default="+1")):
    user = ctx.author
    number = country_code + number

    try:    
        is_valid_number = phonenumbers.is_possible_number(phonenumbers.parse(number)) and twilio_client.lookups.v2.phone_numbers(number).fetch().valid
    except:
        is_valid_number = False

    if is_valid_number:
        verified_users = db.reference('users_sms/verified_users').get() or {}

        if str(user.id) in verified_users:
            await send_error_msg(ctx, "You are already subscribed via SMS!")

        else:
            ref = db.reference('users_sms/pending_users')
            data = ref.get() or {}
            data[user.id] = number
            ref.set(data)
            verify_service.verifications.create(to=number, channel='sms')
            await send_pending_msg(ctx, "Please enter the verification code sent to your phone number using `/verify`.")
            
    else:
        await send_error_msg(ctx, "This phone number does not exist!")


unsubscribe = bot.create_group("unsubscribe", "Unsubscribe from event reminders.")

@unsubscribe.command(description="Unsubscribe from Discord event reminders.")
async def disc(ctx):
    user = ctx.author
    ref = db.reference('users_discord/id')
    data = ref.get()
    try:
        data.remove(user.id)
        ref.set(data)        
        await send_success_msg(ctx, "You are now unsubscribed.")
    except:
        await send_error_msg(ctx, "You are already unsubscribed.")

@unsubscribe.command(description="Unsubscribe from SMS event reminders.")
async def sms(ctx):
    user = ctx.author
    ref = db.reference('users_sms/verified_users')
    data = ref.get() or {}

    if str(user.id) in data:
        del data[str(user.id)]
        ref.set(data)
        await send_success_msg(ctx, "You are now unsubscribed from SMS reminders.")
    else:
        await send_error_msg(ctx, "You are already unsubscribed from SMS reminders.")
