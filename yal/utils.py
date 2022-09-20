import re
from datetime import datetime, timedelta, timezone

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
GENDERS = {
    "girl_woman": "Girl/Woman",
    "boy_man": "Boy/Man",
    "non_binary": "Non-binary",
    "other": "Something else",
}
BACK_TO_MAIN = "0. 🏠 *Back* to Main *MENU*"
GET_HELP = "#. 🆘Get *HELP*"


def get_today():
    return datetime.now(tz=TZ_SAST).date()


def get_current_datetime():
    return datetime.now(tz=TZ_SAST)


def clean_inbound(content):
    return re.sub(r"\W+", " ", content or "").strip().lower()


def get_bot_age():
    bot_dob = datetime.strptime(config.YAL_BOT_LAUNCH_DATE, "%Y-%m-%d").date()
    return (get_today() - bot_dob).days


def normalise_phonenumber(phonenumber):
    try:
        if phonenumber.startswith("0"):
            pn = phonenumbers.parse(phonenumber, "ZA")
        else:
            if not phonenumber.startswith("+") and not phonenumber.startswith("0"):
                phonenumber = f"+{phonenumber}"
            pn = phonenumbers.parse(phonenumber, None)
        assert phonenumbers.is_possible_number(pn)
        assert phonenumbers.is_valid_number(pn)
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.phonenumberutil.NumberParseException, AssertionError):
        raise ValueError("Invalid phone number")
