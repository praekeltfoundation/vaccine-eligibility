import re
from datetime import datetime, timedelta, timezone

import aiohttp
import phonenumbers
import pycountry

from yal import config

TZ_SAST = timezone(timedelta(hours=2), "SAST")
PROVINCES = sorted(
    (s.code.split("-")[1], s.name.split(" (")[0])
    for s in pycountry.subdivisions.get(country_code="ZA")
)
GENERIC_ERROR = (
    "Eish 👀, I didn't understand your reply, sorry. Do you mind trying "
    "again? This time, try replying with the number that matches your choice.👍🏽"
)


def get_today():
    return datetime.now(tz=TZ_SAST).date()


def get_current_datetime():
    return datetime.now(tz=TZ_SAST)


def get_turn_api():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.v1+json",
            "User-Agent": "yal-whatsapp-bot",
            "Authorization": f"Bearer {config.API_TOKEN}",
        },
    )


def clean_inbound(content):
    return re.sub(r"\W+", " ", content or "").strip().lower()


def get_bot_age():
    bot_dob = datetime.strptime(config.YAL_BOT_LAUNCH_DATE, "%Y-%m-%d").date()
    return (get_today() - bot_dob).days


def normalise_phonenumber(phonenumber):
    try:
        if not phonenumber.startswith("+"):
            phonenumber = f"+{phonenumber}"
        pn = phonenumbers.parse(phonenumber, None)
        assert phonenumbers.is_possible_number(pn)
        assert phonenumbers.is_valid_number(pn)
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.phonenumberutil.NumberParseException, AssertionError):
        raise ValueError("Invalid phone number")
