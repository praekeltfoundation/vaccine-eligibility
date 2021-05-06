from vaccine.states import ErrorMessage


def nonempty_validator(error_text):
    async def validator(value):
        if value is None or value.strip() == "":
            raise ErrorMessage(error_text)

    return validator
