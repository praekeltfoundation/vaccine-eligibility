from datetime import date

from vaccine.states import ErrorMessage
from vaccine.utils import get_today
from yal import config
from yal.utils import normalise_phonenumber


def day_validator(dob_year, dob_month, error_text):
    async def validator(value):
        if value != "skip":
            try:
                assert isinstance(value, str)
                assert value.isdigit()
                if int(value) > 31:
                    raise ErrorMessage(error_text)

                if dob_month != "skip" and dob_year != "skip":
                    date(int(dob_year), int(dob_month), int(value))
            except (AssertionError, ValueError, OverflowError) as e:
                raise ErrorMessage(error_text) from e

    return validator


def year_validator(error_text):
    async def validator(value):
        try:
            if value != "skip":
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > get_today().year - config.MAX_AGE
                assert int(value) <= get_today().year
        except AssertionError as ae:
            raise ErrorMessage(error_text) from ae

    return validator


def phone_number_validator(error_text):
    async def validator(value):
        if value:
            try:
                normalise_phonenumber(value)
            except ValueError as e:
                print(e)
                raise ErrorMessage(error_text) from e
        else:
            raise ErrorMessage(error_text) from None

    return validator


def age_validator(error_text):
    async def validator(value):
        try:
            if value and value.lower() != "skip":
                assert isinstance(value, str)
                assert value.isdigit()
                assert int(value) > 0
                assert int(value) <= 100
        except AssertionError as ae:
            raise ErrorMessage(error_text) from ae

    return validator
