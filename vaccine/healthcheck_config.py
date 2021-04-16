from os import environ

EVENTSTORE_API_URL = environ.get("EVENTSTORE_API_URL")
EVENTSTORE_API_TOKEN = environ.get("EVENTSTORE_API_TOKEN")
TURN_API_URL = environ.get("TURN_API_URL")
TURN_API_TOKEN = environ.get("TURN_API_TOKEN")
GOOGLE_PLACES_URL = "https://maps.googleapis.com"
GOOGLE_PLACES_KEY = environ.get("GOOGLE_PLACES_KEY")
