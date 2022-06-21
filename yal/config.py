from os import environ

API_HOST = environ.get("API_HOST")
API_TOKEN = environ.get("API_TOKEN")
YAL_BOT_LAUNCH_DATE = environ.get("YAL_BOT_LAUNCH_DATE", "2022-05-01")
CONTENTREPO_API_URL = environ.get("CONTENTREPO_API_URL")
MAX_AGE = int(environ.get("MAX_AGE", "122"))
PRIVACY_POLICY_PDF = environ.get("PRIVACY_POLICY_PDF", "1/sample.pdf")
EMERGENCY_NUMBER = environ.get("EMERGENCY_NUMBER", "XXX")
LOVELIFE_URL = environ.get("LOVELIFE_URL")
LOVELIFE_TOKEN = environ.get("LOVELIFE_TOKEN")
