import asyncio
import re
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from functools import cached_property
from json import JSONDecodeError
from typing import Optional
from uuid import uuid4

import aiohttp
import phonenumbers
import pycountry
from rapidfuzz import process

DECODE_MESSAGE_EXCEPTIONS = (
    UnicodeDecodeError,
    JSONDecodeError,
    TypeError,
    KeyError,
    ValueError,
)

HTTP_EXCEPTIONS = (aiohttp.ClientError, asyncio.TimeoutError)


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
    return datetime.now(tz=timezone(timedelta(hours=2))).date()


def calculate_age(date_of_birth: date):
    today = get_today()
    years = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.year):
        years -= 1
    return years


def get_display_choices(choices) -> str:
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
        except AssertionError:
            raise ValueError("Invalid format for SA ID number")

    def _extract_dob(self):
        try:
            d = datetime.strptime(self.id_number[:6], "%y%m%d").date()
            # Assume that the person is 0-100 years old
            if d >= get_today():
                d = d.replace(year=d.year - 100)
            return d
        except ValueError:
            raise ValueError("Invalid date of birth in SA ID number")

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
    except (phonenumbers.phonenumberutil.NumberParseException, AssertionError):
        raise ValueError("Invalid phone number")


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
