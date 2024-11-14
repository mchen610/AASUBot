# twilio_service.py

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import phonenumbers
from singleton import SingletonMeta

class TwilioService(metaclass=SingletonMeta):
    """A service class for interacting with Twilio's API."""
    
    def __init__(self):
        # Twilio configuration
        self.TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')  # Your Twilio Account SID
        self.TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')    # Your Twilio Auth Token
        self.TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID')  # Your Verify Service SID
        self.TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')  # Your Twilio phone number
        
        # Initialize the Twilio client
        self.twilio_client = Client(self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN)
        
        # Access the Verify service
        self.verify_service = self.twilio_client.verify.services(self.TWILIO_VERIFY_SERVICE_SID)
    
    def send_verification_code(self, number):
        """Send a verification code to the given phone number."""
        try:
            verification = self.verify_service.verifications.create(to=number, channel='sms')
            return verification.status
        except TwilioRestException as e:
            print(f"Error sending verification code: {e}")
            return None
    
    def check_verification_code(self, number, code):
        """Check the verification code entered by the user."""
        try:
            result = self.verify_service.verification_checks.create(to=number, code=code)
            return result.status == 'approved'
        except TwilioRestException as e:
            print(f"Error verifying code: {e}")
            return False
    
    def is_valid_phone_number(self, number):
        """Check if the given phone number is valid."""
        try:
            parsed_number = phonenumbers.parse(number)
            is_possible = phonenumbers.is_possible_number(parsed_number)
            lookup = self.twilio_client.lookups.v2.phone_numbers(number).fetch()
            is_valid = lookup.valid
            return is_possible and is_valid
        except Exception as e:
            print(f"Error validating phone number: {e}")
            return False
    
    def send_sms(self, to_number, message):
        """Send an SMS message to the given phone number."""
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            return message.sid
        except TwilioRestException as e:
            print(f"Error sending SMS: {e}")
            return None
