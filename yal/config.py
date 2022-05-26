from os import environ

API_HOST = environ.get("API_HOST")
API_TOKEN = environ.get("API_TOKEN")
YAL_BOT_LAUNCH_DATE = environ.get("YAL_BOT_LAUNCH_DATE", "2022-05-01")
CONTENTREPO_API_URL = environ.get("CONTENTREPO_API_URL")
MAX_AGE = int(environ.get("MAX_AGE", "122"))
