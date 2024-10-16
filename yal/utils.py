import random
import re
from csv import reader
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import phonenumbers
import pkg_resources
import pycountry
from emoji import emoji_list
from rapidfuzz import fuzz, process

from yal import config, rapidpro

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
GENERIC_ERROR_OPTIONS = (
    "Oh oh 👀, I don't understand your reply. But don't worry, we can "
    "try again. This time, please reply with the option that matches "
    "your choice.👍🏾",
    "Oops, looks like I don't have that option available.🤔 Please "
    "try again - I'll get it if you use the option that matches your "
    "choice, promise.👍🏾",
    "Umm...I'm sorry but I'm not sure what that means "
    "[persona_emoji]. You can help me by trying again. This time, "
    "look for the option matching your choice and send that👍🏾",
)
GENDERS = {
    "female": "Female",
    "male": "Male",
    "non_binary": "Non-binary",
    "other": "None of the above",
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
    if config.QA_OVERRIDE_CURRENT_TIMESTAMP:
        return datetime.fromisoformat(config.QA_OVERRIDE_CURRENT_TIMESTAMP)
    return datetime.now(tz=TZ_SAST)


def clean_inbound(content):
    return re.sub(r"[^\w#]+", " ", content or "").strip().lower()


def get_bot_age():
    bot_dob = datetime.strptime(config.YAL_BOT_LAUNCH_DATE, "%Y-%m-%d").date()
    return (get_today() - bot_dob).days


def normalise_phonenumber(phonenumber):
    try:
        if phonenumber is not None:
            if phonenumber.startswith("0"):
                pn = phonenumbers.parse(phonenumber, "ZA")
            else:
                if not phonenumber.startswith("+") and not phonenumber.startswith("0"):
                    phonenumber = f"+{phonenumber}"
                pn = phonenumbers.parse(phonenumber, None)
            assert phonenumbers.is_possible_number(pn)
            assert phonenumbers.is_valid_number(pn)
            return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.phonenumberutil.NumberParseException, AssertionError) as e:
        raise ValueError("Invalid phone number") from e


def extract_first_emoji(persona_emoji):
    emojis_preset = emoji_list(persona_emoji)
    if emojis_preset:
        return emojis_preset[0]["emoji"]
    return ""


def replace_persona_fields(text, metadata=None):
    if metadata is None:
        metadata = {}
    for key in PERSONA_FIELDS:
        value = metadata.get(key)
        if value and value.lower() not in ["skip", ""]:
            if key == "persona_emoji":
                value = extract_first_emoji(value)
            text = text.replace(f"[{key}]", re.sub(r"\s+", " ", value))
        else:
            text = text.replace(f"[{key}]", PERSONA_DEFAULTS[key])
    return text


def get_keywords(name):
    keywords = []
    filename = pkg_resources.resource_filename("yal", f"keywords/{name}.csv")
    with open(filename) as keyword_file:
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
    if not path:
        return obj
    if not isinstance(obj, dict) or path[0] not in obj:
        return default_value
    return get_by_path(obj[path[0]], *(path[1:]), default_value=default_value)


def is_integer(string: str) -> bool:
    try:
        int(string)
        return True
    except ValueError:
        return False


def get_generic_error_options():
    return random.choice(GENERIC_ERROR_OPTIONS)


async def check_if_baseline_active():
    """
    Checks a Global var on the RapidPro instance to see if the Baseline survey is active
    """
    return await rapidpro.get_global_flag("baseline_survey_active")


async def check_if_service_finder_active():
    """
    Checks a Global var on the RapidPro instance to see if the Service finder is active
    """
    return await rapidpro.get_global_flag("service_finder_active")
