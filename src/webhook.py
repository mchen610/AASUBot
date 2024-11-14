from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from db_service import DBService
from config import TWILIO_AUTH_TOKEN

app = Flask(__name__)

db = DBService()


def validate_twilio_request(f):
    """Decorator to validate that the request is from Twilio"""

    def decorated_function(*args, **kwargs):
        # Your Twilio Auth Token from environment variables
        validator = RequestValidator(TWILIO_AUTH_TOKEN)

        # Get the request URL and POST data
        scheme = request.headers.get(
            "X-Forwarded-Proto", "http"
        )  # Default to 'http' if header is absent
        host = request.headers.get("X-Forwarded-Host", request.host)
        url = f"{scheme}://{host}{request.path}"

        post_data = request.form

        # Get the X-Twilio-Signature header
        signature = request.headers.get("X-Twilio-Signature", "")
        # Validate the request
        if validator.validate(url, post_data, signature):
            return f(*args, **kwargs)
        else:
            return "Invalid request", 403

    return decorated_function


@app.route("/sms", methods=["POST"])
@validate_twilio_request
def handle_sms():
    # Get the message body and phone number
    incoming_msg = request.form.get("Body", "").strip().upper()
    from_number = request.form.get("From", "")

    # Create a response object
    resp = MessagingResponse()

    print(incoming_msg, from_number)

    if incoming_msg in ("STOP", "UNSUBSCRIBE", "END", "QUIT", "STOPALL", "CANCEL"):
        # Handle the STOP request
        try:
            users = db.get_sms_verified_users()
            for user_id, user_number in users.items():
                if from_number in user_number or user_number in from_number:
                    del users[user_id]
                    db.set_sms_verified_users(users)

            resp.message('You have succesfully unsubscribed from AASU reminders. Text "SUBSCRIBE" to undo.')

        except Exception as e:
            # Log the error
            print(f"Error handling STOP request: {e}")
            return str(resp)

    if incoming_msg in ("SUBSCRIBE", "START", "UNSTOP"):
        verified_users = db.get_sms_verified_users()
        verified_users[from_number] = from_number
        db.set_sms_verified_users(verified_users)
        
        resp.message('You have succesfully subscribed to AASU reminders! Text "STOP" to unsubscribe.')

    if incoming_msg == "STATUS":
        verified_users = db.get_sms_verified_users()
        if from_number in verified_users.values():
            resp.message('Subscription status: you are subscribed. TEXT "STOP" to unsubscribe.')
        else:
            resp.message('You are not subscribed. Text "SUBSCRIBE" to subscribe.')
            
    if incoming_msg == "COMMANDS":
        resp.message('Text "STOP" to unsubscribe or "SUBSCRIBE" to subscribe. Text "COMMANDS" for commands and "STATUS" to view your subscription status.')

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=3000)
