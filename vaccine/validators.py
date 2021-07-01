from vaccine.states import ErrorMessage
from vaccine.utils import clean_name


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
