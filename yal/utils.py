import random
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
GENERIC_ERRORS = (
    "Oh oh 👀, I don't understand your reply. But don't worry, we can try again. This "
    "time, please reply with the number that matches your choice.👍🏽",
    "Oops, looks like I don't have that option available.🤔Please try again - I'll get "
    "it if you use the number that matches your choice, promise.👍",
    "Umm...I'm sorry but I'm not sure what that means [persona_emoji]. You can help "
    "me by trying again. This time, look for the number matching your choice and send "
    "that👍🏽",
)
GENDERS = {
    "female": "Female",
    "male": "Male",
    "non_binary": "Non-binary",
    "other": "None of these",
    "rather_not_say": "Rather not say",
}
BACK_TO_MAIN = "0. 🏠 *Back* to Main *MENU*"
GET_HELP = "#. 🆘Get *HELP*"
PERSONA_FIELDS = ["persona_emoji", "persona_name"]
PERSONA_DEFAULTS = {"persona_emoji": "🤖", "persona_name": "B-wise"}


def get_generic_error():
    return random.choice(GENERIC_ERRORS)


def get_today():
    return datetime.now(tz=TZ_SAST).date()


def get_current_datetime():
    return datetime.now(tz=TZ_SAST)


def clean_inbound(content):
    return re.sub(r"[^\w#]+", " ", content or "").strip().lower()


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


def replace_persona_fields(text, metadata={}):
    for key in PERSONA_FIELDS:
        if key in metadata and metadata[key].lower() != "skip":
            text = text.replace(f"[{key}]", metadata[key])
        else:
            text = text.replace(f"[{key}]", PERSONA_DEFAULTS[key])
    return text
