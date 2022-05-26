from datetime import date

from vaccine.states import ErrorMessage
from vaccine.utils import get_today
from yal import config


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
            except (AssertionError, ValueError, OverflowError):
                raise ErrorMessage(error_text)

    return validator


def year_validator(error_text):
    async def validator(value):
        try:
            assert isinstance(value, str)
            assert value.isdigit()
            assert int(value) > get_today().year - config.MAX_AGE
            assert int(value) <= get_today().year
        except AssertionError:
            raise ErrorMessage(error_text)

    return validator
