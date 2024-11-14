from config import FIREBASE_REALTIME_DATABASE_URL
from singleton import SingletonMeta
from firebase_admin import credentials, db, initialize_app


cred = credentials.Certificate("service_account_key.json") 
initialize_app(cred, {"databaseURL": FIREBASE_REALTIME_DATABASE_URL})


class DBService(metaclass=SingletonMeta):
    def __init__(self):
        self.discord_valid_users_ref = db.reference('discord/valid_users')
        self.discord_invalid_users_ref = db.reference('discord/invalid_users')
        self.sms_verified_users_ref = db.reference('sms/verified_users')
        self.sms_pending_users_ref = db.reference('sms/pending_users')
        self.sms_invalid_users_ref = db.reference('sms/invalid_users')

    # Discord Related Methods
    def get_discord_valid_users(self):
        return self.discord_valid_users_ref.get() or {}

    def set_discord_valid_users(self, valid_users):
        self.discord_valid_users_ref.set(valid_users)

    def get_discord_invalid_users(self):
        return self.discord_invalid_users_ref.get() or {}

    def set_discord_invalid_users(self, invalid_users):
        self.discord_invalid_users_ref.set(invalid_users)

    # SMS Related Methods
    def get_sms_verified_users(self):
        return self.sms_verified_users_ref.get() or {}

    def set_sms_verified_users(self, verified_users):
        self.sms_verified_users_ref.set(verified_users)

    def get_sms_pending_users(self):
        return self.sms_pending_users_ref.get() or {}

    def set_sms_pending_users(self, pending_users):
        self.sms_pending_users_ref.set(pending_users)

    def get_sms_invalid_users(self):
        return self.sms_invalid_users_ref.get() or {}

    def set_sms_invalid_users(self, invalid_users):
        self.sms_invalid_users_ref.set(invalid_users)
