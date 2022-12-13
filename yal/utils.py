import random
import re
from csv import reader
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import phonenumbers
import pkg_resources
import pycountry
from rapidfuzz import fuzz, process

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
BACK_TO_MAIN = "0. 🏠 Back to Main *MENU*"
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
        value = metadata.get(key)
        if value and value.lower() != "skip":
            text = text.replace(f"[{key}]", value)
        else:
            text = text.replace(f"[{key}]", PERSONA_DEFAULTS[key])
    return text


def get_keywords(name):
    keywords = []
    filename = pkg_resources.resource_filename("yal", f"keywords/{name}.csv")
    with open(filename, mode="r") as keyword_file:
        csvreader = reader(keyword_file)
        next(csvreader)
        for row in csvreader:
            keywords.extend([x.lower() for x in row if x != ""])
    return keywords


def check_keyword(keyword, keyword_list):
    return bool(
        process.extract(
            keyword,
            keyword_list,
            scorer=fuzz.ratio,
            score_cutoff=76,
        )
    )


def get_by_path(obj: Optional[dict], *path: str, default_value: Any = None) -> Any:
    """
    Gets a nested value from a dictionary, by following the keys specified in path.
    Returns default_value if no value can be resolved.
    """
    print(type(path))
    print("get_by_path", obj, path)
    if not path:
        return obj
    if not isinstance(obj, dict) or path[0] not in obj:
        return default_value
    return get_by_path(obj[path[0]], *(path[1:]), default_value=default_value)
