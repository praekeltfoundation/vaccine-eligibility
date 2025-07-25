import asyncio
import json
import re
import time
from collections.abc import Awaitable
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from functools import cached_property
from logging import Logger
from typing import TYPE_CHECKING, AnyStr, Callable, Optional
from uuid import uuid4

import aiohttp
import phonenumbers
import pycountry
from rapidfuzz import process

DECODE_MESSAGE_EXCEPTIONS = (
    UnicodeDecodeError,
    json.JSONDecodeError,
    TypeError,
    KeyError,
    ValueError,
)

HTTP_EXCEPTIONS = (aiohttp.ClientError, asyncio.TimeoutError)

TZ_SAST = timezone(timedelta(hours=2), "SAST")

if TYPE_CHECKING:  # pragma: no cover
    from vaccine.base_application import BaseApplication


def random_id():
    return uuid4().hex


def current_timestamp():
    return datetime.now(timezone.utc)


def luhn_checksum(input):
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(input)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10


def get_today():
    return datetime.now(tz=TZ_SAST).date()


def calculate_age(date_of_birth: date):
    today = get_today()
    years = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


def get_display_choices(choices, bold_numbers=False) -> str:
    if bold_numbers:
        return "\n".join(f"*{i + 1}*. {c.label}" for i, c in enumerate(choices))
    return "\n".join(f"{i + 1}. {c.label}" for i, c in enumerate(choices))


def enforce_character_limit_in_choices(choices, char_limit=160):
    _choices = choices
    while len(get_display_choices(_choices)) > char_limit:
        _choices.pop()
    return _choices


class SAIDNumber:
    class SEX(Enum):
        male = "Male"
        female = "Female"

    @staticmethod
    def _validate_format(value):
        try:
            assert isinstance(value, str)
            value = value.strip()
            assert value.isdigit()
            assert len(value) == 13
            assert luhn_checksum(value) == 0
            return value
        except AssertionError as ae:
            raise ValueError("Invalid format for SA ID number") from ae

    def _extract_dob(self):
        try:
            d = datetime.strptime(self.id_number[:6], "%y%m%d").date()
            # Assume that the person is 0-100 years old
            if d >= get_today():
                d = d.replace(year=d.year - 100)
            return d
        except ValueError as ve:
            raise ValueError("Invalid date of birth in SA ID number") from ve

    def __init__(self, value):
        self.id_number = self._validate_format(value)
        self.date_of_birth = self._extract_dob()

    @property
    def age(self):
        return calculate_age(self.date_of_birth)

    @property
    def sex(self):
        n = int(self.id_number[6])
        if n < 5:
            return self.SEX.female
        return self.SEX.male


def normalise_phonenumber(phonenumber):
    try:
        pn = phonenumbers.parse(phonenumber, "ZA")
        assert phonenumbers.is_possible_number(pn)
        assert phonenumbers.is_valid_number(pn)
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.phonenumberutil.NumberParseException, AssertionError) as e:
        raise ValueError("Invalid phone number") from e


def display_phonenumber(phonenumber):
    try:
        pn = phonenumbers.parse(phonenumber, "ZA")
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.NATIONAL)
    except phonenumbers.phonenumberutil.NumberParseException:
        return phonenumber


class Countries:
    @cached_property
    def countries(self):
        return {
            country.alpha_2: getattr(country, "official_name", "") or country.name
            for country in pycountry.countries
            if country.alpha_2 != "ZA"
        }

    def search_for_country(self, search_text):
        possibilities = process.extract(search_text, self.countries, limit=3)
        return [(code, name) for name, _, code in possibilities]


countries = Countries()


def clean_name(name: Optional[str]) -> str:
    name = re.sub(r"[^a-zA-Z0-9\s\u00C0-\u017F]|\n", "", name or "")
    return name.strip()


def enforce_string(anystring: AnyStr) -> str:
    if isinstance(anystring, bytes):
        return anystring.decode()
    return anystring


def save_media(
    app: "BaseApplication", field: str
) -> Callable[[Optional[str]], Awaitable]:
    """
    If this is a media message, store the media metadata on the contact
    """

    async def validator(content: Optional[str]):
        if not app.inbound:
            return
        msg_type = app.inbound.transport_metadata.get("message", {}).get("type")
        if msg_type in ["audio", "document", "image", "video", "voice", "sticker"]:
            media = app.inbound.transport_metadata.get("message", {}).get(msg_type, {})
            app.save_answer(field, json.dumps(media))

    return validator


@asynccontextmanager
async def log_timing(message: str, logger: Logger):
    start_time = time.monotonic()
    try:
        yield
    finally:
        logger.debug(f"{message} in {time.monotonic() - start_time}s")
