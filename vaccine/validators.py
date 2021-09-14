from vaccine.states import ErrorMessage
from vaccine.utils import clean_name, normalise_phonenumber


def nonempty_validator(error_text):
    async def validator(value):
        if value is None or value.strip() == "":
            raise ErrorMessage(error_text)

    return validator


def name_validator(error_text):
    async def validator(value):
        if len(clean_name(value)) < 2:
            raise ErrorMessage(error_text)

    return validator


def phone_number_validator(error_text):
    async def validator(value):
        try:
            normalise_phonenumber(value)
        except ValueError:
            raise ErrorMessage(error_text)

    return validator
