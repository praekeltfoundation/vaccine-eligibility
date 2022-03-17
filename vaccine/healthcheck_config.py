from os import environ

EVENTSTORE_API_URL = environ.get("EVENTSTORE_API_URL")
EVENTSTORE_API_TOKEN = environ.get("EVENTSTORE_API_TOKEN")
TURN_API_URL = environ.get("TURN_API_URL")
TURN_API_TOKEN = environ.get("TURN_API_TOKEN")
GOOGLE_PLACES_URL = "https://maps.googleapis.com"
GOOGLE_PLACES_KEY = environ.get("GOOGLE_PLACES_KEY")
RAPIDPRO_URL = environ.get("RAPIDPRO_URL")
RAPIDPRO_TOKEN = environ.get("RAPIDPRO_TOKEN")
RAPIDPRO_PRIVACY_POLICY_SMS_FLOW = environ.get("RAPIDPRO_PRIVACY_POLICY_SMS_FLOW")
TB_USSD_CODE = environ.get("TB_USSD_CODE", "")
EXTERNAL_REGISTRATIONS_V2 = environ.get("EXTERNAL_REGISTRATIONS_V2")
