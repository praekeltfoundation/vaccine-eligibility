from os import environ

CALLBACK_API_URL = environ.get("CALLBACK_API_URL", "https://webservices.cci-sa.co.za")
TURN_URL = environ.get("TURN_URL", "https://whatsapp.turn.io")
TURN_TOKEN = environ.get("TURN_TOKEN")
